import json
import re
from typing import Any, Iterator, Mapping, NamedTuple, Self, Sequence, cast

import httpx
from httpx import (
    Client,
    HTTPStatusError,
    Response,
    Timeout,
    USE_CLIENT_DEFAULT,
    BasicAuth
)

from ._binding import BindingConfig, bind_parameters
from ._client import KsqlDbClient
from ._paramstyles import ParamStyle
from .types import QueryMetaData, create_ksql_error

CONTENT_TYPE_JSON = "application/vnd.ksql.v1+json"
CONTENT_TYPE_NDJSON = "application/vnd.ksqlapi.delimited.v1"

paramstyle: ParamStyle = "pyformat"


class CursorDescription(NamedTuple):
    name: str
    type_code: str
    display_size: int | None
    internal_size: int | None
    precision: int | None
    scale: int | None
    null_ok: bool | None


class Connection:

    def __init__(
            self,
            client: Client,
            binding_config: BindingConfig,
    ) -> None:
        self._client = client
        self._binding_config = binding_config

    @classmethod
    def connect(
            cls,
            url: str = "http://localhost:8088",
            api_key: str | None = None,
            api_secret: str | None = None,
            binding_config: BindingConfig | None = None,
    ) -> Self:
        auth = (
            BasicAuth(api_key, api_secret)
            if api_key and api_secret else
            None
        )
        client = Client(base_url=url, auth=auth, http1=False, http2=True)
        return cls(client, binding_config or BindingConfig())


_SQL_COMMENTS = re.compile(
    r'(([\'"])(?:(?!\2|\\).|\\.)*\2)|--.*|/\*(?:[^*]|\*(?!/))*\*/'
)


class Cursor:

    def __init__(
            self,
            connection: Connection,
            binding_config: BindingConfig
    ) -> None:
        self._connection = connection
        self._binding_config = binding_config
        self._result: Iterator | None
        self._iter: Iterator[str] | None = None

    def execute(self, query: str, params: Sequence[Any] | Mapping[str, Any] | None) -> None:
        global paramstyle
        if params:
            bound_query = bind_parameters(
                query,
                params,
                paramstyle,
                self._binding_config
            )
        else:
            bound_query = query

        bound_query = re.sub(_SQL_COMMENTS, "", bound_query)
        bound_query = re.sub(r'\s+', " ", bound_query)
        if not bound_query.upper().startswith("SELECT"):
            self._ksql(query)
            return

        return self._query(query)

    def _ksql(
            self,
            ksql: str,
            *,
            streams_properties: Mapping[str, str] | None = None,
            session_variables: Mapping[str, str] | None = None,
            command_sequence_number: int | None = None,
            timeout: Timeout | None = None
    ) -> list[Any]:
        headers = {
            "content-type": CONTENT_TYPE_JSON
        }

        body: dict[str, Any] = {
            "ksql": ksql,
            "streamsProperties": streams_properties or {},
        }
        if session_variables is not None:
            body['sessionVariables'] = session_variables
        if command_sequence_number is not None:
            body['commandSequenceNumber'] = command_sequence_number

        response = self._connection._client.post(
            "/ksql",
            headers=headers,
            json=body,
            timeout=timeout or USE_CLIENT_DEFAULT
        )
        if response.is_success:
            return response.json()

        if response.status_code == httpx.codes.BAD_REQUEST:
            error = create_ksql_error(response.json())
            raise error

        raise HTTPStatusError(
            f"{response.status_code}: {response.reason_phrase}",
            request=response.request,
            response=response
        )

    def _query(
            self,
            sql: str,
            *,
            timeout: float = 1.0,
            properties: dict[str, Any] | None = None
    ) -> QueryMetaData:
        headers = {
            "content-type": CONTENT_TYPE_NDJSON
        }

        body: dict[str, Any] = {
            "sql": sql,
            "properties": properties or {},
        }

        request = self._connection._client.build_request(
            "POST",
            "/query-stream",
            headers=headers,
            json=body,
            timeout=Timeout(timeout, read=None)
        )
        response = self._connection._client.send(
            request=request,
            stream=True
        )

        response.raise_for_status()
        self._iter = response.iter_lines()
        data = json.loads(next(self._iter))
        return cast(QueryMetaData, data)

        meta_data: QueryMetaData | None = None
        for line in response.iter_lines():
            data = json.loads(line)
            if meta_data is None:
                meta_data = cast(QueryMetaData, data)
            else:
                yield dict(zip(meta_data['columnNames'], data))


connect = Connection.connect
