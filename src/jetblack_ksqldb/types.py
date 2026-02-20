from typing import TypedDict


class QueryMetaData(TypedDict):
    queryId: str
    columnNames: list[str]
    columnTypes: list[str]
