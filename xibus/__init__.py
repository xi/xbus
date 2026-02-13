import contextlib

from .client import MagicClient
from .connection import get_connection


@contextlib.asynccontextmanager
async def get_client(bus):
    async with get_connection(bus) as con:
        yield MagicClient(con)
