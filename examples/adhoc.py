"""Example 1"""

import asyncio

import jetblack_ksql_dbapi as ksql
import jetblack_ksql_dbapi.aio as ksql_async


def main() -> None:

    conn = ksql.connect("http://localhost:8088")

    cur = conn.cursor()

    cur.execute("SHOW TABLES;")
    for row in cur:
        print(row)


async def main_async() -> None:

    conn = ksql_async.connect("http://localhost:8088")

    cur = conn.cursor()

    await cur.execute("SHOW TABLES;")
    async for row in cur:
        print(row)


if __name__ == "__main__":
    main()
    asyncio.run(main_async())
