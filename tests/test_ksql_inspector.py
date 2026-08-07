from jetblack_ksqldb.dbapi._ksql_inspector import (
    KsqlInspector,
    StatementStyle,
    StatementType
)


def test_select() -> None:
    inspector = KsqlInspector()
    sql = "SELECT * FROM user;"
    statement_type = inspector.find_statement_type(sql)
    assert statement_type == (StatementStyle.QUERY, StatementType.SELECT)


def test_print() -> None:
    inspector = KsqlInspector()
    sql = "PRINT user FROM BEGINNING;"
    statement_type = inspector.find_statement_type(sql)
    assert statement_type == (StatementStyle.QUERY, StatementType.PRINT)


def test_show_tables() -> None:
    inspector = KsqlInspector()
    sql = "SHOW TABLES;"
    statement_type = inspector.find_statement_type(sql)
    assert statement_type == (StatementStyle.COMMAND,
                              StatementType.SHOW_TABLES)
