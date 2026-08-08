"""A connection class fort ksql"""

from typing import (
    Literal,
    Self,
)

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
            format_config: FormatConfig,
            paramstyle: ParamStyle,
            close_timeout: float,
    ) -> None:
        self._client = client
        self._format_config = format_config
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
            format_config: FormatConfig | None = None,
            paramstyle: ParamStyle = "qmark",
            close_timeout: float = 1.0
    ) -> Self:
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
            close_timeout (float, optional): The close timeout. Defaults to 1.0.

        Returns:
            Self: A connection object.
        """
        auth = (
            BasicAuth(api_key, api_secret)
            if api_key and api_secret else
            None
        )
        client = Client(base_url=url, auth=auth, http1=False, http2=True)
        return cls(
            client,
            format_config or FormatConfig(),
            paramstyle,
            close_timeout
        )

    def cursor(self) -> Cursor:
        if self._client.is_closed:
            raise Error("Connection is closed")

        return KsqlSyncCursor(
            self._client,
            self._format_config,
            self._inspector,
            self._paramstyle,
            self._close_timeout
        )

    def close(self) -> None:
        self._client.close()

    def commit(self) -> None:
        raise Error("ksql does not support transactions")

    def rollback(self) -> None:
        raise Error("ksql does not support transactions")


connect = KsqlSyncConnection.connect
