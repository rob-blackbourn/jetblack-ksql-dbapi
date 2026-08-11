import asyncio
from datetime import date, datetime
from decimal import Decimal
import json
from typing import Any, TypedDict, cast

from jetblack_ksql_dbapi.aio import connect, Connection


class CurrencyDict(TypedDict):
    ccy: str
    name: str
    minor_unit: int
    numeric_code: int
    is_legacy: bool
    is_major: bool
    is_ndf: bool
    is_commodity: bool
    is_per_usd: bool


SECURITY_TABLE_DROP = "DROP TABLE IF EXISTS security_table DELETE TOPIC;"
STRATEGY_TABLE_DROP = "DROP TABLE IF EXISTS strategy_table DELETE TOPIC;"
TRADE_STREAM_DROP = "DROP STREAM IF EXISTS trade DELETE TOPIC;"
POSITION_TABLE_DROP = "DROP TABLE IF EXISTS position_table DELETE TOPIC;"
PRICE_STREAM_DROP = "DROP STREAM IF EXISTS price DELETE TOPIC;"
CURRENCY_TABLE_DROP = "DROP TABLE IF EXISTS currency_table DELETE TOPIC;"
CURRENCY_QUERYABLE_DROP = "DROP TABLE IF EXISTS currency;"
FX_RATE_STREAM_DROP = "DROP STREAM IF EXISTS fx_rate DELETE TOPIC;"

DROP = {
    'fx_rate': FX_RATE_STREAM_DROP,
    'currency_queryable': CURRENCY_QUERYABLE_DROP,
    'currency_table': CURRENCY_TABLE_DROP,
    'price': PRICE_STREAM_DROP,
    'position_table': POSITION_TABLE_DROP,
    'trade': TRADE_STREAM_DROP,
    'strategy_table': STRATEGY_TABLE_DROP,
    'security_table': SECURITY_TABLE_DROP,
}

SECURITY_TABLE_DDL = """\
CREATE OR REPLACE TABLE security_table
(
    security_id     BIGINT  PRIMARY KEY,
    ticker          VARCHAR,
    description     VARCHAR,
    contract_size   INT,
    ccy             VARCHAR
) WITH (
    kafka_topic='security',
    value_format='json',
    key_format='json',
    partitions=1
);"""

STRATEGY_TABLE_DDL = """\
CREATE OR REPLACE TABLE strategy_table
(
    strategy_id     BIGINT  PRIMARY KEY,
    name            VARCHAR,
    ccy             VARCHAR
)
WITH (
    kafka_topic='strategy',
    value_format='json',
    key_format='json',
    partitions=1
);"""

TRADE_STREAM_DDL = """\
CREATE OR REPLACE STREAM trade
(
    trade_id        BIGINT KEY,
    version         BIGINT KEY,
    security_id     BIGINT,
    strategy_id     BIGINT,
    quantity        DOUBLE,
    price           DOUBLE
)
WITH (
    kafka_topic='trade',
    value_format='json',
    key_format='json',
    partitions=1
);
"""

POSITION_TABLE_DDL = """\
CREATE OR REPLACE TABLE position_table
(
    security_id     BIGINT PRIMARY KEY,
    strategy_id     BIGINT PRIMARY KEY,
    quantity        DOUBLE,
    cost            DOUBLE,
    value           DOUBLE,
    realized        DOUBLE
)
WITH (
    kafka_topic='position',
    value_format='json',
    key_format='json',
    partitions=1
);
"""

PRICE_STREAM_DDL = """\
CREATE OR REPLACE STREAM price
(
    ticker          VARCHAR,
    bid             DOUBLE,
    ask             DOUBLE
)
WITH (
    kafka_topic='price',
    value_format='json',
    partitions=1
);
"""

CURRENCY_TABLE_DDL = """\
CREATE OR REPLACE TABLE currency_table
(
    ccy             VARCHAR PRIMARY KEY,
    name            VARCHAR,
    minor_unit      INT,
    numeric_code    INT,
    is_legacy       BOOLEAN,
    is_major        BOOLEAN,
    is_ndf          BOOLEAN,
    is_commodity    BOOLEAN,
    is_per_usd      BOOLEAN
)
WITH (
    kafka_topic='currency',
    value_format='json',
    key_format='json',
    partitions=1
);
"""

CURRENCY_QUERYABLE_DDL = """\
CREATE TABLE currency AS
SELECT * FROM currency_table;"""

FX_RATE_STREAM_DDL = """\
CREATE OR REPLACE STREAM fx_rate
(
    ccy             VARCHAR,
    bid             DOUBLE,
    ask             DOUBLE
)
WITH (
    kafka_topic='fx_rate',
    value_format='json',
    partitions=1
);
"""

DDL = {
    'security_table': SECURITY_TABLE_DDL,
    'strategy_table': STRATEGY_TABLE_DDL,
    'trade': TRADE_STREAM_DDL,
    'position_table': POSITION_TABLE_DDL,
    'price': PRICE_STREAM_DDL,
    'currency_table': CURRENCY_TABLE_DDL,
    'currency_queryable': CURRENCY_QUERYABLE_DDL,
    'fx_rate': FX_RATE_STREAM_DDL,
}


async def drop(conn: Connection) -> None:
    async with conn.cursor() as cur:
        for name, sql in DROP.items():
            print(f"{name}: {sql}")
            await cur.execute(sql)

    print("Done")


async def create(conn: Connection) -> None:
    async with conn.cursor() as cur:
        for name, sql in DDL.items():
            print(f"{name}: {sql}")
            await cur.execute(sql)

    print("Done")


def to_sql(value: Any) -> str:
    match value:
        case str():
            return f"'{value}'"
        case int():
            return str(value)
        case float():
            return str(value)
        case Decimal():
            return str(value)
        case bool():
            return 'true' if value else 'false'
        case date():
            return f"'{value}'"
        case datetime():
            return f"'{value}'"
        case None:
            return "NULL"
        case _:
            raise ValueError(f"Unhandled type: {value}")


async def populate(conn: Connection) -> None:
    with open("examples/pnl_data/currencies.json", "r") as f:
        currencies = cast(list[CurrencyDict], json.load(f))

    async with conn.cursor() as cur:
        query = f"""\
INSERT INTO currency_table(
    ccy,
    name,
    minor_unit,
    numeric_code,
    is_legacy,
    is_major,
    is_ndf,
    is_commodity,
    is_per_usd
) VALUES (
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?
);
"""
        seq_params = [
            [
                currency['ccy'],
                currency['name'],
                currency['minor_unit'],
                currency['numeric_code'],
                currency['is_legacy'],
                currency['is_major'],
                currency['is_ndf'],
                currency['is_commodity'],
                currency['is_per_usd']
            ]
            for currency in currencies
        ]
        await cur.executemany(query, seq_params)


async def query(conn: Connection) -> None:
    async with conn.cursor() as cur:
        currency_query = "SELECT * FROM currency;"
        await cur.execute(currency_query)
        async for currency in cur:
            print(currency)


async def main() -> None:
    """Entrypoint"""

    async with connect("http://localhost:8088") as conn:
        # await drop(conn)
        # await create(conn)
        # await populate(conn)
        await query(conn)


if __name__ == "__main__":
    asyncio.run(main())
