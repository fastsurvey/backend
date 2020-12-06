import secrets
import time
import asyncio

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError
from pymongo import DESCENDING

from app.validation import AccountValidator
from app.cryptography import PasswordManager
from app.utils import now


class AccountManager:
    """The manager manages creating, updating and deleting admin accounts."""

    def __init__(self, database, survey_manager, letterbox, token_manager):
        """Initialize an admin manager instance."""
        self.accounts = database['accounts']
        self.configurations = database['configurations']
        self.survey_manager = survey_manager
        self.validator = AccountValidator.create()
        self.password_manager = PasswordManager()
        self.token_manager = token_manager
        self.letterbox = letterbox

        loop = asyncio.get_event_loop()

        loop.run_until_complete(self.accounts.create_index(
            keys='admin_name',
            name='admin_name_index',
            unique=True,
        ))
        loop.run_until_complete(self.accounts.create_index(
            keys='email_address',
            name='email_address_index',
            unique=True,
        ))
        loop.run_until_complete(self.accounts.create_index(
            keys='token',
            name='token_index',
            unique=True,
        ))
        loop.run_until_complete(self.accounts.create_index(
            keys='creation_time',
            name='creation_time_index',
            expireAfterSeconds=10*60,  # delete draft accounts after 10 mins
            partialFilterExpression={'verified': {'$eq': False}},
        ))

    async def fetch(self, admin_name, access_token):
        """Return the account data corresponding to given admin name."""
        admin_id = self.token_manager.decode(access_token)
        account_data = await self.accounts.find_one(
            filter={'_id': admin_id},
            projection={'_id': False},
        )

        # TODO do not return sensitive information e.g. password hash

        if account_data is None:
            raise HTTPException(404, 'admin not found')
        if account_data['admin_name'] != admin_name:
            raise HTTPException(401, 'unauthorized')
        return account_data

    async def create(self, admin_name, email_address, password):
        """Create new admin account with some default account data."""
        account_data = {
            'admin_name': admin_name,
            'email_address': email_address,
        }
        if not self.validator.validate(account_data):
            raise HTTPException(400, 'invalid account data')
        if not self.password_manager.validate_password(password):
            raise HTTPException(400, 'invalid password format')
        account_data = {
            '_id': secrets.token_hex(64),
            **account_data,
            'password_hash': self.password_manager.hash_password(password),
            'creation_time': now(),
            'verified': False,
            'token': secrets.token_hex(64),
        }
        while True:
            try:
                await self.accounts.insert_one(account_data)
                break
            except DuplicateKeyError as error:
                index = str(error).split()[7]
                if index == 'admin_name_index':
                    raise HTTPException(400, f'admin name already taken')
                if index == 'email_address_index':
                    raise HTTPException(400, f'email already taken')
                if index == 'token_index':
                    account_data['token'] = secrets.token_hex(64)
                if index == '_id_':
                    account_data['_id'] = secrets.token_hex(64)
                else:
                    raise HTTPException(500, 'account creation error')

        status = await self.letterbox.send_account_verification_mail(
            admin_name=admin_name,
            receiver=email_address,
            token=account_data['token'],
        )
        if status != 200:
            # we do not delete the unverified account here, as the admin could
            # request a new verification email, and the account gets deleted
            # anyways after a few minutes
            raise HTTPException(500, 'email delivery failure')

    async def verify(self, token, password):
        """Verify an existing account via its unique verification token."""
        account_data = await self.accounts.find_one(
            filter={'token': token},
            projection={'password_hash': True, 'verified': True},
        )
        if account_data is None:
            raise HTTPException(401, 'invalid token')
        password_hash = account_data['password_hash']
        if not self.password_manager.verify_password(password, password_hash):
            raise HTTPException(401, 'invalid password')
        if account_data['verified'] is True:
            raise HTTPException(400, 'account already verified')
        result = await self.accounts.update_one(
            filter={'token': token},
            update={'$set': {'verified': True}}
        )
        if result.matched_count == 0:
            raise HTTPException(401, 'invalid token')
        return self.token_manager.generate(account_data['_id'])

    async def authenticate(self, identifier, password):
        """Authenticate admin by her admin_name or email and her password."""
        expression = (
            {'email_address': identifier}
            if '@' in identifier
            else {'admin_name': identifier}
        )
        account_data = await self.accounts.find_one(
            filter=expression,
            projection={'password_hash': True, 'verified': True},
        )
        if account_data is None:
            raise HTTPException(404, 'account not found')
        password_hash = account_data['password_hash']
        if not self.password_manager.verify_password(password, password_hash):
            raise HTTPException(401, 'invalid password')
        if account_data['verified'] is False:
            raise HTTPException(400, 'account not verified')
        return self.token_manager.generate(account_data['_id'])

    async def update(self, admin_name, account_data, access_token):
        """Update existing admin account data in the database."""

        # TODO handle email change specially, as it needs to be reverified

        admin_id = self.token_manager.decode(access_token)
        if not self.validator.validate(account_data):
            raise HTTPException(400, 'invalid account data')
        result = await self.accounts.replace_one(
            filter={'_id': admin_id, 'admin_name': admin_name},
            replacement=account_data,
        )
        if result.matched_count == 0:
            raise HTTPException(404, 'account not found')

    async def delete(self, admin_name, access_token):
        """Delete the admin including all her surveys from the database."""
        admin_id = self.token_manager.decode(access_token)
        await self.accounts.delete_one({'_id': admin_id})
        cursor = self.configurations.find(
            filter={'admin_id': admin_id},
            projection={'_id': False, 'survey_name': True},
        )
        survey_names = [
            configuration['survey_name']
            for configuration
            in await cursor.to_list(None)
        ]
        for survey_name in survey_names:
            await self.survey_manager.delete(admin_id, survey_name)

    async def fetch_configurations(
            self,
            admin_name,
            skip,
            limit,
            access_token
        ):
        """Return a list of the admin's survey configurations."""
        admin_id = self.token_manager.decode(access_token)
        cursor = self.configurations.find(
            filter={'admin_id': admin_id},
            projection={'_id': False},
            sort=[('start', DESCENDING)],
            skip=skip,
            limit=limit,
        )
        configurations = await cursor.to_list(None)
        return configurations
