from jetblack_ksqldb._ksql_inspector import KsqlInspector, StatmentType


def test_select() -> None:
    inspector = KsqlInspector()
    sql = "SELECT * FROM user;"
    statement_type = inspector.find_statement_type(sql)
    assert statement_type == StatmentType.SELECT


def test_show_tables() -> None:
    inspector = KsqlInspector()
    sql = "SHOW TABLES;"
    statement_type = inspector.find_statement_type(sql)
    assert statement_type == StatmentType.SHOW_TABLES
