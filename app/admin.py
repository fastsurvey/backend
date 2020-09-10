
class AdminManager:
    """The manager manages creating, updating and deleting admin objects."""

    def __init__(self, database):
        """Initialize this class with empty surveys dictionary."""
        self._database = database
