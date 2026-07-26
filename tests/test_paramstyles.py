from jetblack_ksqldb._paramstyles import convert, Parameters, ParamStyle, PARAMSTYLES


def test_convert() -> None:
    sequence_params = ['a', 'b', 'c', 'd']
    dict_params = {
        'param1': 'a',
        'param2': 'b',
        'param3': 'c',
        'param4': 'd',
    }

    tests: dict[ParamStyle, tuple[str, Parameters]] = {
        'qmark': ('SELECT * FROM ? WHERE ? > ? OR ? IS NOT NULL', sequence_params),
        'numeric': ('SELECT * FROM :1 WHERE :2 > :3 OR :4 IS NOT NULL', sequence_params),
        'named': ('SELECT * FROM :param1 WHERE :param2 > :param3 OR :param4 IS NOT NULL', dict_params),
        'format': ('SELECT * FROM %s WHERE %s > %s OR %s IS NOT NULL', sequence_params),
        'pyformat': ('SELECT * FROM %(param1)s WHERE %(param2)s > %(param3)s OR %(param4)s IS NOT NULL', dict_params),
    }

    for from_paramstyle in PARAMSTYLES['all']:
        for to_paramstyle in PARAMSTYLES['all']:
            from_query, from_params = tests[from_paramstyle]
            to_query, to_params = tests[to_paramstyle]
            query, params = convert(
                from_paramstyle,
                to_paramstyle,
                from_query,
                from_params
            )
            assert query == to_query
            assert params == to_params
