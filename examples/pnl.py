import asyncio
from datetime import date, datetime
from decimal import Decimal
import json
from typing import Any, TypedDict, cast

from jetblack_ksqldb import AsyncKsqlDbClient


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


async def setup(ksqldb: AsyncKsqlDbClient) -> None:
    for name, sql in DDL.items():
        print(f"{name}: {sql}")
        response = await ksqldb.ksql(sql)
        print(response)

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


async def populate(ksqldb: AsyncKsqlDbClient) -> None:
    with open("examples/pnl_data/currencies.json", "r") as f:
        currencies = cast(list[CurrencyDict], json.load(f))

    for currency in currencies:
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
    {to_sql(currency['ccy'])},
    {to_sql(currency['name'])},
    {to_sql(currency['minor_unit'])},
    {to_sql(currency['numeric_code'])},
    {to_sql(currency['is_legacy'])},
    {to_sql(currency['is_major'])},
    {to_sql(currency['is_ndf'])},
    {to_sql(currency['is_commodity'])},
    {to_sql(currency['is_per_usd'])}
);
"""
        response = await ksqldb.ksql(query)
        print(response)


async def query(ksqldb: AsyncKsqlDbClient) -> None:
    currency_query = "SELECT * FROM currency;"
    async for currency in ksqldb.query(currency_query):
        print(currency)


async def main() -> None:
    """Entrypoint"""

    ksqldb = AsyncKsqlDbClient()

    # await setup(ksqldb)
    # await populate(ksqldb)
    await query(ksqldb)


if __name__ == "__main__":
    asyncio.run(main())
