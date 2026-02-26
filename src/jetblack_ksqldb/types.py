from typing import Any, Self, TypedDict


class QueryMetaData(TypedDict):
    queryId: str
    columnNames: list[str]
    columnTypes: list[str]


class KsqlError(Exception):

    def __init__(self, message: str, error_code: int) -> None:
        super().__init__(message)
        self.error_code = error_code


class KsqlStatementError(KsqlError):

    def __init__(
            self,
            message: str,
            error_code: int,
            statement_text: str,
            entities: list[Any]
    ) -> None:
        super().__init__(message, error_code)
        self.statement_text = statement_text
        self.entities = entities


class KsqlInsertError(KsqlError):

    def __init__(
            self,
            message: str,
            error_code: int,
            seq: int
    ) -> None:
        super().__init__(message, error_code)
        self.seq = seq


def create_ksql_error(data: dict[str, Any]) -> Exception:
    if '@type' not in data:
        return ValueError("Unknown error")

    match data['@type']:

        case "statement_error":
            return KsqlStatementError(
                data['message'],
                data['error_code'],
                data['statementText'],
                data['entities']
            )

        case "insert_error":
            return KsqlInsertError(
                data['message'],
                data['error_code'],
                data['sqe'],
            )

        case _:
            return KsqlError(
                data['message'],
                data['error_code']
            )
