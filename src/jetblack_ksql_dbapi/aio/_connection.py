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


class KsqlAsyncConnection(Connection):
    """An async ksql connection"""

    def __init__(
            self,
            client: AsyncClient,
            binding_config: FormatConfig,
            paramstyle: ParamStyle,
            close_timeout: float | None,
    ) -> None:
        self._client = client
        self._binding_config = binding_config
        self._inspector = KsqlInspector()
        self._paramstyle = paramstyle
        self._close_timeout = close_timeout

    @classmethod
    def connect(
            cls,
            url: str,
            *,
            api_key: str | None = None,
            api_secret: str | None = None,
            binding_config: FormatConfig | None = None,
            paramstyle: ParamStyle = "qmark",
            close_timeout: float | None = None
    ) -> Connection:
        """Connect to the database.

        Args:
            url (_type_): The connection url.
            api_key (str | None, optional): An optional API key. Defaults to
                None.
            api_secret (str | None, optional): An optional API secret. Defaults
                to None.
            format_config (FormatConfig | None, optional): Optional format
                configuration. Defaults to None.
            paramstyle (ParamStyle, optional): The param style. Defaults to
                "qmark".
            close_timeout (float | None, optional): The close timeout. Defaults to None.

        Returns:
            Self: A connection object.
        """
        auth = (
            BasicAuth(api_key, api_secret)
            if api_key and api_secret else
            None
        )
        client = AsyncClient(base_url=url, auth=auth, http1=False, http2=True)
        return cls(
            client,
            binding_config or FormatConfig(),
            paramstyle,
            close_timeout
        )

    def cursor(self) -> Cursor:
        if self._client.is_closed:
            raise Error("Connection is closed")

        return KsqlAsyncCursor(
            self._client,
            self._binding_config,
            self._inspector,
            self._paramstyle,
            self._close_timeout
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def commit(self) -> None:
        raise Error("ksql does not support transactions")

    async def rollback(self) -> None:
        raise Error("ksql does not support transactions")


connect = KsqlAsyncConnection.connect
