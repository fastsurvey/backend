from fastapi import HTTPException


class AdminManager:
    """The manager manages creating, updating and deleting admins."""

    def __init__(self, database):
        """Initialize an admin manager instance."""
        self._database = database

    async def fetch(self, admin_name, start, end):
        """Return admin account data corresponding to given admin name."""


        if start is not None or end is not None:
            raise HTTPException(501, 'not implemented')


        account = await self._database['accounts'].find_one(
            filter={'_id': admin_name},
            projection={'_id': False},
        )
        if account is None:
            raise HTTPException(404, 'admin not found')
        return account

    async def update(self, settings):
        """Create or update admin account in the database."""
        raise HTTPException(501, 'not implemented')

    async def delete(self, admin_name):
        """Delete the admin from the database."""
        raise HTTPException(501, 'not implemented')
