import asyncio

from jetblack_ksqldb import KsqlDbClient


async def setup(ksqldb: KsqlDbClient) -> None:
    response = await ksqldb.ksql(
        """\
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
);
"""
    )
    print(response)

    response = await ksqldb.ksql(
        """\
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
);
"""
    )
    print(response)

    response = await ksqldb.ksql(
        """\
CREATE OR REPLACE TABLE trade
(
    trade_id        BIGINT PRIMARY KEY,
    version         BIGINT PRIMARY KEY,
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
    )
    print(response)

    response = await ksqldb.ksql(
        """
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
    )
    print(response)

    response = await ksqldb.ksql(
        """
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
    )
    print(response)

    response = await ksqldb.ksql(
        """
CREATE OR REPLACE TABLE currency
(
    ccy             VARCHAR PRIMARY KEY,
    is_per_usd      BOOL
)
WITH (
    kafka_topic='currency',
    value_format='json',
    key_format='json',
    partitions=1
);
"""
    )
    print(response)

    response = await ksqldb.ksql(
        """
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
    )
    print(response)


async def main() -> None:
    """Entrypoint"""

    ksqldb = KsqlDbClient()

    # await setup(ksqldb)

    response = await ksqldb.ksql(
        """\
CREATE TABLE user
(
    user_id BIGINT  PRIMARY KEY,
    username        VARCHAR
) WITH (
    kafka_topic='user',
    value_format='json',
    key_format='json',
    partitions=1
);
"""
    )
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
