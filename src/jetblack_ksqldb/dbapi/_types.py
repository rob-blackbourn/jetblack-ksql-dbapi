from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Callable, NamedTuple, Sequence

from ._exceptions import DataError


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
    date_to_str: Callable[[date], str] = date.isoformat
    str_to_date: Callable[[str], date] = date.fromisoformat
    datetime_to_str: Callable[[datetime], str] = _to_json_datetime
    str_to_datetime: Callable[[str], datetime] = datetime.fromisoformat
    time_to_str: Callable[[time], str] = _to_json_time
    str_to_time: Callable[[str], time] = time.fromisoformat


class DBAPITypeObject[T]:

    def __init__(
            self,
            name: str,
            types: Sequence[type],
            from_str: Callable[[str, FormatConfig], T]
    ) -> None:
        self._name = name
        self._types = set(types)
        self._from_str = from_str

    def __hash__(self) -> int:
        return hash(self._name)

    def __repr__(self) -> str:
        return f"DBAPITypeObject({self._name!r}, {self._types!r})"

    def __str__(self) -> str:
        return self._name

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DBAPITypeObject):
            return self._name == other._name
        else:
            return other in self._types


def _str_to_str(s: str, config: FormatConfig) -> str:
    return s


def _str_to_bytes(s: str, config: FormatConfig) -> bytes:
    return s.encode('utf-8')


def _str_to_number(s: str, config: FormatConfig) -> int | float:
    try:
        return int(s)
    except ValueError:
        return float(s)


def _str_to_datetime(s: str, config: FormatConfig) -> datetime:
    return config.str_to_datetime(s)


def _str_to_date(s: str, config: FormatConfig) -> date:
    return config.str_to_date(s)


def _str_to_decimal(s: str, config: FormatConfig) -> Decimal:
    return Decimal(s)


def _str_to_bool(s: str, config: FormatConfig) -> bool:
    return s.lower() == 'true'


def _str_to_int(s: str, config: FormatConfig) -> int:
    return int(s)


def _str_to_float(s: str, config: FormatConfig) -> float:
    return float(s)


def _str_to_time(s: str, config: FormatConfig) -> time:
    return config.str_to_time(s)


# Mandated types
STRING = DBAPITypeObject[str](
    'STRING',
    (str,),
    _str_to_str
)
BINARY = DBAPITypeObject[bytes](
    'BINARY',
    (bytes, bytearray, memoryview),
    _str_to_bytes
)
NUMBER = DBAPITypeObject[float](
    'NUMBER',
    (int, float),
    _str_to_number
)
DATETIME = DBAPITypeObject[datetime](
    'DATETIME',
    (datetime,),
    _str_to_datetime
)
ROWID = DBAPITypeObject[int](
    'ROWID',
    (int,),
    _str_to_int
)

BIGINT = DBAPITypeObject[int](
    'BIGINT',
    (int,),
    _str_to_int
)
BOOLEAN = DBAPITypeObject[bool](
    'BOOLEAN',
    (bool,),
    _str_to_bool
)
DATE = DBAPITypeObject[date](
    'DATE',
    (date,),
    _str_to_date
)
DECIMAL = DBAPITypeObject[Decimal](
    'DECIMAL',
    (Decimal,),
    _str_to_decimal
)
DOUBLE = DBAPITypeObject[float](
    'DOUBLE',
    (float,),
    _str_to_float
)
INTEGER = DBAPITypeObject[int](
    'INTEGER',
    (int,),
    _str_to_int
)
TIME = DBAPITypeObject[time](
    'TIME',
    (time,),
    _str_to_time
)
