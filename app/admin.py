from fastapi import HTTPException
from pymongo import DESCENDING


class AdminManager:
    """The manager manages creating, updating and deleting admins."""

    def __init__(self, database):
        """Initialize an admin manager instance."""
        self._database = database

    async def fetch_account_data(self, admin_name):
        """Return admin account data corresponding to given admin name."""
        account = await self._database['accounts'].find_one(
            filter={'_id': admin_name},
            projection={'_id': False},
        )
        if account is None:
            raise HTTPException(404, 'admin not found')
        return account

    async def fetch_configurations(self, admin_name, skip, limit):
        """Return list of admin's configurations within specified bounds."""
        cursor = self._database['configurations'].find(
            filter={'admin_name': admin_name},
            projection={'_id': False},
            sort=[('start', DESCENDING)],
            skip=skip,
            limit=limit,
        )
        configurations = await cursor.to_list(None)
        return configurations

    async def update(self, account_data):
        """Create or update admin account data in the database."""
        raise HTTPException(501, 'not implemented')

    async def delete(self, admin_name):
        """Delete the admin from the database."""
        raise HTTPException(501, 'not implemented')
