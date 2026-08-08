from __future__ import annotations

import json
from typing import (
    Any,
    Iterator,
    Literal,
    Mapping,
    Sequence,
    cast
)

try:
    import httpx  # type: ignore
    from httpx import (  # type: ignore
        Client,
        HTTPStatusError,
        Timeout,
        USE_CLIENT_DEFAULT,
    )
except ModuleNotFoundError:
    import httpx2 as httpx  # type: ignore
    from httpx2 import (  # type: ignore
        Client,
        HTTPStatusError,
        Timeout,
        USE_CLIENT_DEFAULT,
    )

from ._abc import Cursor
from ._binding import bind
from ._description import Description
from ._exceptions import Error, NotSupportedError, ProgrammingError
from ._ksql_inspector import KsqlInspector
from ._ksql_types import QueryMetaData, create_ksql_error
from ._paramstyles import ParamStyle
from ._statement_transformer import StatementStyle, StatementType
from ._types import FormatConfig


type QueryType = Literal['print', 'select']

CONTENT_TYPE_JSON = "application/vnd.ksql.v1+json"
CONTENT_TYPE_DELIMITED = "application/vnd.ksqlapi.delimited.v1"


class KsqlSyncCursor(Cursor):
    """A PEP-294 compliant cursor class"""

    def __init__(
            self,
            client: Client,
            binding_config: FormatConfig,
            inspector: KsqlInspector,
            paramstyle: ParamStyle,
            close_timeout: float,
    ) -> None:
        self._client = client
        self._binding_config = binding_config
        self._inspector = inspector
        self._paramstyle = paramstyle
        self._query_id: str | None = None
        self._iter: Iterator[Sequence[Any]] | None = None
        self._description: list[Description] | None = None
        self._close_timeout = close_timeout

        self.arraysize: int = 1

    @property
    def description(self) -> Sequence[Description] | None:
        return self._description

    @property
    def rowcount(self) -> int:
        # TODO: There can only be a rowcount for "pull" queries. We could detect
        # this in the parser. Then we would need to fetch all the rows and wrap
        # the result iterator.
        return -1

    def callproc(self, procname: str, parameters: Sequence[Any] | None = None) -> None:
        raise NotSupportedError("ksql does not support stored procedures")

    def close(self) -> None:
        if self._query_id is None:
            return

        headers = {
            "content-type": CONTENT_TYPE_JSON
        }

        body = {
            "queryId": self._query_id
        }

        response = self._client.post(
            "/close-query",
            headers=headers,
            json=body,
            timeout=self._close_timeout
        )
        if not response.is_success:
            raise Error("Failed to close query")

    def execute(
            self,
            query: str,
            params: Sequence[Any] | Mapping[str, Any] | None = None
    ) -> None:
        bound_query = bind(
            query,
            params,
            self._paramstyle,
            self._binding_config
        )

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
            param_seq: Sequence[Sequence[Any]] | Sequence[Mapping[str, Any]]
    ) -> None:
        if len(param_seq) == 0:
            raise ProgrammingError("Must have params")

        bound_queries = [
            bind(
                query,
                args,
                self._paramstyle,
                self._binding_config
            )
            for args in param_seq
        ]

        (statement_style, _) = self._inspector.find_statement_type(
            bound_queries[0]
        )
        if statement_style != StatementStyle.COMMAND:
            raise ProgrammingError("Expected a command")

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
            self._query_id = meta_data['queryId']
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
            description.type_code.from_sql(value, self._binding_config)
            for value, description in zip(row, self._description)
        ]

    def fetchone(self) -> Sequence[Any] | None:
        if self._iter is None:
            raise Error("No results available")

        return next(self._iter, None)

    def fetchmany(self, size: int | None = None) -> Sequence[Sequence[Any]]:
        if self._iter is None:
            raise Error("No results available")

        if size is None:
            size = self.arraysize

        rows = []
        while size > 0:
            try:
                rows.append(next(self._iter))
            except StopIteration:
                break
            size -= 1

        return rows

    def fetchall(self) -> Sequence[Sequence[Any]]:
        if self._iter is None:
            raise Error("No results available")

        return list(self._iter)

    def nextset(self) -> bool | None:
        return None

    def __iter__(self) -> Iterator[Sequence[Any]]:
        if self._iter is None:
            raise Error("No results available")

        return self._iter
