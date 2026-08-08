"""An asyncio cursor class for ksql"""

import json
from typing import (
    Any,
    AsyncIterator,
    Literal,
    Mapping,
    Sequence,
    cast
)

try:
    import httpx  # type: ignore
    from httpx import (  # type: ignore
        AsyncClient,
        HTTPStatusError,
        Timeout,
        USE_CLIENT_DEFAULT,
    )
except ModuleNotFoundError:
    import httpx2 as httpx  # type: ignore
    from httpx2 import (  # type: ignore
        AsyncClient,
        HTTPStatusError,
        Timeout,
        USE_CLIENT_DEFAULT,
    )

from .._binding import bind
from .._description import Description
from .._exceptions import Error, NotSupportedError
from .._ksql_inspector import KsqlInspector
from .._ksql_types import QueryMetaData, create_ksql_error
from .._paramstyles import ParamStyle
from .._statement_transformer import StatementStyle, StatementType
from .._types import FormatConfig

from ._abc import Cursor

type QueryType = Literal['print', 'select']

CONTENT_TYPE_JSON = "application/vnd.ksql.v1+json"
CONTENT_TYPE_DELIMITED = "application/vnd.ksqlapi.delimited.v1"


class KsqlAsyncCursor(Cursor):
    """An async ksql cursor."""

    def __init__(
            self,
            client: AsyncClient,
            format_config: FormatConfig,
            inspector: KsqlInspector,
            paramstyle: ParamStyle,
            close_timeout: float | None,
    ) -> None:
        self._client = client
        self._format_config = format_config
        self._inspector = inspector
        self._paramstyle = paramstyle
        self._close_timeout = close_timeout
        self._query_id: str | None = None
        self._iter: AsyncIterator[Sequence[Any]] | None = None
        self._description: list[Description] | None = None

        self.arraysize: int = 1

    def _clear_state(self) -> None:
        self._query_id = None
        self._iter = None
        self._description = None

    @property
    def description(self) -> list[Description] | None:
        return self._description

    @property
    def rowcount(self) -> int:
        # TODO: There can only be a rowcount for "pull" queries. We could detect
        # this in the parser. Then we would need to fetch all the rows and wrap
        # the result iterator.
        return -1

    async def callproc(self, procname: str, parameters: Sequence[Any] | None = None) -> None:
        raise NotSupportedError("ksql does not support stored procedures")

    async def close(self) -> None:
        if self._query_id is None:
            return

        headers = {
            "content-type": CONTENT_TYPE_JSON
        }

        body = {
            "queryId": self._query_id
        }

        response = await self._client.post(
            "/close-query",
            headers=headers,
            json=body,
            timeout=self._close_timeout
        )
        if not response.is_success:
            raise Error("Failed to close query")

    async def execute(
            self,
            query: str,
            params: Sequence[Any] | Mapping[str, Any] | None = None
    ) -> None:
        self._clear_state()

        if params:
            bound_query = bind(
                query,
                params,
                self._paramstyle,
                self._format_config
            )
        else:
            bound_query = query

        statement_tuple = self._inspector.find_statement_type(bound_query)

        match statement_tuple:

            case (StatementStyle.COMMAND, _):
                await self._ksql(bound_query)
            case (StatementStyle.QUERY, StatementType.SELECT):
                await self._query_stream(bound_query, 'select')
            case (StatementStyle.QUERY, StatementType.PRINT):
                await self._query_stream(bound_query, 'print')

    async def executemany(
            self,
            query: str,
            param_seq: Sequence[Sequence[Any]] | Sequence[Mapping[str, Any]]
    ) -> None:
        self._clear_state()

        if len(param_seq) == 0:
            raise ValueError("Must have params")

        bound_queries = [
            bind(
                query,
                params,
                self._paramstyle,
                self._format_config
            )
            for params in param_seq
        ]

        (statement_style, _) = self._inspector.find_statement_type(
            bound_queries[0])
        if statement_style != StatementStyle.COMMAND:
            raise ValueError("Expected a command")

        ksql = "".join(bound_queries)
        await self._ksql(ksql)

    async def _ksql(
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

        response = await self._client.post(
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

    async def _query_stream(
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
        response = await self._client.send(
            request=request,
            stream=True
        )

        response.raise_for_status()
        if query_type == 'select':
            line_iter = response.aiter_lines()
            meta_data = cast(QueryMetaData, json.loads(await anext(line_iter)))
            self._description = Description.create_all(meta_data)
            self._query_id = meta_data['queryId']
            self._iter = (self._to_row(line) async for line in line_iter)
        else:
            self._iter = response.aiter_lines()
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
            description.type_code.from_sql(value, self._format_config)
            for value, description in zip(row, self._description)
        ]

    async def fetchone(self) -> Sequence[Any]:
        if self._iter is None:
            raise Error("No results available")

        return await anext(self._iter)

    async def fetchmany(self, size: int | None = None) -> Sequence[Sequence[Any]]:
        if self._iter is None:
            raise Error("No results available")

        if size is None:
            size = self.arraysize

        return [await anext(self._iter) for _ in range(size)]

    async def fetchall(self) -> Sequence[Sequence[Any]]:
        if self._iter is None:
            raise Error("No results available")

        return [row async for row in self._iter]

    async def nextset(self) -> bool | None:
        return None

    def __aiter__(self) -> AsyncIterator[Sequence[Any]]:
        if self._iter is None:
            raise Error("No results available")

        return self._iter
