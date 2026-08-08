from __future__ import annotations

import json
from typing import (
    Any,
    Iterator,
    Literal,
    Mapping,
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

from jetblack_ksqldb.dbapi._paramstyles import ParamStyle

from .._types import QueryMetaData, create_ksql_error

from ._binding import bind_parameters
from ._description import Description
from ._ksql_inspector import KsqlInspector
from ._statement_transformer import StatementStyle, StatementType
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
        return Cursor(self._client, self._binding_config, self._inspector, paramstyle=self._paramstyle)


class Cursor:

    def __init__(
            self,
            client: Client,
            binding_config: FormatConfig,
            inspector: KsqlInspector,
            paramstyle: ParamStyle
    ) -> None:
        self._client = client
        self._binding_config = binding_config
        self._inspector = inspector
        self._paramstyle = paramstyle
        self._result: Iterator | None
        self._iter: Iterator[Sequence[Any]] | None = None
        self._description: list[Description] | None = None

    @property
    def description(self) -> list[Description] | None:
        return self._description

    def execute(
            self,
            query: str,
            params: Sequence[Any] | Mapping[str, Any] | None = None
    ) -> None:
        if params:
            bound_query = bind_parameters(
                query,
                params,
                self._paramstyle,
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

        bound_queries = [
            bind_parameters(
                query,
                args,
                self._paramstyle,
                self._binding_config
            )
            for args in params
        ]

        (statement_style, _) = self._inspector.find_statement_type(
            bound_queries[0])
        if statement_style != StatementStyle.COMMAND:
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
            line_iter = response.iter_lines()
            meta_data = cast(QueryMetaData, json.loads(next(line_iter)))
            self._description = Description.create_all(meta_data)
            self._iter = map(self._to_row, line_iter)
        else:
            self._iter = response.iter_lines()
            self._description = None

    def _to_row(self, line: str) -> Sequence[Any]:
        assert self._iter is not None
        assert self._description is not None
        row = json.loads(
            line,
            parse_float=lambda x: x,
            parse_int=lambda x: x
        )
        return [
            description.type_code._from_str(value, self._binding_config)
            for value, description in zip(row, self._description)
        ]

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


connect = Connection.connect
