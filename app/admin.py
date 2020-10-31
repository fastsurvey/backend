import time

from fastapi import HTTPException
from pymongo import DESCENDING
from pymongo.errors import DuplicateKeyError

from app.validation import AccountDataValidator


class AdminManager:
    """The manager manages creating, updating and deleting admins."""

    def __init__(self, database):
        """Initialize an admin manager instance."""
        self.database = database
        self.database['accounts'].create_index(
            keys='admin_name',
            unique=True,
            name='admin-name-index',
        )
        self.database['accounts'].create_index(
            keys='email',
            unique=True,
            name='email-index',
        )
        self.validator = AccountDataValidator.create()

    async def fetch(self, admin_name):
        """Return the account data corresponding to given admin name."""
        account = await self.database['accounts'].find_one(
            filter={'admin_name': admin_name},
            projection={'_id': False},
        )
        if account is None:
            raise HTTPException(404, 'admin not found')
        return account

    async def create(self, admin_name, account_data):
        """Update new admin account data in the database."""
        if admin_name != account_data['admin_name']:
            raise HTTPException(400, 'route/account data admin names differ')
        if not self.validator.validate(account_data):
            raise HTTPException(400, 'invalid account data')
        account_data['created'] = int(time.time())
        try:
            await self.database['accounts'].insert_one(account_data)
        except DuplicateKeyError as error:
            index = str(error).split()[7]
            att = 'admin name' if index == 'admin-name-index' else 'email'
            raise HTTPException(400, f'{att} already taken')

    async def update(self, admin_name, account_data):
        """Update admin account data in the database."""
        raise HTTPException(501, 'not implemented')

    async def delete(self, admin_name):
        """Delete the admin including all her surveys from the database."""
        raise HTTPException(501, 'not implemented')

    async def fetch_configurations(self, admin_name, skip, limit):
        """Return list of admin's configurations within specified bounds."""
        cursor = self.database['configurations'].find(
            filter={'admin_name': admin_name},
            projection={'_id': False},
            sort=[('start', DESCENDING)],
            skip=skip,
            limit=limit,
        )
        configurations = await cursor.to_list(None)
        return configurations
