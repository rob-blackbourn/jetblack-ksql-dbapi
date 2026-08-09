"""Utilites"""

from typing import Any, AsyncIterator, Iterable


async def list_aiter(iterable: Iterable[Any]) -> AsyncIterator[Any]:
    for item in iterable:
        yield item
