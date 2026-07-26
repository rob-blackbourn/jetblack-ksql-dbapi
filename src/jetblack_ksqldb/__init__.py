"""jetblack-ksqldb"""

from ._client import KsqlDbClient
from ._dbapi import Connection, Cursor
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
connect = Connection.connect
apilevel = "2.0"
threadsafety = 2
paramstyle = "pyformat"

__all__ = [
    'KsqlDbClient',
    'Connection',
    'Cursor',

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
