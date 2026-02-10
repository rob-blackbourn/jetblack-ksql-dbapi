"""A client for ksqlDB"""

import base64
from typing import Annotated, Any, Mapping

import httpx
from httpx import AsyncClient, Timeout
from jetblack_serialization import SerializerConfig
from jetblack_serialization.json import deserialize, JSONValue
from stringcase import camelcase, snakecase  # type: ignore

from .types import HealthcheckResponse, InfoResponse


class KsqlDbClient:
    """A client for the ksqlDB service"""

    def __init__(
            self,
            url: str = "http://localhost:8088",
            api_key: str | None = None,
            api_secret: str | None = None
    ) -> None:
        self._url = url
        self._headers = {"content-type": "application/vnd.ksql.v1+json"}
        if api_key and api_secret:
            b64string = base64.b64encode(f"{api_key}:{api_secret}".encode())
            self._headers["authorization"] = f"Basic {b64string.decode()}"
        self._serializer_config = SerializerConfig(
            camelcase,
            snakecase
        )

    async def info(
            self,
            *,
            timeout: Timeout | None = None
    ) -> InfoResponse:
        async with AsyncClient() as client:
            response = await client.get(
                f"{self._url}/info",
                headers=self._headers,
                timeout=timeout
            )
            response.raise_for_status()
            dct: InfoResponse = deserialize(
                response.content,
                Annotated[InfoResponse, JSONValue()],
                self._serializer_config
            )
            return dct

    async def healthcheck(
            self,
            *,
            timeout: Timeout | None = None
    ) -> Any:
        async with AsyncClient() as client:
            response = await client.get(
                f"{self._url}/healthcheck",
                headers=self._headers,
                timeout=timeout
            )
            response.raise_for_status()
            dct: InfoResponse = deserialize(
                response.content,
                Annotated[HealthcheckResponse, JSONValue()],
                self._serializer_config
            )
            return dct

    async def ksql(
            self,
            ksql: str,
            *,
            streams_properties: Mapping[str, str] | None = None,
            session_variables: Mapping[str, str] | None = None,
            command_sequence_number: int | None = None
    ) -> Any:
        body: dict[str, Any] = {
            "ksql": ksql,
            "streamsProperties": streams_properties or {},
        }
        if session_variables is not None:
            body['sessionVariables'] = session_variables
        if command_sequence_number is not None:
            body['commandSequenceNumber'] = command_sequence_number

        async with AsyncClient() as client:
            response = await client.post(
                f"{self._url}/ksql",
                json=body,
                headers=self._headers
            )
            response.raise_for_status()
            return response.json()
