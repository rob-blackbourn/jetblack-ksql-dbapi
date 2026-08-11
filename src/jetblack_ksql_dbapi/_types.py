"""DBAPI types."""

from base64 import b64encode
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Callable, Mapping, NamedTuple, Sequence

from ._exceptions import DataError, ProgrammingError


def Date(year: int, month: int, day: int) -> date:
    try:
        return date(year, month, day)
    except BaseException as error:
        raise DataError("Invalid date") from error


def Time(hour: int, minute: int, second: int) -> time:
    try:
        return time(hour, minute, second)
    except BaseException as error:
        raise DataError("Invalid time") from error


def Timestamp(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
) -> datetime:
    try:
        return datetime(year, month, day, hour, minute, second)
    except BaseException as error:
        raise DataError("Invalid timestamp") from error


def DateFromTicks(ticks: float) -> date:
    try:
        return date.fromtimestamp(ticks)
    except BaseException as error:
        raise DataError("Invalid ticks") from error


def TimeFromTicks(ticks: float) -> time:
    try:
        return datetime.fromtimestamp(ticks).time()
    except BaseException as error:
        raise DataError("Invalid ticks") from error


def TimestampFromTicks(ticks: float) -> datetime:
    try:
        return datetime.fromtimestamp(ticks)
    except BaseException as error:
        raise DataError("Invalid ticks") from error


def _to_json_datetime(ts: datetime) -> str:
    return ts.isoformat("T", "milliseconds")


def _to_json_time(t: time) -> str:
    return t.isoformat("milliseconds")


class FormatConfig(NamedTuple):
    date_to_sql: Callable[[date], str] = date.isoformat
    sql_to_date: Callable[[str], date] = date.fromisoformat
    datetime_to_sql: Callable[[datetime], str] = _to_json_datetime
    sql_to_datetime: Callable[[str], datetime] = datetime.fromisoformat
    time_to_sql: Callable[[time], str] = _to_json_time
    sql_to_time: Callable[[str], time] = time.fromisoformat


class DBAPITypeObject[T]:

    def __init__(
            self,
            name: str,
            types: Sequence[type],
            from_sql: Callable[[str, FormatConfig], T],
            to_sql: Callable[[T, FormatConfig], str]
    ) -> None:
        self.name = name
        self.types = set(types)
        self._from_sql = from_sql
        self.to_sql = to_sql

    def from_sql(self, s: str | T | None, config: FormatConfig) -> T | None:
        if isinstance(s, str):
            return self._from_sql(s, config)
        return s

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return f"DBAPITypeObject({self.name!r}, {self.types!r})"

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DBAPITypeObject):
            return self.name == other.name
        else:
            return other in self.types


_ESCAPE_TABLE = [chr(x) for x in range(128)]
_ESCAPE_TABLE[0] = "\\0"
_ESCAPE_TABLE[ord("\\")] = "\\\\"
_ESCAPE_TABLE[ord("\n")] = "\\n"
_ESCAPE_TABLE[ord("\r")] = "\\r"
_ESCAPE_TABLE[ord("\032")] = "\\Z"
_ESCAPE_TABLE[ord('"')] = '\\"'
_ESCAPE_TABLE[ord("'")] = "\\'"


def _sql_to_str(s: str, config: FormatConfig) -> str:
    return s


def _str_to_sql(s: str, config: FormatConfig) -> str:
    return "'%s'" % s.translate(_ESCAPE_TABLE)


def _sql_to_bytes(s: str, config: FormatConfig) -> bytes:
    return s.encode('utf-8')


def _bytes_to_sql(b: bytes, config: FormatConfig) -> str:
    return "'%s'" % b64encode(b).decode('ascii')


def _sql_to_number(s: str, config: FormatConfig) -> int | float:
    try:
        return int(s)
    except ValueError:
        return float(s)


def _number_to_sql(n: int | float, config: FormatConfig) -> str:
    return (
        _int_to_sql(n, config)
        if isinstance(n, int) else
        _float_to_sql(n, config)
    )


def _sql_to_datetime(s: str, config: FormatConfig) -> datetime:
    return config.sql_to_datetime(s)


def _datetime_to_sql(dt: datetime, config: FormatConfig) -> str:
    return config.datetime_to_sql(dt)


def _sql_to_date(s: str, config: FormatConfig) -> date:
    return config.sql_to_date(s)


