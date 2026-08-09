# jetblack-ksql-dbapi

A vanilla and asyncio [ksql](https://www.confluent.io/product/ksqldb/)
[DBAPI](https://peps.python.org/pep-0249/) interface for Python >= 3.12.

## Status

This is work in progress.

## Installation

The package uses either httpx or httpx2. This can either
be installed separately or specified as an extra.

```bash
pip install jetblack-ksql-dbapi[httpx2]
```

## Usage

In the source repo there is a docker compose file in the scripts folder which will bring
up a local instance of ksql.

Here is an example using the async client connecting to a local instance of ksql.

```python
import asyncio

from jetblack_ksql_dbapi.aio import connect


async def main() -> None:

    conn = connect("http://localhost:8088")

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

    await cur.execute("SELECT * FROM user_view;")
    async for row in cur:
        print(row)


if __name__ == "__main__":
    asyncio.run(main())
```

## Things to do

* Figure out what to do with the `paramstyle` global.
* How to handle timeouts.
* Do something useful with the output of commands like `SHOW TABLES;`
* Handle multiple commands.
* Tidy up cursors with multiple executions.
* rowcount can be supported if we detect pull/push quueries.
