from typing import Self

from ._client import KsqlDbClient


class Connection:

    def __init__(self, client: KsqlDbClient) -> None:
        self._client = client

    @classmethod
    def connect(
            cls,
            url: str = "http://localhost:8088",
            api_key: str | None = None,
            api_secret: str | None = None
    ) -> Self:
        client = KsqlDbClient(url, api_key, api_secret)
        return cls(client)


class Cursor:

    def __init__(self, connection: Connection) -> None:
        self._connection = connection
