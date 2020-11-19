import secrets
import time

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.validation import AccountValidator
from app.cryptography import PasswordManager
from app.utils import timestamp


class AccountManager:
    """The manager manages creating, updating and deleting admin accounts."""

    async def __init__(self, database, survey_manager):
        """Initialize an admin manager instance."""
        self.accounts = database['accounts']
        self.configurations = database['configurations']
        self.survey_manager = survey_manager
        self.validator = AccountValidator.create()
        self.password_manager = PasswordManager()

        await self.accounts.create_index(
            keys='admin_name',
            name='admin-name-index',
            unique=True,
        )
        await self.accounts.create_index(
            keys='email',
            name='email-index',
            unique=True,
        )
        await self.accounts.create_index(
            keys='created',
            name='created-index',
            expireAfterSeconds=10*60,  # delete draft accounts after 10 mins
            partialFilterExpression={'verified': {'$eq': False}},
        )

    async def fetch(self, admin_name):
        """Return the account data corresponding to given admin name."""
        account = await self.accounts.find_one(
            filter={'admin_name': admin_name},
            projection={'_id': False},
        )
        if account is None:
            raise HTTPException(404, 'admin not found')
        return account

    async def create(self, admin_name, email, password):
        """Create new admin account with some default account data."""

        # TODO create account with some default data
        # TODO validate data

        account_data = {
            '_id': secrets.token_hex(64),
            'email': email,
            'pwdhash': self.password_manager.hash_password(password),
            'created': timestamp(),
        }

        if not self.validator.validate(account_data):
            raise HTTPException(400, 'invalid account data')
        try:
            await self.database['accounts'].insert_one(account_data)
        except DuplicateKeyError as error:
            index = str(error).split()[7]
            att = 'admin name' if index == 'admin-name-index' else 'email'
            raise HTTPException(400, f'{att} already taken')

    async def update(self, admin_name, account_data):
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
