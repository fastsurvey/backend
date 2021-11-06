import loguru
import sys


LOGGER = loguru.logger
LOGGER.remove()
LOGGER.add(
    sys.stderr,
    colorize=True,
    format=(
        "<bold><dim>{time:YYYY-MM-DD HH:mm:ss.SS Z ddd}</></> | "
        "<level>{level:8}</> | "
        "<blue>{name}:{function}:{line}</> - {message}"
    ),
)


def format_pydantic_error(exc):
    """Format a pydantic validation error to a single line string for logging."""
    errors = "["
    for i, x in enumerate(str(exc).splitlines()[1:]):
        errors += f"{x.strip()}, " if i % 2 else f"{x}: "
    return errors[:-2] + "]"
