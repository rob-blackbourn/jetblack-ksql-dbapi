from __future__ import annotations

from typing import (
    Literal,
    Self,
)

from httpx import (
    Client,
    BasicAuth
)

from jetblack_ksql_dbapi._paramstyles import ParamStyle

from ._cursor import Cursor
from ._exceptions import Error
from ._ksql_inspector import KsqlInspector
from ._types import FormatConfig


type QueryType = Literal['print', 'select']

CONTENT_TYPE_JSON = "application/vnd.ksql.v1+json"
CONTENT_TYPE_DELIMITED = "application/vnd.ksqlapi.delimited.v1"


class Connection:

    def __init__(
            self,
            client: Client,
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
            url: str = "http://localhost:8088",
            api_key: str | None = None,
            api_secret: str | None = None,
            binding_config: FormatConfig | None = None,
            paramstyle: ParamStyle = "qmark"
    ) -> Self:
        auth = (
            BasicAuth(api_key, api_secret)
            if api_key and api_secret else
            None
        )
        client = Client(base_url=url, auth=auth, http1=False, http2=True)
        return cls(client, binding_config or FormatConfig(), paramstyle=paramstyle)

    def cursor(self) -> Cursor:
        if self._client.is_closed:
            raise Error("Connection is closed")

        return Cursor(self._client, self._binding_config, self._inspector, paramstyle=self._paramstyle)

    def close(self) -> None:
        self._client.close()

    def commit(self) -> None:
        raise Error("ksql does not support transactions")

    def rollback(self) -> None:
        raise Error("ksql does not support transactions")


connect = Connection.connect
