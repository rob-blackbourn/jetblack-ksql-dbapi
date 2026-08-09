"""A connection class for ksql"""

from typing import Literal

try:
    from httpx import (  # type: ignore
        Client,
        BasicAuth
    )
except ModuleNotFoundError:
    from httpx2 import (  # type: ignore
        Client,
        BasicAuth
    )

from jetblack_ksql_dbapi._paramstyles import ParamStyle

from ._abc import Connection, Cursor
from ._binding import BindConfig
from ._cursor import KsqlSyncCursor
from ._exceptions import Error
from ._ksql_inspector import KsqlInspector
from ._types import FormatConfig


type QueryType = Literal['print', 'select']


class KsqlSyncConnection(Connection):
    """A ksql connection class"""

    def __init__(
            self,
            client: Client,
            bind_config: BindConfig,
            close_timeout: float | None,
    ) -> None:
        self._client = client
        self._bind_config = bind_config
        self._close_timeout = close_timeout

        self._inspector = KsqlInspector()

    @classmethod
    def connect(
            cls,
            url: str,
            *,
            api_key: str | None = None,
            api_secret: str | None = None,
            bind_config: BindConfig | None = None,
            close_timeout: float | None = None
    ) -> Connection:
        """Connect to the database.

        Args:
            url (_type_): The connection url.
            api_key (str | None, optional): An optional API key. Defaults to
                None.
            api_secret (str | None, optional): An optional API secret. Defaults
                to None.
            bind_config (BindConfig | None, optional): Optional bind
                configuration. Defaults to None.
            close_timeout (float | None, optional): The close timeout. Defaults to None.

        Returns:
            Connection: A connection object.
        """
        auth = (
            BasicAuth(api_key, api_secret)
            if api_key and api_secret else
            None
        )
        client = Client(base_url=url, auth=auth, http1=False, http2=True)
        return cls(
            client,
            bind_config or BindConfig('qmark', FormatConfig()),
            close_timeout
        )

    def cursor(self) -> Cursor:
        if self._client.is_closed:
            raise Error("Connection is closed")

        return KsqlSyncCursor(
            self._client,
            self._bind_config,
            self._inspector,
            self._close_timeout
        )

    def close(self) -> None:
        self._client.close()

    def commit(self) -> None:
        raise Error("ksql does not support transactions")

    def rollback(self) -> None:
        raise Error("ksql does not support transactions")


connect = KsqlSyncConnection.connect
