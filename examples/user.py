import asyncio

from jetblack_ksqldb import AsyncKsqlDbClient


async def drop_tables(ksqldb: AsyncKsqlDbClient) -> None:
    response = await ksqldb.ksql(
        """\
DROP TABLE IF EXISTS user DELETE TOPIC;
"""
    )
    print(response)

    response = await ksqldb.ksql(
        """\
DROP TABLE IF EXISTS user_view DELETE TOPIC;
"""
    )
    print(response)


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

    response = await ksqldb.ksql(
        """\
CREATE TABLE user_view AS SELECT * FROM user;
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
    async for row in ksqldb.query_stream(
        """\
PRINT user_view FROM BEGINNING;
"""
    ):
        print(row)


async def select_all(ksqldb: AsyncKsqlDbClient) -> None:
    async for row in ksqldb.query(
        """\
SELECT * FROM user_view;
"""
    ):
        print(row)


async def main() -> None:
    """Entrypoint"""

    ksqldb = AsyncKsqlDbClient()

    # await drop_tables(ksqldb)
    # await create_tables(ksqldb)
    # await insert_data(ksqldb)
    # await print_data(ksqldb)
    await select_all(ksqldb)


if __name__ == "__main__":
    asyncio.run(main())