def _date_to_sql(d: date, config: FormatConfig) -> str:
    return config.date_to_sql(d)


def _sql_to_decimal(s: str, config: FormatConfig) -> Decimal:
    return Decimal(s)


def _decimal_to_sql(d: Decimal, config: FormatConfig) -> str:
    return str(d)


def _sql_to_bool(s: str, config: FormatConfig) -> bool:
    return s.lower() == 'true'


def _bool_to_sql(b: bool, config: FormatConfig) -> str:
    return "true" if b else "false"


def _sql_to_int(s: str, config: FormatConfig) -> int:
    return int(s)


def _int_to_sql(i: int, config: FormatConfig) -> str:
    return str(i)


def _sql_to_float(s: str, config: FormatConfig) -> float:
    return float(s)


def _float_to_sql(f: float, config: FormatConfig) -> str:
    s = repr(f)
    if s in ("inf", "-inf", "nan"):
        raise ValueError(f"Invalid float: {s}")
    if "e" not in s:
        s += "e0"
    return s


def _sql_to_time(s: str, config: FormatConfig) -> time:
    return config.sql_to_time(s)


def _time_to_sql(t: time, config: FormatConfig) -> str:
    return config.time_to_sql(t)


# Mandated types
STRING = DBAPITypeObject[str](
    'STRING',
    (str,),
    _sql_to_str,
    _str_to_sql
)
BINARY = DBAPITypeObject[bytes](
    'BINARY',
    (bytes, bytearray, memoryview),
    _sql_to_bytes,
    _bytes_to_sql
)
NUMBER = DBAPITypeObject[float](
    'NUMBER',
    (int, float),
    _sql_to_number,
    _number_to_sql
)
DATETIME = DBAPITypeObject[datetime](
    'DATETIME',
    (datetime,),
    _sql_to_datetime,
    _datetime_to_sql
)
ROWID = DBAPITypeObject[int](
    'ROWID',
    (int,),
    _sql_to_int,
    _int_to_sql
)
BIGINT = DBAPITypeObject[int](
    'BIGINT',
    (int,),
    _sql_to_int,
    _int_to_sql
)
BOOLEAN = DBAPITypeObject[bool](
    'BOOLEAN',
    (bool,),

    _sql_to_bool,
    _bool_to_sql
)
DATE = DBAPITypeObject[date](
    'DATE',
    (date,),
    _sql_to_date,
    _date_to_sql
)
DECIMAL = DBAPITypeObject[Decimal](
    'DECIMAL',
    (Decimal,),
    _sql_to_decimal,
    _decimal_to_sql
)
DOUBLE = DBAPITypeObject[float](
    'DOUBLE',
    (float,),
    _sql_to_float,
    _float_to_sql
)
INTEGER = DBAPITypeObject[int](
    'INTEGER',
    (int,),
    _sql_to_int,
    _int_to_sql
)
TIME = DBAPITypeObject[time](
    'TIME',
    (time,),
    _sql_to_time,
    _time_to_sql
)

PY_TYPE_MAP: Mapping[type, DBAPITypeObject] = {
    str: STRING,
    bytes: BINARY,
    bytearray: BINARY,
    memoryview: BINARY,
    int: INTEGER,
    float: DOUBLE,
    Decimal: DECIMAL,
    bool: BOOLEAN,
    datetime: DATETIME,
    date: DATE,
    time: TIME
}


def _raise_if_not_type(value: Any, type_: type | tuple[type]) -> bool:
    if not isinstance(value, type_):
        raise ProgrammingError("Invalid type")
    return True


def to_sql(parameter: Any, config: FormatConfig) -> str:

    if parameter is None:

        return "NULL"

    elif isinstance(parameter, (list, tuple)):

        args = ", ".join(
            to_sql(v, config)
            for v in parameter
        )
        return f"ARRAY[{args}]"

    elif isinstance(parameter, Mapping):

        args = ", ".join(
            f"{k} := {to_sql(v, config)}"
            for k, v in parameter.items()
            if _raise_if_not_type(k, str)
        )
        return f"STRUCT({args})"

    else:

        py_type = type(parameter)

        if py_type in PY_TYPE_MAP:
            return PY_TYPE_MAP[py_type].to_sql(parameter, config)
        else:
            raise TypeError(f"Type {py_type} not supported: {parameter}")
