import asyncio

from jetblack_ksqldb import AsyncKsqlDbClient


async def create_tables(ksqldb: AsyncKsqlDbClient) -> None:
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


async def insert_data(ksqldb: AsyncKsqlDbClient) -> None:

    response = await ksqldb.ksql(
        """\
INSERT INTO user(user_id, username) VALUES (1, 'tom');
INSERT INTO user(user_id, username) VALUES (2, 'dick');
INSERT INTO user(user_id, username) VALUES (3, 'harry');
"""
    )
    print(response)


async def print_data(ksqldb: AsyncKsqlDbClient) -> None:
    response = await ksqldb.ksql(
        """\
PRINT user FROM BEGINNING;
"""
    )
    print(response)


async def select_all(ksqldb: AsyncKsqlDbClient) -> None:
    async for row in ksqldb.query_stream(
        """\
SELECT * FROM user;
"""
    ):
        print(row)


async def main() -> None:
    """Entrypoint"""

    ksqldb = AsyncKsqlDbClient()

    # await create_tables(ksqldb)
    # await insert_data(ksqldb)
    # await print_data(ksqldb)
    await select_all(ksqldb)


if __name__ == "__main__":
    asyncio.run(main())
