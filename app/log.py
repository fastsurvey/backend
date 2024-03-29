import datetime as dt
import logging
import sys


def format_pydantic_error(exc):
    """Format a pydantic validation error to a single line string for logging."""
    errors = "["
    for i, x in enumerate(str(exc).splitlines()[1:]):
        errors += f"{x.split(' (type=')[0].strip()}, " if i % 2 else f"{x}: "
    return errors[:-2] + "]"


formatter = logging.Formatter(
    fmt="{asctime} | {levelname:8} | {msg}",
    datefmt="%a %Y-%m-%d %H:%M:%S %z",
    style="{",
)

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)

logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)
