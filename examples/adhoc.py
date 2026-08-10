"""Example 1"""

import asyncio

import jetblack_ksql_dbapi as ksql
import jetblack_ksql_dbapi.aio as ksql_async


def main() -> None:

    conn = ksql.connect("http://localhost:8088")

    cur = conn.cursor()

    cur.execute("DESCRIBE user;")
    assert cur.description is not None
    for col in cur.description:
        print(col)
    for row in cur:
        print(row)


async def main_async() -> None:

    conn = ksql_async.connect("http://localhost:8088")

    cur = conn.cursor()

    await cur.execute("DESCRIBE user;")
    assert cur.description is not None
    for col in cur.description:
        print(col)
    async for row in cur:
        print(row)


if __name__ == "__main__":
    main()
    asyncio.run(main_async())
