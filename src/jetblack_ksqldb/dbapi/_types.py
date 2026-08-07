from datetime import date, datetime, time
from decimal import Decimal

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


class DBAPITypeObject:

    def __init__(self, name: str, *types: type) -> None:
        self._name = name
        self._types = set(types)

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


# Mandated types
STRING = DBAPITypeObject('STRING', str)
BINARY = DBAPITypeObject('BINARY', bytes, bytearray, memoryview)
NUMBER = DBAPITypeObject('NUMBER', int, float)
DATETIME = DBAPITypeObject('DATETIME', datetime)
ROWID = DBAPITypeObject('ROWID', int)

BIGINT = DBAPITypeObject('BIGINT', int)
BOOLEAN = DBAPITypeObject('BOOLEAN', bool)
DATE = DBAPITypeObject('DATE', date)
DECIMAL = DBAPITypeObject('DECIMAL', Decimal)
DOUBLE = DBAPITypeObject('DOUBLE', float)
INTEGER = DBAPITypeObject('INTEGER', int)
TIME = DBAPITypeObject('TIME', time)
