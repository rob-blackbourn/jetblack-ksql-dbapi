import asyncio

import jetblack_ksqldb.dbapi as ksql
from jetblack_ksqldb.dbapi import Connection


def drop_tables(conn: Connection) -> None:

    cur = conn.cursor()

    cur.execute(
        """\
DROP TABLE IF EXISTS user_view DELETE TOPIC;
"""
    )

    cur.execute(
        """\
DROP TABLE IF EXISTS user DELETE TOPIC;
"""
    )


def create_tables(conn: Connection) -> None:
    cur = conn.cursor()

    cur.execute(
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

    cur.execute(
        """\
CREATE TABLE user_view AS SELECT * FROM user;
"""
    )


def insert_data(conn: Connection) -> None:
    cur = conn.cursor()

    cur.executemany(
        """\
INSERT INTO user(user_id, username, created, age) VALUES (?, ?, ?, ?);
""",
        (
            (1, 'tom', '2026-07-28T12:03:24', 42),
            (2, 'dick', '2026-07-28T12:03:24', 42),
            (3, 'harry', '2026-07-28T12:03:24', 42)
        )
    )


def print_data(conn: Connection) -> None:
    cur = conn.cursor()

    cur.execute(
        """\
PRINT user FROM BEGINNING;
"""
    )

    for row in cur:
        print(row)


def select_all(conn: Connection) -> None:
    cur = conn.cursor()

    cur.execute(
        """\
SELECT * FROM user_view;
"""
    )

    for row in cur.fetchall():
        print(row)


def main() -> None:
    """Entrypoint"""

    ksql.paramstyle = 'qmark'
    conn = ksql.connect()

    drop_tables(conn)
    create_tables(conn)
    insert_data(conn)
    # print_data(conn)
    # select_all(conn)

    # cur = conn.cursor()
    # cur.execute("DESCRIBE user;")


if __name__ == "__main__":
    main()
