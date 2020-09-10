
class AdminManager:
    """The manager manages creating, updating and deleting admin objects."""

    def __init__(self, database):
        """Initialize this class."""
        self._database = database

    async def update_admin(self, settings):
        """Create or update the admin settings in the database."""

        admin_name = 'fastsurvey'

        await self._database['admins'].find_one_and_replace(
            filter={'_id': admin_name},
            replacement=settings,
            upsert=True,
        )

    async def get_admin(self, admin_name):
        """Return the admin settings corresponding to the given identifiers."""
        settings = await self._database['configurations'].find_one(
            filter={'_id': admin_name},
        )
        return settings

    async def delete_admin(self, admin_name):
        """Delete the admin settings and all their surveys."""
        pass

    async def update_survey(self, configuration):
        """Create or update the survey configuration in the database."""
        pass

    async def update_survey(self, configuration):
        """Create or update the survey configuration in the database."""
        pass
