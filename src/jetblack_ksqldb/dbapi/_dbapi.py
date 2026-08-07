from __future__ import annotations

from importlib import resources as impresources
import json
import re
from typing import (
    Any,
    Iterator,
    Literal,
    Mapping,
    NamedTuple,
    Self,
    Sequence,
    cast
)

import httpx
from httpx import (
    Client,
    HTTPStatusError,
    Timeout,
    USE_CLIENT_DEFAULT,
    BasicAuth
)

from .._types import QueryMetaData, create_ksql_error

from ._binding import BindingConfig, bind_parameters
from ._ksql_inspector import KsqlInspector
from ._paramstyles import ParamStyle
from ._statement_transformer import StatementStyle, StatementType


type QueryType = Literal['print', 'select']

CONTENT_TYPE_JSON = "application/vnd.ksql.v1+json"
CONTENT_TYPE_DELIMITED = "application/vnd.ksqlapi.delimited.v1"


class CursorDescription(NamedTuple):
    name: str
    type_code: str
    display_size: int | None
    internal_size: int | None
    precision: int | None
    scale: int | None
    null_ok: bool | None

    @classmethod
    def create(cls, query_id: str, name: str, type: str) -> Self:
        if type.upper().startswith('DECIMAL('):
            lhs, sep, rhs = type[8:-1].partition(',')
            assert sep == ','
            precision: int | None = int(lhs.strip())
            scale: int | None = int(rhs.strip())
        else:
            precision = None
            scale = None

        return cls(
            name,
            type,
            None,
            None,
            precision,
            scale,
            True
        )

    @classmethod
    def create_all(cls, meta_data: QueryMetaData) -> list[Self]:
        return [
            cls.create(meta_data['queryId'], name, type)
            for name, type in zip(meta_data['columnNames'], meta_data['columnTypes'])
        ]


class Connection:

    def __init__(
            self,
            client: Client,
            binding_config: BindingConfig,
    ) -> None:
        self._client = client
        self._binding_config = binding_config
        self._inspector = KsqlInspector()

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

    def cursor(self) -> Cursor:
        return Cursor(self._client, self._binding_config, self._inspector)


class Cursor:

    def __init__(
            self,
            client: Client,
            binding_config: BindingConfig,
            inspector: KsqlInspector
    ) -> None:
        self._client = client
        self._binding_config = binding_config
        self._inspector = inspector
        self._result: Iterator | None
        self._iter: Iterator[str] | None = None
        self._description: list[CursorDescription] | None = None

    @property
    def description(self) -> list[CursorDescription] | None:
        return self._description

    def execute(
            self,
            query: str,
            params: Sequence[Any] | Mapping[str, Any] | None = None
    ) -> None:
        import jetblack_ksqldb
        if params:
            bound_query = bind_parameters(
                query,
                params,
                jetblack_ksqldb.paramstyle,
                self._binding_config
            )
        else:
            bound_query = query

        statement_tuple = self._inspector.find_statement_type(bound_query)

        match statement_tuple:

            case (StatementStyle.COMMAND, _):
                self._ksql(bound_query)
            case (StatementStyle.QUERY, StatementType.SELECT):
                self._query_stream(bound_query, 'select')
            case (StatementStyle.QUERY, StatementType.PRINT):
                self._query_stream(bound_query, 'print')

    def executemany(
            self,
            query: str,
            params: Sequence[Sequence[Any]] | Sequence[Mapping[str, Any]]
    ) -> None:
        if len(params) == 0:
            raise ValueError("Must have params")

        import jetblack_ksqldb
        bound_queries = [
            bind_parameters(
                query,
                args,
                jetblack_ksqldb.paramstyle,
                self._binding_config
            )
            for args in params
        ]

        statement_type = self._inspector.find_statement_type(bound_queries[0])
        if statement_type != StatementStyle.COMMAND:
            raise ValueError("Expected a command")

        ksql = "".join(bound_queries)
        self._ksql(ksql)

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

        response = self._client.post(
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

    def _query_stream(
            self,
            sql: str,
            query_type: QueryType,
            *,
            timeout: float = 1.0,
            properties: dict[str, Any] | None = None
    ) -> None:
        headers = {
            "content-type": (
                CONTENT_TYPE_JSON
                if query_type == 'select' else
                CONTENT_TYPE_DELIMITED
            )
        }

        body: dict[str, Any] = {
            "sql": sql,
            "properties": properties or {},
        }

        request = self._client.build_request(
            "POST",
            "/query-stream",
            headers=headers,
            json=body,
            timeout=Timeout(timeout, read=None)
        )
        response = self._client.send(
            request=request,
            stream=True
        )

        response.raise_for_status()
        if query_type == 'select':
            self._iter = map(json.loads, response.iter_lines())
            meta_data = cast(QueryMetaData, next(self._iter))
            self._description = CursorDescription.create_all(meta_data)
        else:
            self._iter = response.iter_lines()
            self._description = None

    def fetchone(self) -> Sequence[Any]:
        assert self._iter is not None
        row = next(self._iter)
        return row

    def fetchall(self) -> Sequence[Sequence[Any]]:
        assert self._iter is not None
        return list(self._iter)

    def __iter__(self) -> Iterator[Sequence[Any]]:
        assert self._iter is not None
        return self._iter

    def _execute_print(
            self,
            sql: str,
            *,
            timeout: float = 1.0,
            properties: dict[str, Any] | None = None
    ) -> None:
        raise RuntimeError()


connect = Connection.connect
