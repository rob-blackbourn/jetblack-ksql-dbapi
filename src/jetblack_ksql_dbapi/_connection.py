"""The connection class

See: [Connection Objects](https://peps.python.org/pep-0249/#connection-objects)
"""

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

from ._cursor import Cursor
from ._exceptions import Error
from ._ksql_inspector import KsqlInspector
from ._types import FormatConfig


type QueryType = Literal['print', 'select']


class Connection:
    """A PEP-294 compliant connection class"""

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
            url: str = "http://localhost:8088",
            *,
            api_key: str | None = None,
            api_secret: str | None = None,
            format_config: FormatConfig | None = None,
            paramstyle: ParamStyle = "qmark",
            close_timeout: float = 1.0
    ) -> Self:
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

        return Cursor(
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


connect = Connection.connect
