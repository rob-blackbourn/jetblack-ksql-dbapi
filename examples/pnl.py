import asyncio

from jetblack_ksqldb import KsqlDbClient

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


async def setup(ksqldb: KsqlDbClient) -> None:
    for name, sql in DDL.items():
        print(f"{name}: {sql}")
        response = await ksqldb.ksql(sql)
        print(response)

    print("Done")


async def main() -> None:
    """Entrypoint"""

    ksqldb = KsqlDbClient()

    await setup(ksqldb)

#     response = await ksqldb.ksql(
#         """\
# CREATE TABLE user
# (
#     user_id BIGINT  PRIMARY KEY,
#     username        VARCHAR
# ) WITH (
#     kafka_topic='user',
#     value_format='json',
#     key_format='json',
#     partitions=1
# );
# """
#     )
#     print(response)

#     response = await ksqldb.ksql(
#         """\
# INSERT INTO user(user_id, username) VALUES (1, 'tom');
# INSERT INTO user(user_id, username) VALUES (2, 'dick');
# INSERT INTO user(user_id, username) VALUES (3, 'harry');
# """
#     )
#     print(response)

#     response = await ksqldb.ksql(
#         """\
# PRINT user FROM BEGINNING;
# """
#     )
#     print(response)


if __name__ == "__main__":
    asyncio.run(main())
