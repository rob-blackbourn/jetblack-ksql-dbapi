"""Example 1"""

import asyncio

from jetblack_ksql_dbapi import AsyncKsqlDbClient


async def main() -> None:
    """Entrypoint"""

    ksqldb = AsyncKsqlDbClient()

    info = await ksqldb.info()
    print(info)

    healthcheck = await ksqldb.healthcheck()
    print(healthcheck)

    streams = await ksqldb.ksql("LIST STREAMS;")
    print(streams)

if __name__ == "__main__":
    asyncio.run(main())
