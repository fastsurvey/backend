import fastapi as api
import pymongo.errors
import pymongo

import app.validation as validation
import app.email as email
import app.cryptography.access as access
import app.cryptography.password as pw
import app.cryptography.verification as verification
import app.utils as utils


class AccountManager:
    """The manager manages creating, updating and deleting user accounts."""

    def __init__(self, database, survey_manager):
        """Initialize an account manager instance."""
        self.database = database
        self.survey_manager = survey_manager
        self.validator = validation.AccountValidator()

    async def fetch(self, username):
        """Return the account data corresponding to given user name."""
        account_data = await self.database['accounts'].find_one(
            filter={'_id': username},
            projection={
                '_id': False,
                'email_address': True,
                'creation_time': True,
                'verified': True,
            },
        )
        if account_data is None:
            raise api.HTTPException(404, 'user not found')
        return account_data

    async def create(self, username, account_data):
        """Create new user account with some default account data."""
        if username != account_data['username']:
            raise api.HTTPException(400, 'invalid account data')
        if not self.validator.validate(account_data):
            raise api.HTTPException(400, 'invalid account data')
        account_data = {
            '_id': username,
            'email_address': account_data['email_address'],
            'password_hash': pw.hash(account_data['password']),
            'creation_time': utils.now(),
            'verified': False,
            'verification_token': verification.token(),
        }
        while True:
            try:
                await self.database['accounts'].insert_one(account_data)
                break
            except pymongo.errors.DuplicateKeyError as error:
                index = str(error).split()[7]
                if index == '_id_':
                    raise api.HTTPException(400, 'username already taken')
                if index == 'email_address_index':
                    raise api.HTTPException(400, 'email address already taken')
                if index == 'verification_token_index':
                    account_data['verification_token'] = verification.token()
                else:
                    raise api.HTTPException(500, 'account creation error')

        status = await email.send_account_verification(
            account_data['email_address'],
            username,
            account_data['verification_token'],
        )
        if status != 200:
            # we do not delete the unverified account here, as the user could
            # request a new verification email, and the account gets deleted
            # anyways after a few minutes
            raise api.HTTPException(500, 'email delivery failure')

    async def verify(self, verification_token, password):
        """Verify an existing account via its unique verification token."""
        account_data = await self.database['accounts'].find_one(
            filter={'verification_token': verification_token},
            projection={'password_hash': True, 'verified': True},
        )
        if account_data is None:
            raise api.HTTPException(401, 'invalid verification token')
        password_hash = account_data['password_hash']
        if not pw.verify(password, password_hash):
            raise api.HTTPException(401, 'invalid password')
        if account_data['verified'] is True:
            raise api.HTTPException(400, 'account already verified')
        result = await self.database['accounts'].update_one(
            filter={'verification_token': verification_token},
            update={'$set': {'verified': True}}
        )
        if result.matched_count == 0:
            raise api.HTTPException(401, 'invalid verification token')
        return access.generate(account_data['_id'])

    async def update(self, username, account_data):
        """Update existing user account data in the database."""

        # TODO handle username change with transactions
        # TODO how to change password?
        # TODO handle email change specially, as it needs to be reverified

        if not self.validator.validate(account_data):
            raise api.HTTPException(400, 'invalid account data')

        # TODO cannot do a full replace, think password hash!

        result = await self.database['accounts'].replace_one(
            filter={'_id': username},
            replacement=account_data,
        )
        if result.matched_count == 0:
            raise api.HTTPException(404, 'user not found')

    async def delete(self, username):
        """Delete the user including all her surveys from the database."""
        await self.database['accounts'].delete_one({'_id': username})
        cursor = self.database['configurations'].find(
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
        """Authenticate user by her username or email and her password."""
        expression = (
            {'email_address': identifier}
            if '@' in identifier
            else {'_id': identifier}
        )
        account_data = await self.database['accounts'].find_one(
            filter=expression,
            projection={'password_hash': True, 'verified': True},
        )
        if account_data is None:
            raise api.HTTPException(404, 'user not found')
        password_hash = account_data['password_hash']
        if not pw.verify(password, password_hash):
            raise api.HTTPException(401, 'invalid password')
        if account_data['verified'] is False:
            raise api.HTTPException(400, 'account not verified')
        return access.generate(account_data['_id'])

    async def fetch_configurations(self, username, skip, limit):
        """Return a list of the user's survey configurations."""
        cursor = self.database['configurations'].find(
            filter={'username': username},
            projection={'_id': False, 'username': False},
            sort=[('start', pymongo.DESCENDING)],
            skip=skip,
            limit=limit,
        )
        configurations = await cursor.to_list(None)
        return configurations
