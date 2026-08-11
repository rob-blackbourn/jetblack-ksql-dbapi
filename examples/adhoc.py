"""Example 1"""

import asyncio

import jetblack_ksql_dbapi as ksql
import jetblack_ksql_dbapi.aio as ksql_async


def main() -> None:

    with ksql.connect("http://localhost:8088") as conn:

        with conn.cursor() as cur:

            cur.execute("""\
CREATE OR REPLACE TABLE currency_test
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
    kafka_topic='currency_test',
    value_format='json',
    key_format='json',
    partitions=1
);
""")

            cur.execute("DESCRIBE currency_test;")
            assert cur.description is not None
            for col in cur.description:
                print(col)
            for row in cur:
                print(row)


async def main_async() -> None:

    async with ksql_async.connect("http://localhost:8088") as conn:

        async with conn.cursor() as cur:

            await cur.execute("""\
CREATE OR REPLACE TABLE currency_test
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
    kafka_topic='currency_test',
    value_format='json',
    key_format='json',
    partitions=1
);
""")

            await cur.execute("DESCRIBE currency_test;")
            assert cur.description is not None
            for col in cur.description:
                print(col)
            async for row in cur:
                print(row)


if __name__ == "__main__":
    main()
    asyncio.run(main_async())
