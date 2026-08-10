import json
from inspect import get_annotations
from typing import (
    Any,
    Collection,
    Literal,
    Mapping,
    Sequence,
    TypedDict,
    cast,
    get_args
)

from jetblack_ksql_dbapi._ksql_types import QueryMetaData
from jetblack_ksql_dbapi._types import PY_TYPE_MAP

type WindowType = Literal['SESSION', 'HOPPING', 'TUMBLING']
type KsqlQueryType = Literal['PERSISTENT', 'PUSH', 'PULL']
type PersistentQueryType = Literal['CREATE_SOURCE', 'CREATE_AS', 'INSERT']
type KsqlQueryStatus = Literal['RUNNING', 'ERROR', 'UNRESPONSIVE', 'PAUSED']
type QueryStatusCount = Mapping[KsqlQueryStatus, int]
type SqlBaseType = Literal[
    'BOOLEAN', 'INTEGER', 'BIGINT', 'DECIMAL', 'DOUBLE', 'STRING', 'ARRAY', 'MAP',
    'STRUCT', 'TIME', 'DATE', 'TIMESTAMP', 'BYTES']
type FieldType = Literal['SYSTEM', 'KEY', 'HEADER']


class RunningQuery(TypedDict):
    queryString: str
    sinks: set[str]
    sinkKafkaTopics: set[str]
    id: str
    statusCount: QueryStatusCount
    queryType: KsqlQueryType


class SchemaInfo[FieldInfoType: 'FieldInfo'](TypedDict):
    type: SqlBaseType
    fields: list[FieldInfoType]
    memberSchema: 'SchemaInfo'
    parameters: Mapping[str, Any]


class FieldInfo(TypedDict):
    name: str
    schema: SchemaInfo
    fieldType: FieldType | None
    headerKey: str | None


class ConsumerPartitionOffsets(TypedDict):
    partition: int
    logStartOffset: int
    logEndOffset: int
    consumerOffset: int


class QueryTopicOffsetSummary(TypedDict):
    kafkaTopic: str
    offsets: list[ConsumerPartitionOffsets]


class QueryOffsetSummary(TypedDict):
    groupId: str
    topicSummaries: list[QueryTopicOffsetSummary]


class KsqlHostInfoEntity(TypedDict):
    host: str
    port: int


class QueryHostStat(TypedDict):
    host: KsqlHostInfoEntity
    name: str
    value: float
    timestamp: int


class SourceDescription(TypedDict):
    name: str
    windowType: WindowType
    readQueries: list[RunningQuery]
    writeQueries: list[RunningQuery]
    fields: list[FieldInfo]
    type: str
    timestamp: str
    statistics: str
    errorStats: str
    extended: bool
    keyFormat: str
    valueFormat: str
    topic: str
    partitions: int
    replication: int
    statement: str
    queryOffsetSummaries: list[QueryOffsetSummary]
    sourceConstraints: list[str]
    clusterStatistics: list[QueryHostStat]
    clusterErrorStats: list[QueryHostStat]


class KsqlTable(TypedDict):
    type: str
    name: str
    topic: str
    keyFormat: str
    valueFormat: str
    isWindowed: bool


class KsqlTablesResponse(TypedDict):
    statementText: str
    tables: list[KsqlTable]
    warnings: list[Any]


def _to_query_meta_data(query_id: str, table_metadata: Mapping[str, type]) -> QueryMetaData:
    return {
        'queryId': query_id,
        'columnNames': [
            col
            for col in table_metadata.keys()
        ],
        'columnTypes': [
            PY_TYPE_MAP[value].name
            for value in table_metadata.values()
        ]
    }


def _to_query_rows(rows: Sequence[Mapping[str, Any]], cols: Collection[str]) -> Sequence[Sequence[Any]]:
    return [
        [
            row[col]
            for col in cols
        ]
        for row in rows
    ]


def _to_ndjson(items: Sequence[Any]) -> str:
    return "\n".join(json.dumps(item) for item in items)


def _to_query_response(
    query_id: str,
    rows: Sequence[Mapping[str, Any]],
    meta_data: Mapping[str, type]


) -> tuple[QueryMetaData, Sequence[Sequence[Any]]]:
    query_meta_data = _to_query_meta_data(query_id, meta_data)
    query_rows = _to_query_rows(rows, meta_data.keys())
    return query_meta_data, query_rows


def _handle_table_response(
    response: KsqlTablesResponse
) -> tuple[QueryMetaData, Sequence[Sequence[Any]]]:
    annot = get_annotations(KsqlTablesResponse)
    tables_annotation, *_ = get_args(annot['tables'])
    table_metadata: Mapping[str, type] = get_annotations(tables_annotation)
    return _to_query_response('#tables', response['tables'], table_metadata)


def _handle_source_description(
        source_description: SourceDescription
) -> tuple[QueryMetaData, Sequence[Sequence[Any]]]:
    query_meta_data: QueryMetaData = {
        'queryId': '#sourceDescription',
        'columnNames': ['name', 'type', 'precision', 'scale'],
        'columnTypes': ['STRING', 'STRING', 'INTEGER', 'INTEGER']
    }
    query_rows = [
        [
            field['name'],
            field['schema']['type'],
            field['schema'].get('parameters', {}).get('precision'),
            field['schema'].get('parameters', {}).get('scale'),
        ]
        for field in source_description['fields']
    ]
    return query_meta_data, query_rows


def handle_response(
    response: Mapping[str, Any]
) -> tuple[QueryMetaData, Sequence[Sequence[Any]]] | None:
    match response['@type']:
        case 'tables':
            return _handle_table_response(cast(KsqlTablesResponse, response))

        case 'sourceDescription':
            return _handle_source_description(cast(SourceDescription, response))

        case _:
            return None


def handle_responses(
    responses: Sequence[Mapping[str, Any]]
) -> tuple[QueryMetaData, Sequence[Sequence[Any]]] | None:
    match len(responses):
        case 0:
            return None
        case 1:
            return handle_response(responses[0])
        case _:
            raise ValueError("Only one response can be handled")


if __name__ == '__main__':
    handle_responses([
        {
            '@type': 'tables',
            'statementText': 'SHOW TABLES;',
            'tables': [
                {
                    'type': 'TABLE',
                    'name': 'USER',
                    'topic': 'user',
                    'keyFormat': 'JSON',
                    'valueFormat': 'JSON',
                    'isWindowed': False
                },
                {
                    'type': 'TABLE',
                    'name': 'USER_VIEW',
                    'topic': 'USER_VIEW',
                    'keyFormat': 'JSON',
                    'valueFormat': 'JSON',
                    'isWindowed': False
                }
            ],
            'warnings': []
        }
    ]
    )
