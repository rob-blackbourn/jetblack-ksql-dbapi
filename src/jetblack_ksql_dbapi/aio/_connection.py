from __future__ import annotations

from typing import Literal

try:
    from httpx import (  # type: ignore
        AsyncClient,
        BasicAuth
    )
except ModuleNotFoundError:
    from httpx2 import (  # type: ignore
        AsyncClient,
        BasicAuth
    )

from .._paramstyles import ParamStyle

from ._cursor import KsqlAsyncCursor
from .._exceptions import Error
from .._ksql_inspector import KsqlInspector
from .._types import FormatConfig

from ._abc import Connection, Cursor


type QueryType = Literal['print', 'select']

CONTENT_TYPE_JSON = "application/vnd.ksql.v1+json"
CONTENT_TYPE_DELIMITED = "application/vnd.ksqlapi.delimited.v1"


class KsqlAsyncConnection(Connection):
    """An async ksql connection"""

    def __init__(
            self,
            client: AsyncClient,
            binding_config: FormatConfig,
            paramstyle: ParamStyle = "qmark"
    ) -> None:
        self._client = client
        self._binding_config = binding_config
        self._inspector = KsqlInspector()
        self._paramstyle = paramstyle

    @classmethod
    def connect(
            cls,
            url: str,
            *,
            api_key: str | None = None,
            api_secret: str | None = None,
            binding_config: FormatConfig | None = None,
            paramstyle: ParamStyle = "qmark"
    ) -> Connection:
        auth = (
            BasicAuth(api_key, api_secret)
            if api_key and api_secret else
            None
        )
        client = AsyncClient(base_url=url, auth=auth, http1=False, http2=True)
        return cls(client, binding_config or FormatConfig(), paramstyle=paramstyle)

    def cursor(self) -> Cursor:
        if self._client.is_closed:
            raise Error("Connection is closed")

        return KsqlAsyncCursor(self._client, self._binding_config, self._inspector, paramstyle=self._paramstyle)

    async def close(self) -> None:
        await self._client.aclose()

    async def commit(self) -> None:
        raise Error("ksql does not support transactions")

    async def rollback(self) -> None:
        raise Error("ksql does not support transactions")


connect = KsqlAsyncConnection.connect
