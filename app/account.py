import time
import asyncio

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError
from pymongo import DESCENDING

from app.validation import AccountValidator
from app.cryptography import PasswordManager, vtoken
from app.utils import now


class AccountManager:
    """The manager manages creating, updating and deleting user accounts."""

    def __init__(self, database, letterbox, jwt_manager, survey_manager):
        """Initialize an account manager instance."""
        self.database = database
        self.survey_manager = survey_manager
        self.validator = AccountValidator.create()
        self.password_manager = PasswordManager()
        self.jwt_manager = jwt_manager
        self.letterbox = letterbox

    async def fetch(self, username, access_token):
        """Return the account data corresponding to given username."""
        self.jwt_manager.authorize(username, access_token)
        return await self._fetch(username)

    async def create(self, username, account_data):
        """Create new user account with some default account data."""
        if username != account_data['username']:
            raise HTTPException(400, 'invalid account data')
        if not self.validator.validate(account_data):
            raise HTTPException(400, 'invalid account data')
        account_data = {
            '_id': username,
            'email_address': account_data['username'],
            'password_hash': self.password_manager.hash(
                account_data['password'],
            ),
            'creation_time': now(),
            'verified': False,
            'verification_token': vtoken(),
        }
        while True:
            try:
                await self.database['accounts'].insert_one(account_data)
                break
            except DuplicateKeyError as error:
                index = str(error).split()[7]
                if index == '_id_':
                    raise HTTPException(400, f'username already taken')
                if index == 'email_address_index':
                    raise HTTPException(400, f'email address already taken')
                if index == 'verification_token_index':
                    account_data['verification_token'] = vtoken()
                else:
                    raise HTTPException(500, 'account creation error')

        status = await self.letterbox.send_account_verification_email(
            username=username,
            receiver=account_data['email_address'],
            verification_token=account_data['verification_token'],
        )
        if status != 200:
            # we do not delete the unverified account here, as the user could
            # request a new verification email, and the account gets deleted
            # anyways after a few minutes
            raise HTTPException(500, 'email delivery failure')

    async def verify(self, verification_token, password):
        """Verify an existing account via its unique verification token."""
        account_data = await self.database['accounts'].find_one(
            filter={'verification_token': verification_token},
            projection={'password_hash': True, 'verified': True},
        )
        if account_data is None:
            raise HTTPException(401, 'invalid verification token')
        password_hash = account_data['password_hash']
        if not self.password_manager.verify(password, password_hash):
            raise HTTPException(401, 'invalid password')
        if account_data['verified'] is True:
            raise HTTPException(400, 'account already verified')
        result = await self.database['accounts'].update_one(
            filter={'verification_token': verification_token},
            update={'$set': {'verified': True}}
        )
        if result.matched_count == 0:
            raise HTTPException(401, 'invalid verification token')
        return self.jwt_manager.generate(account_data['_id'])

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
            raise HTTPException(404, 'user not found')
        password_hash = account_data['password_hash']
        if not self.password_manager.verify(password, password_hash):
            raise HTTPException(401, 'invalid password')
        if account_data['verified'] is False:
            raise HTTPException(400, 'account not verified')
        return self.jwt_manager.generate(account_data['_id'])

    async def update(self, username, account_data, access_token):
        """Update existing user account data in the database."""
        self.jwt_manager.authorize(username, access_token)
        self._update(username, account_data)

    async def delete(self, username, access_token):
        """Delete the user including all her surveys from the database."""
        self.jwt_manager.authorize(username, access_token)
        self._delete(username)

    async def fetch_configurations(
            self,
            username,
            skip,
            limit,
            access_token,
        ):
        """Return a list of the user's survey configurations."""
        self.jwt_manager.authorize(username, access_token)
        return await self._fetch_configurations(username, skip, limit)

    async def _fetch(self, username):
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
            raise HTTPException(404, 'user not found')
        return account_data

    async def _update(self, username, account_data):
        """Update existing user account data in the database."""

        # TODO handle username change with transactions
        # TODO how to change password?
        # TODO handle email change specially, as it needs to be reverified

        if not self.validator.validate(account_data):
            raise HTTPException(400, 'invalid account data')

        # TODO cannot do a full replace, think password hash!

        result = await self.database['accounts'].replace_one(
            filter={'_id': username},
            replacement=account_data,
        )
        if result.matched_count == 0:
            raise HTTPException(404, 'user not found')

    async def _delete(self, username):
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
            await self.survey_manager._delete(username, survey_name)

    async def _fetch_configurations(self, username, skip, limit):
        """Return a list of the user's survey configurations."""
        cursor = self.database['configurations'].find(
            filter={'username': username},
            projection={'_id': False, 'username': False},
            sort=[('start', DESCENDING)],
            skip=skip,
            limit=limit,
        )
        configurations = await cursor.to_list(None)
        return configurations
