"""jetblack-ksqldb"""

from ._client_async import AsyncKsqlDbClient
from ._dbapi import Connection, Cursor, CursorDescription, connect
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
from ._paramstyles import ParamStyle

# DBAPI compliance
apilevel = "2.0"
threadsafety = 2
paramstyle: ParamStyle = "pyformat"

__all__ = [
    # client
    'AsyncKsqlDbClient',

    # dbapi
    'Connection',
    'Cursor',
    'CursorDescription',
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
