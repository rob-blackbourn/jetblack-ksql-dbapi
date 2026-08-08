from datetime import date, datetime

from jetblack_ksql_dbapi._binding import (
    _escape_parameter_sequence,
    _escape_parameter_dict,
)


def test_sequence_scalar() -> None:
    params = (
        'a',
        42,
        3.14,
        date(1967, 12, 8),
        datetime(2026, 3, 22, 12, 15, 5)
    )
    actual = _escape_parameter_sequence(params, None)
    expected = (
        "'a'",
        "42",
        "3.14e0",
        "1967-12-08",
        "2026-03-22T12:15:05.000"
    )
    assert actual == expected


def test_sequence_array() -> None:
    params = (
        [1, 2, 3],
        ['a', 'b', 'c']
    )
    actual = _escape_parameter_sequence(params, None)
    expected = (
        "ARRAY[1, 2, 3]",
        "ARRAY['a', 'b', 'c']",
    )
    assert actual == expected


def test_sequence_struct() -> None:
    params = (
        {'one': 1, 'two': 2, 'three': 3},
        {'a': 'A', 'b': 'B', 'c': 'C'}
    )
    actual = _escape_parameter_sequence(params, None)
    expected = (
        "STRUCT(one := 1, two := 2, three := 3)",
        "STRUCT(a := 'A', b := 'B', c := 'C')",
    )
    assert actual == expected


def test_dict_parameters() -> None:
    params = {
        'first': 'a',
        'second': 42,
        'third': 3.14,
        'fourth': date(1967, 12, 8),
        'fifth': datetime(2026, 3, 22, 12, 15, 5)
    }
    actual = _escape_parameter_dict(params, None)
    expected = {
        "first": "'a'",
        "second": "42",
        "third": "3.14e0",
        "fourth": "1967-12-08",
        "fifth": "2026-03-22T12:15:05.000"
    }
    assert actual == expected
