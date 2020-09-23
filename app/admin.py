


class AdminManager:
    """The manager manages creating, updating and deleting admins."""

    def __init__(self, database):
        """Initialize an admin manager instance."""
        self._database = database

    async def fetch(self, admin_name):
        """Return admin settings corresponding to given admin name."""
        raise NotImplementedError

    async def update(self, settings):
        """Create or update admin settings in the database."""
        raise NotImplementedError

    async def delete(self, admin_name):
        """Delete the admin from the database."""
        raise NotImplementedError
