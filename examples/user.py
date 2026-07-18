import asyncio

from jetblack_ksqldb import KsqlDbClient


async def create_tables(ksqldb: KsqlDbClient) -> None:
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


async def insert_data(ksqldb: KsqlDbClient) -> None:

    response = await ksqldb.ksql(
        """\
INSERT INTO user(user_id, username) VALUES (1, 'tom');
INSERT INTO user(user_id, username) VALUES (2, 'dick');
INSERT INTO user(user_id, username) VALUES (3, 'harry');
"""
    )
    print(response)


async def print_data(ksqldb: KsqlDbClient) -> None:
    response = await ksqldb.ksql(
        """\
PRINT user FROM BEGINNING;
"""
    )
    print(response)


async def main() -> None:
    """Entrypoint"""

    ksqldb = KsqlDbClient()

    await create_tables(ksqldb)
    await insert_data(ksqldb)
    await print_data(ksqldb)


if __name__ == "__main__":
    asyncio.run(main())
