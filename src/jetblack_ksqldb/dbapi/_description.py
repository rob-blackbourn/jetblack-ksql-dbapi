from typing import Mapping, NamedTuple, Self

from .._types import QueryMetaData

from ._types import (
    DBAPITypeObject,
    STRING,
    BINARY,
    NUMBER, DATETIME,
    ROWID,
    BIGINT,
    BOOLEAN,
    DATE,
    DECIMAL,
    INTEGER,
    TIME,
)


_TYPE_MAP: Mapping[str, DBAPITypeObject] = {
    'BIGINT': BIGINT,
    'BINARY': BINARY,
    'BOOLEAN': BOOLEAN,
    'BYTES': BINARY,
    'DATE': DATE,
    'DATETIME': DATETIME,
    'DECIMAL': DECIMAL,
    'INT': INTEGER,
    'INTEGER': INTEGER,
    'NUMBER': NUMBER,
    'ROWID': ROWID,
    'STRING': STRING,
    'TIME': TIME,
    'TIMESTAMP': DATETIME,
    'VARCHAR': STRING
}


class Description(NamedTuple):
    name: str
    type_code: DBAPITypeObject
    display_size: int | None
    internal_size: int | None
    precision: int | None
    scale: int | None
    null_ok: bool | None

    @classmethod
    def create(cls, name: str, type: str) -> Self:
        if type.startswith('DECIMAL('):
            lhs, sep, rhs = type[8:-1].partition(',')
            assert sep == ','
            precision: int | None = int(lhs.strip())
            scale: int | None = int(rhs.strip())
            type = type[:7]
        else:
            precision = None
            scale = None

        return cls(
            name,
            _TYPE_MAP[type],
            None,
            None,
            precision,
            scale,
            True
        )

    @classmethod
    def create_all(cls, meta_data: QueryMetaData) -> list[Self]:
        return [
            cls.create(name, type)
            for name, type in zip(meta_data['columnNames'], meta_data['columnTypes'])
        ]
