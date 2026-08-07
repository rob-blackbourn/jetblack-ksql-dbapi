from enum import Enum, auto
from typing import Any, Sequence

from lark import Transformer, Token


class StatmentType(Enum):
    SELECT = auto()
    PRINT = auto()
    COMMAND = auto()
    SHOW_TABLES = auto()


class KsqlStatementTransformer(Transformer):

    def query(self, items: Sequence[Any]) -> StatmentType:
        return StatmentType.SELECT

    def print(self, items: Sequence[Any]) -> StatmentType:
        return StatmentType.PRINT

    def command_statement(self, items: Sequence[Any]) -> StatmentType:
        if len(items) == 1 and isinstance(items[0], StatmentType):
            return items[0]

        return StatmentType.COMMAND

    def show_tables(self, items: Sequence[Any]) -> StatmentType:
        return StatmentType.SHOW_TABLES

    def query_statement(self, items: Sequence[Any]) -> StatmentType:
        assert len(items) == 1, isinstance(items[0], StatmentType)
        return items[0]

    def statements(self, items: Sequence[Any]) -> Sequence[StatmentType]:
        assert all(isinstance(item, StatmentType) for item in items)
        return items
