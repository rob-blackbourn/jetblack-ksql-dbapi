"""jetblack-ksqldb"""

from ._async_client import AsyncKsqlDbClient
from ._dbapi import Connection, Cursor, connect, paramstyle
from ._exceptions import (
    Warning,
    Error,
    InterfaceError,
    DatabaseError,
    DataError,
    OperationalError,
    IntegrityError,
    InternalError,
    ProgrammingError,
    NotSupportedError,
)

# DBAPI compliance
apilevel = "2.0"
threadsafety = 2

__all__ = [
    'AsyncKsqlDbClient',
    'Connection',
    'Cursor',
    'connect',
    'paramstyle',

    # exceptions
    'Warning',
    'Error',
    'InterfaceError',
    'DatabaseError',
    'DataError',
    'OperationalError',
    'IntegrityError',
    'InternalError',
    'ProgrammingError',
    'NotSupportedError',
]
