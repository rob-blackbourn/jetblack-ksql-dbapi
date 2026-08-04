from enum import Enum, auto
from typing import Any, Sequence

from lark import Transformer, Token


class StatmentType(Enum):
    SELECT = auto()
    PRINT = auto()
    COMMAND = auto()


class KsqlStatementTransformer(Transformer):

    def query(self, items: Sequence[Any]) -> StatmentType:
        return StatmentType.SELECT

    def print(self, items: Sequence[Any]) -> StatmentType:
        return StatmentType.PRINT

    def command_statement(self, items: Sequence[Any]) -> StatmentType:
        return StatmentType.COMMAND

    def query_statement(self, items: Sequence[Any]) -> StatmentType:
        assert len(items) == 1, isinstance(items[0], StatmentType)
        return items[0]

    def statements(self, items: Sequence[Any]) -> Sequence[StatmentType]:
        assert all(isinstance(item, StatmentType) for item in items)
        return items
