from fastapi import HTTPException
from pymongo import DESCENDING


class AdminManager:
    """The manager manages creating, updating and deleting admins."""

    def __init__(self, database):
        """Initialize an admin manager instance."""
        self.database = database

    async def fetch(self, admin_name):
        """Return the account data corresponding to given admin name."""
        account = await self.database['accounts'].find_one(
            filter={'admin_name': admin_name},
            projection={'_id': False},
        )
        if account is None:
            raise HTTPException(404, 'admin not found')
        return account

    async def update(self, admin_name, account_data):
        """Create or update admin account data in the database."""
        if admin_name != account_data['admin_name']:
            raise HTTPException(400, 'route/account data admin names differ')
        '''
        if not self.validator.validate(account_data):
            raise HTTPException(400, 'invalid account data')
        '''
        await self.database['accounts'].find_one_and_replace(
            filter={'admin_name': admin_name},
            replacement=account_data,
            upsert=True,
        )

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
