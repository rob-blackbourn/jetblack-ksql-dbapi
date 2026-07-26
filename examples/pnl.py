import asyncio
import json
from typing import TypedDict

from jetblack_ksqldb import AsyncKsqlDbClient


class CurrencyDict(TypedDict):
    ccy: str
    name: str
    minor_unit: int
    major_unit: int
    numeric_code: int
    is_legacy: bool
    is_major: bool
    is_ndf: bool
    is_commodity: bool
    is_per_usd: bool


SECURITY_TABLE_DDL = """\
CREATE OR REPLACE TABLE security
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
CREATE OR REPLACE TABLE strategy
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
CREATE OR REPLACE TABLE position
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
CREATE OR REPLACE TABLE currency
(
    ccy             VARCHAR PRIMARY KEY,
    name            VARCHAR,
    minor_unit      INT,
    major_unit      INT,
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
    'security': SECURITY_TABLE_DDL,
    'strategy': STRATEGY_TABLE_DDL,
    'trade': TRADE_STREAM_DDL,
    'position': POSITION_TABLE_DDL,
    'price': PRICE_STREAM_DDL,
    'currency': CURRENCY_TABLE_DDL,
    'fx_rate': FX_RATE_STREAM_DDL,
}


async def setup(ksqldb: AsyncKsqlDbClient) -> None:
    for name, sql in DDL.items():
        print(f"{name}: {sql}")
        response = await ksqldb.ksql(sql)
        print(response)

    print("Done")


async def populate(ksqldb: AsyncKsqlDbClient) -> None:
    with open("examples/currencies.json", "r") as f:
        currencies = json.load(f)

    for currency in currencies:
        response = await ksqldb.ksql(
            f"INSERT INTO currency(ccy, name, minor_unit, major_unit, numeric_code, is_legacy, is_major, is_ndf, is_commodity) "
            "VALUES ('{currency['ccy']}', {str(currency['is_per_usd']).lower()});"
        )
        print(response)


async def main() -> None:
    """Entrypoint"""

    ksqldb = AsyncKsqlDbClient()

    await setup(ksqldb)
    await populate(ksqldb)


if __name__ == "__main__":
    asyncio.run(main())
