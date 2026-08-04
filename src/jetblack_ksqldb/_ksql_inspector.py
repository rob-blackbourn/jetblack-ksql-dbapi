from importlib import resources as impresources

from lark import Lark

from . import _grammars
from ._statement_transformer import KsqlStatementTransformer, StatmentType


class KsqlInspector:

    def __init__(self):
        inp_file = impresources.files(_grammars) / 'ksql.lark'
        with inp_file.open(mode="r") as f:
            grammar = f.read()
        self._parser = Lark(grammar, start='statements')
        self._transformer = KsqlStatementTransformer()

    def find_statement_type(self, query: str) -> StatmentType:
        tree = self._parser.parse(query)
        statement_types = self._transformer.transform(tree)
        if len(statement_types) != 1:
            raise ValueError("Expected a single statement")
        return statement_types[0]
