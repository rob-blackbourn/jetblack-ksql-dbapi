"""jetblack-ksql-dbapi"""

from ._ksql_client_async import AsyncKsqlDbClient

from ._connection import Connection, connect
from ._cursor import Cursor
from ._description import Description
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
from ._types import (
    BIGINT,
    BINARY,
    BOOLEAN,
    DATE,
    DATETIME,
    DECIMAL,
    INTEGER,
    NUMBER,
    ROWID,
    STRING,
    TIME,
)

# DBAPI compliance
apilevel = "2.0"
threadsafety = 2
paramstyle: ParamStyle = "pyformat"

__all__ = [
    # _ksql_client_async
    'AsyncKsqlDbClient',

    # .
    'apilevel',
    'threadsafety',
    'paramstyle',

    # dbapi
    'Connection',
    'connect',

    # .cursor
    'Cursor',

    # .description
    'Description',

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

    # ._types
    'BIGINT',
    'BINARY',
    'BOOLEAN',
    'DATE',
    'DATETIME',
    'DECIMAL',
    'INTEGER',
    'NUMBER',
    'ROWID',
    'STRING',
    'TIME',
]
