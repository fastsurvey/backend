from abc import ABC, abstractmethod


class Field(ABC):
    """The abstract class that all input field classes inherit."""

    @abstractmethod
    def check(self):
        """Check the submission for validity."""
        pass


class Selection(Field):

    def __init__(self, min_selections, max_selections, options):
        self.min = min_selections
        self.max = max_selections
        self.options = options

    def check(self):
        raise NotImplementedError


class YesNo(Field):

    def check(self):
        raise NotImplementedError
