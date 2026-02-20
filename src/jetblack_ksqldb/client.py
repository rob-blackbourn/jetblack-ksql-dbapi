"""A client for ksqlDB"""

import json
from typing import Any, AsyncIterator, Mapping, cast

from httpx import AsyncClient, Timeout, USE_CLIENT_DEFAULT, BasicAuth

from .types import QueryMetaData

CONTENT_TYPE_JSON = "application/vnd.ksql.v1+json"
CONTENT_TYPE_NDJSON = "application/vnd.ksqlapi.delimited.v1"


class KsqlDbClient:
    """A client for the ksqlDB service"""

    def __init__(
            self,
            url: str = "http://localhost:8088",
            api_key: str | None = None,
            api_secret: str | None = None
    ) -> None:
        self._url = url
        self._auth = (
            BasicAuth(api_key, api_secret)
            if api_key and api_secret else
            None
        )

    async def info(
            self,
            *,
            timeout: Timeout | None = None
    ) -> dict[str, Any]:
        headers = {
            "content-type": CONTENT_TYPE_JSON
        }

        async with AsyncClient(headers=headers, auth=self._auth) as client:
            response = await client.get(
                f"{self._url}/info",
                timeout=timeout or USE_CLIENT_DEFAULT
            )
            response.raise_for_status()
            return response.json()

    async def healthcheck(
            self,
            *,
            timeout: Timeout | None = None
    ) -> dict[str, Any]:
        headers = {
            "content-type": CONTENT_TYPE_JSON
        }

        async with AsyncClient(headers=headers, auth=self._auth) as client:
            response = await client.get(
                f"{self._url}/healthcheck",
                timeout=timeout or USE_CLIENT_DEFAULT
            )
            response.raise_for_status()
            return response.json()

    async def ksql(
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

        async with AsyncClient(headers=headers, auth=self._auth) as client:
            response = await client.post(
                f"{self._url}/ksql",
                json=body,
                timeout=timeout or USE_CLIENT_DEFAULT
            )
            response.raise_for_status()
            return response.json()

    async def query(
            self,
            ksql: str,
            *,
            streams_properties: Mapping[str, str] | None = None,
            timeout: float = 1.0
    ) -> AsyncIterator[Any]:
        headers = {
            "content-type": CONTENT_TYPE_JSON
        }

        body: dict[str, Any] = {
            "ksql": ksql,
            "streamsProperties": streams_properties or {},
        }

        async with AsyncClient(headers=headers, auth=self._auth) as client:
            async with client.stream(
                "POST",
                f"{self._url}/query",
                json=body,
                timeout=Timeout(timeout, read=None)
            ) as response:
                response.raise_for_status()
                meta_data: QueryMetaData | None = None
                async for line in response.aiter_lines():
                    data = json.loads(line)
                    if meta_data is None:
                        meta_data = cast(QueryMetaData, data)
                    else:
                        yield dict(zip(meta_data["columnNames"], data))

    async def queury_status(
            self,
            command_id: str,
            *,
            timeout: Timeout | None = None
    ) -> dict[str, Any]:
        headers = {
            "content-type": CONTENT_TYPE_JSON
        }

        async with AsyncClient(headers=headers, auth=self._auth) as client:
            response = await client.get(
                f"{self._url}/status/{command_id}",
                timeout=timeout or USE_CLIENT_DEFAULT
            )
            response.raise_for_status()
            return response.json()

    async def query_stream(
            self,
            sql: str,
            *,
            timeout: float = 1.0,
            properties: dict[str, Any] | None = None
    ) -> AsyncIterator[Any]:
        headers = {
            "content-type": CONTENT_TYPE_NDJSON
        }

        body: dict[str, Any] = {
            "sql": sql,
            "properties": properties or {},
        }

        async with AsyncClient(headers=headers, auth=self._auth, http1=False, http2=True) as client:
            async with client.stream(
                "POST",
                f"{self._url}/query-stream",
                json=body,
                timeout=Timeout(timeout, read=None)
            ) as response:
                response.raise_for_status()
                meta_data: QueryMetaData | None = None
                async for line in response.aiter_lines():
                    data = json.loads(line)
                    if meta_data is None:
                        meta_data = cast(QueryMetaData, data)
                    else:
                        yield dict(zip(meta_data['columnNames'], data))

    async def close_query(
            self,
            query_id: str,
            *,
            timeout: Timeout | None = None,
    ) -> bool:
        headers = {
            "content-type": CONTENT_TYPE_JSON
        }

        body = {
            "queryId": query_id
        }

        async with AsyncClient(headers=headers, auth=self._auth) as client:
            response = await client.post(
                f"{self._url}/close-query",
                json=body,
                timeout=timeout
            )
            return response.is_success

    async def inserts_stream(
            self,
            target: str,
            rows: list[Any]
    ) -> AsyncIterator[Any]:
        headers = {
            "content-type": CONTENT_TYPE_NDJSON
        }

        body = json.dumps({"target": target}) + "\n"
        body += "\n".join(json.dumps(row) for row in rows)

        async with AsyncClient(headers=headers, auth=self._auth, http1=False, http2=True) as client:
            async with client.stream(
                "POST",
                f"{self._url}/inserts-stream",
                content=body,
            ) as response:
                async for line in response.aiter_lines():
                    yield json.loads(line)
