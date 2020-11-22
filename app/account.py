import secrets
import time

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError
from pymongo import DESCENDING

from app.validation import AccountValidator
from app.cryptography import PasswordManager, TokenManager
from app.utils import now


class AccountManager:
    """The manager manages creating, updating and deleting admin accounts."""

    async def __init__(self, database, survey_manager, letterbox):
        """Initialize an admin manager instance."""
        self.accounts = database['accounts']
        self.configurations = database['configurations']
        self.survey_manager = survey_manager
        self.validator = AccountValidator.create()
        self.password_manager = PasswordManager()
        self.token_manager = TokenManager()
        self.letterbox = letterbox

        await self.accounts.create_index(
            keys='admin_name',
            name='admin_name_index',
            unique=True,
        )
        await self.accounts.create_index(
            keys='email_address',
            name='email_address_index',
            unique=True,
        )
        await self.accounts.create_index(
            keys='token',
            name='token_index',
            unique=True,
        )
        await self.accounts.create_index(
            keys='creation_time',
            name='creation_time_index',
            expireAfterSeconds=10*60,  # delete draft accounts after 10 mins
            partialFilterExpression={'verified': {'$eq': False}},
        )

    async def fetch(self, admin_id):
        """Return the account data corresponding to given admin name."""
        account_data = await self.accounts.find_one(
            filter={'_id': admin_id},
            projection={'_id': False},
        )
        if account_data is None:
            raise HTTPException(404, 'admin not found')
        return account_data

    async def create(self, admin_name, email_address, password):
        """Create new admin account with some default account data."""

        # TODO validate data
        # TODO validate password format

        account_data = {
            '_id': secrets.token_hex(64),
            'admin_name': admin_name,
            'email_address': email_address,
            'password_hash': self.password_manager.hash_password(password),
            'creation_time': now(),
            'verified': False,
            'token': secrets.token_hex(64),
        }

        if not self.validator.validate(account_data):
            raise HTTPException(400, 'invalid account data')
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

        # TODO check if update really took place, and else error

        status = await self.accounts.update_one(
            filter={'token': token},
            update={'$set': {'verified': True}}
        )
        ##
        print(status)
        ##
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
            raise HTTPException(404, 'admin not found')
        password_hash = account_data['password_hash']
        if not self.password_manager.verify_password(password, password_hash):
            raise HTTPException(401, 'invalid password')
        if account_data['verified'] is False:
            raise HTTPException(400, 'account not verified')
        return self.token_manager.generate(account_data['_id'])

    async def update(self, admin_id, account_data):
        """Update existing admin account data in the database."""

        # TODO update survey names and ids when admin name is changed

        if admin_name != account_data['admin_name']:
            raise HTTPException(501, 'admin name changes not yet implemented')

        if not self.validator.validate(account_data):
            raise HTTPException(400, 'invalid account data')
        result = await self.verified_accounts.replace_one(
            filter={'admin_name': admin_name},
            replacement=account_data,
        )
        if result.matched_count == 0:
            raise HTTPException(400, 'not an existing admin account')

    async def delete(self, admin_name):
        """Delete the admin including all her surveys from the database."""
        await self.verified_accounts.delete_one({'admin_name': admin_name})
        cursor = self.configurations.find(
            filter={'admin_name': admin_name},
            projection={'_id': False, 'survey_name': True},
        )
        survey_names = [e['survey_name'] for e in await cursor.to_list(None)]
        for survey_name in survey_names:
            await self.survey_manager.delete(admin_name, survey_name)

    async def fetch_configurations(self, admin_name, skip, limit):
        """Return list of admin's configurations within specified bounds."""
        cursor = self.configurations.find(
            filter={'admin_name': admin_name},
            projection={'_id': False},
            sort=[('start', DESCENDING)],
            skip=skip,
            limit=limit,
        )
        configurations = await cursor.to_list(None)
        return configurations
