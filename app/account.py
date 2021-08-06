import pymongo.errors
import pymongo
import fastapi

import app.email as email
import app.cryptography.access as access
import app.cryptography.password as pw
import app.cryptography.verification as verification
import app.utils as utils
import app.resources.database as database
import app.errors as errors


class AccountManager:
    """The manager manages creating, updating and deleting user accounts."""

    def __init__(self, survey_manager):
        """Initialize an account manager instance."""
        self.survey_manager = survey_manager

    async def fetch(self, username):
        """Return the account data corresponding to given user name."""
        account_data = await database.database['accounts'].find_one(
            filter={'_id': username},
            projection={
                '_id': False,
                'email_address': True,
                'creation_time': True,
                'verified': True,
            },
        )
        if account_data is None:
            raise errors.UserNotFoundError()
        return account_data

    async def create(self, username, account_data):
        """Create new user account with some default account data."""
        if account_data['username'] != username:
            # not very pretty, but cannot raise ValidationError otherwise
            raise fastapi.HTTPException(
                422,
                [{
                    'loc': ['body', 'username'],
                    'msg': 'username does not match username specified in route',
                    'type': 'value_error',
                }]
            )
        timestamp = utils.now()
        account = {
            '_id': username,
            'email_address': account_data['email_address'],
            'password_hash': pw.hash(account_data['password']),
            'creation_time': timestamp,
            'modification_time': timestamp,
            'verified': False,
            'verification_token': verification.token(),
        }
        while True:
            try:
                await database.database['accounts'].insert_one(account)
                break
            except pymongo.errors.DuplicateKeyError as error:
                index = str(error).split()[7]
                if index == '_id_':
                    raise errors.UsernameAlreadyTakenError()
                if index == 'email_address_index':
                    raise errors.EmailAddressAlreadyTakenError()
                if index == 'verification_token_index':
                    account_data['verification_token'] = verification.token()
                else:
                    raise errors.InternalServerError()

        status = await email.send_account_verification(
            account['email_address'],
            username,
            account['verification_token'],
        )
        if status != 200:
            # we do not delete the unverified account here, as the user could
            # request a new verification email, and the account gets deleted
            # anyways after a few minutes
            raise fastapi.HTTPException(
                422,
                [{
                    'loc': ['body', 'email_address'],
                    'msg': 'invalid email_address',
                    'type': 'value_error',
                }]
            )

    async def verify(self, verification_token, password):
        """Verify an existing account via its unique verification token."""
        account_data = await database.database['accounts'].find_one(
            filter={'verification_token': verification_token},
            projection={'password_hash': True, 'verified': True},
        )
        if account_data is None or account_data['verified']:
            raise errors.InvalidVerificationTokenError()
        if not pw.verify(password, account_data['password_hash']):
            raise errors.InvalidPasswordError()
        result = await database.database['accounts'].update_one(
            filter={'verification_token': verification_token},
            update={'$set': {'verified': True}}
        )
        if result.matched_count == 0:
            raise errors.InvalidVerificationTokenError()
        return access.generate(account_data['_id'])

    async def update(self, username, account_data):
        """Update existing user account data in the database."""

        # TODO handle username change with transactions
        # TODO handle email change specially, as it needs to be reverified

        entry = await database.database['accounts'].find_one(
            filter={'_id': username},
            projection={
                '_id': False,
                'email_address': True,
                'password_hash': True,
            },
        )
        if entry is None:
            raise errors.UserNotFoundError()
        update = {}
        if account_data['username'] != username:
            raise errors.NotImplementedError()
        if account_data['email_address'] != entry['email_address']:
            raise errors.NotImplementedError()
        if not pw.verify(account_data['password'], entry['password_hash']):
            update['password_hash'] = pw.hash(account_data['password'])
        if update:
            update['modification_time'] = utils.now()
            result = await database.database['accounts'].update_one(
                filter={'_id': username},
                update={'$set': update},
            )
            if result.matched_count == 0:
                raise errors.UserNotFoundError()

    async def delete(self, username):
        """Delete the user including all their surveys from the database."""

        # TODO when the account is deleted the access token needs to be
        # useless afterwards

        await database.database['accounts'].delete_one({'_id': username})
        cursor = database.database['configurations'].find(
            filter={'username': username},
            projection={'_id': False, 'survey_name': True},
        )
        survey_names = [
            configuration['survey_name']
            for configuration
            in await cursor.to_list(None)
        ]
        for survey_name in survey_names:
            await self.survey_manager.delete(username, survey_name)

    async def authenticate(self, identifier, password):
        """Authenticate user by their username or email and their password."""
        expression = (
            {'email_address': identifier}
            if '@' in identifier
            else {'_id': identifier}
        )
        account_data = await database.database['accounts'].find_one(
            filter=expression,
            projection={'password_hash': True, 'verified': True},
        )
        if account_data is None:
            raise errors.UserNotFoundError()
        password_hash = account_data['password_hash']
        if not pw.verify(password, password_hash):
            raise errors.InvalidPasswordError()
        if account_data['verified'] is False:
            raise errors.AccountNotVerifiedError()
        return access.generate(account_data['_id'])

    async def fetch_configurations(self, username, skip, limit):
        """Return a list of the user's survey configurations."""
        cursor = database.database['configurations'].find(
            filter={'username': username},
            projection={'_id': False, 'username': False},
            sort=[('start', pymongo.DESCENDING)],
            skip=skip,
            limit=limit,
        )
        configurations = await cursor.to_list(None)
        return configurations
