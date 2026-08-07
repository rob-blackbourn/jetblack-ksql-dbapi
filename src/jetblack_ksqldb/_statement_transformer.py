from enum import Enum, auto
from typing import Any, Sequence, TypeGuard

from lark import Transformer


class StatementStyle(Enum):
    QUERY = auto()
    COMMAND = auto()


class StatementType(Enum):
    UNSPECIFIED = auto()
    SELECT = auto()
    PRINT = auto()
    SHOW_TABLES = auto()


def is_statement_tuple(value: Any) -> TypeGuard[tuple[StatementStyle, StatementType]]:
    return (
        isinstance(value, tuple)
        and len(value) == 2
        and isinstance(value[0], StatementStyle)
        and isinstance(value[1], StatementType)
    )


class KsqlStatementTransformer(Transformer):

    def query(self, items: Sequence[Any]) -> StatementType:
        return StatementType.SELECT

    def print(self, items: Sequence[Any]) -> StatementType:
        return StatementType.PRINT

    def command_statement(self, items: Sequence[Any]) -> tuple[StatementStyle, StatementType]:
        if len(items) == 1 and isinstance(items[0], StatementType):
            statement_type = items[0]
        else:
            statement_type = StatementType.UNSPECIFIED

        return StatementStyle.COMMAND, statement_type

    def show_tables(self, items: Sequence[Any]) -> StatementType:
        return StatementType.SHOW_TABLES

    def query_statement(self, items: Sequence[Any]) -> tuple[StatementStyle, StatementType]:
        if len(items) == 1 and isinstance(items[0], StatementType):
            statement_type = items[0]
        else:
            statement_type = StatementType.UNSPECIFIED

        return StatementStyle.QUERY, statement_type

    def statements(self, items: Sequence[Any]) -> Sequence[tuple[StatementStyle, StatementType]]:
        assert all(is_statement_tuple(item) for item in items)
        return items
