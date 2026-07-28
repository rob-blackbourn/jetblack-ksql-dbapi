"""A client for ksqlDB"""

import json
from typing import Any, Iterator, Mapping, cast

import httpx
from httpx import (
    Client,
    HTTPStatusError,
    Timeout,
    USE_CLIENT_DEFAULT,
    BasicAuth
)

from .types import QueryMetaData, create_ksql_error

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
        auth = (
            BasicAuth(api_key, api_secret)
            if api_key and api_secret else
            None
        )
        self._client = Client(base_url=url, auth=auth, http1=False, http2=True)

    def close(self) -> None:
        self._client.close()

    def info(
            self,
            *,
            timeout: Timeout | None = None
    ) -> dict[str, Any]:
        headers = {
            "content-type": CONTENT_TYPE_JSON
        }

        response = self._client.get(
            "/info",
            headers=headers,
            timeout=timeout or USE_CLIENT_DEFAULT
        )
        response.raise_for_status()
        return response.json()

    def healthcheck(
            self,
            *,
            timeout: Timeout | None = None
    ) -> dict[str, Any]:
        headers = {
            "content-type": CONTENT_TYPE_JSON
        }

        response = self._client.get(
            "/healthcheck",
            headers=headers,
            timeout=timeout or USE_CLIENT_DEFAULT
        )
        response.raise_for_status()
        return response.json()

    def ksql(
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

    def query(
            self,
            ksql: str,
            *,
            streams_properties: Mapping[str, str] | None = None,
            timeout: float = 1.0
    ) -> Iterator[Any]:
        headers = {
            "content-type": CONTENT_TYPE_JSON
        }

        body: dict[str, Any] = {
            "ksql": ksql,
            "streamsProperties": streams_properties or {},
        }

        with self._client.stream(
            "POST",
            "/query",
            headers=headers,
            json=body,
            timeout=Timeout(timeout, read=None)
        ) as response:
            response.raise_for_status()
            meta_data: QueryMetaData | None = None
            for line in response.iter_lines():
                data = json.loads(line)
                if meta_data is None:
                    meta_data = cast(QueryMetaData, data)
                else:
                    yield dict(zip(meta_data["columnNames"], data))

    def queury_status(
            self,
            command_id: str,
            *,
            timeout: Timeout | None = None
    ) -> dict[str, Any]:
        headers = {
            "content-type": CONTENT_TYPE_JSON
        }

        response = self._client.get(
            f"/status/{command_id}",
            headers=headers,
            timeout=timeout or USE_CLIENT_DEFAULT
        )
        response.raise_for_status()
        return response.json()

    def query_stream(
            self,
            sql: str,
            *,
            timeout: float = 1.0,
            properties: dict[str, Any] | None = None
    ) -> Iterator[Any]:
        headers = {
            "content-type": CONTENT_TYPE_NDJSON
        }

        body: dict[str, Any] = {
            "sql": sql,
            "properties": properties or {},
        }

        with self._client.stream(
            "POST",
            "/query-stream",
            headers=headers,
            json=body,
            timeout=Timeout(timeout, read=None)
        ) as response:
            response.raise_for_status()
            meta_data: QueryMetaData | None = None
            for line in response.iter_lines():
                data = json.loads(line)
                if meta_data is None:
                    meta_data = cast(QueryMetaData, data)
                else:
                    yield dict(zip(meta_data['columnNames'], data))

    def close_query(
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

        response = self._client.post(
            "/close-query",
            headers=headers,
            json=body,
            timeout=timeout
        )
        return response.is_success

    def inserts_stream(
            self,
            target: str,
            rows: list[Any]
    ) -> Iterator[Any]:
        headers = {
            "content-type": CONTENT_TYPE_NDJSON
        }

        body = json.dumps({"target": target}) + "\n"
        body += "\n".join(json.dumps(row) for row in rows)

        with self._client.stream(
            "POST",
            "/inserts-stream",
            headers=headers,
            content=body,
        ) as response:
            for line in response.iter_lines():
                yield json.loads(line)
