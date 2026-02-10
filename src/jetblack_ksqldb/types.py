"""JSON types"""

from typing import Annotated, Literal, TypedDict

from jetblack_serialization.json import JSONProperty


class KsqlServerInfo(TypedDict):
    version: str
    kafka_cluster_id: str
    ksql_service_id: str
    server_status: str


class InfoResponse(TypedDict):
    ksql_server_info: Annotated[KsqlServerInfo, JSONProperty("KsqlServerInfo")]


class Healthiness(TypedDict):
    is_healthy: bool


class HealthcheckDetails(TypedDict):
    metastore: Healthiness
    kafka: Healthiness
    command_runner: Healthiness


class HealthcheckResponse(Healthiness):
    details: HealthcheckDetails
    server_state: Literal['READY']
