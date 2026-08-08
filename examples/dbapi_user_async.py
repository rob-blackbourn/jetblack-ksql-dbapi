import asyncio

import jetblack_ksql_dbapi.aio as ksql
from jetblack_ksql_dbapi.aio import Connection


async def drop_tables(conn: Connection) -> None:

    cur = conn.cursor()

    await cur.execute(
        """\
DROP TABLE IF EXISTS user_view DELETE TOPIC;
"""
    )

    await cur.execute(
        """\
DROP TABLE IF EXISTS user DELETE TOPIC;
"""
    )


async def create_tables(conn: Connection) -> None:
    cur = conn.cursor()

    await cur.execute(
        """\
CREATE TABLE user
(
    user_id BIGINT  PRIMARY KEY,
    username        STRING,
    created         TIMESTAMP,
    age             DECIMAL(3, 0)
) WITH (
    kafka_topic='user',
    value_format='json',
    key_format='json',
    partitions=1
);
"""
    )

    await cur.execute(
        """\
CREATE TABLE user_view AS SELECT * FROM user;
"""
    )


async def insert_data(conn: Connection) -> None:
    cur = conn.cursor()

    await cur.executemany(
        """\
INSERT INTO user(user_id, username, created, age) VALUES (?, ?, ?, ?);
""",
        (
            (1, 'tom', '2026-07-28T12:03:24', 42),
            (2, 'dick', '2026-07-28T12:03:24', 42),
            (3, 'harry', '2026-07-28T12:03:24', 42)
        )
    )


async def print_data(conn: Connection) -> None:
    cur = conn.cursor()

    await cur.execute(
        """\
PRINT user FROM BEGINNING;
"""
    )

    async for row in cur:
        print(row)


async def select_all(conn: Connection) -> None:
    cur = conn.cursor()

    await cur.execute(
        """\
SELECT * FROM user_view;
"""
    )

    for row in await cur.fetchall():
        print(row)


async def main() -> None:
    """Entrypoint"""

    conn = ksql.connect("http://localhost:8088")

    await drop_tables(conn)
    await create_tables(conn)
    await insert_data(conn)
    # await print_data(conn)
    await select_all(conn)

    # cur = conn.cursor()
    # cur.execute("DESCRIBE user;")


if __name__ == "__main__":
    asyncio.run(main())
