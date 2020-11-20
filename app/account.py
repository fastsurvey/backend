import secrets
import time

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.validation import AccountValidator
from app.cryptography import PasswordManager
from app.utils import timestamp


class AccountManager:
    """The manager manages creating, updating and deleting admin accounts."""

    async def __init__(self, database, survey_manager, letterbox):
        """Initialize an admin manager instance."""
        self.accounts = database['accounts']
        self.configurations = database['configurations']
        self.survey_manager = survey_manager
        self.validator = AccountValidator.create()
        self.password_manager = PasswordManager()
        self.letterbox = letterbox

        await self.accounts.create_index(
            keys='admin_name',
            name='admin_name_index',
            unique=True,
        )
        await self.accounts.create_index(
            keys='email',
            name='email_index',
            unique=True,
        )
        await self.accounts.create_index(
            keys='creation_time',
            name='creation_time_index',
            expireAfterSeconds=15*60,  # delete draft accounts after 15 mins
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

        # TODO validate data
        # TODO validate password format

        account_data = {
            '_id': secrets.token_hex(64),
            'admin_name': admin_name,
            'email': email,
            'password_hash': self.password_manager.hash_password(password),
            'creation_time': timestamp(),
            'verified': False,
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
                if index == 'email_index':
                    raise HTTPException(400, f'email already taken')
                if index == '_id_':
                    account_data['_id'] = secrets.token_hex(64)

        status = await self.letterbox.send_account_verification_mail(
            admin_name=admin_name,
            receiver=email,
            token=account_data['_id'],
        )
        if status != 200:
            # we do not delete the unverified account here, as the admin could
            # request a new verification email, and the account gets deleted
            # anyways after a few minutes
            raise HTTPException(500, 'email delivery failure')

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
