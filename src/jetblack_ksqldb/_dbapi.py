import re
from typing import Any, Iterator, Mapping, Self, Sequence


from ._binding import BindingConfig, bind_parameters
from ._client import KsqlDbClient
from ._paramstyles import ParamStyle

paramstyle: ParamStyle = "pyformat"


class Connection:

    def __init__(
            self,
            client: KsqlDbClient,
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
        client = KsqlDbClient(url, api_key, api_secret)
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
        if bound_query.upper().startswith("SELECT"):
            yield self._connection._client.ksql(query)
        else:
            return self._connection._client.query(query)


connect = Connection.connect
