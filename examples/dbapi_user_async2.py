import asyncio

import jetblack_ksql_dbapi.aio as ksql
from jetblack_ksql_dbapi.aio import KsqlAsyncConnection


async def main() -> None:
    """Entrypoint"""

    conn = ksql.connect("http://localhost:8088")

    cur = conn.cursor()

    # Drop the tables if they exist.
    await cur.execute(
        "DROP TABLE IF EXISTS user_view DELETE TOPIC;"
    )
    await cur.execute(
        "DROP TABLE IF EXISTS user DELETE TOPIC;"
    )

    # Create the tables.
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

    # Insert some data.
    await cur.executemany(
        """\
INSERT INTO user(user_id, username, created, age)
VALUES (?, ?, ?, ?);
""",
        (
            (1, 'tom', '2026-07-28T12:03:24', 42),
            (2, 'dick', '2026-07-28T12:03:24', 42),
            (3, 'harry', '2026-07-28T12:03:24', 42)
        )
    )

    await cur.execute(
        "SELECT * FROM user_view;"
    )
    async for row in cur:
        print(row)


if __name__ == "__main__":
    asyncio.run(main())
