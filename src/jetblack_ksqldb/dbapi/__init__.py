"""jetblack-ksqldb"""

from ._dbapi import Connection, Cursor, Description, connect
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

    # dbapi
    'Connection',
    'Cursor',
    'Description',
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
