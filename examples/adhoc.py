"""Example 1"""

import asyncio

from jetblack_ksqldb import KsqlDbClient


async def main() -> None:
    """Entrypoint"""

    ksqldb = KsqlDbClient()

    info = await ksqldb.info()
    print(info)

    healthcheck = await ksqldb.healthcheck()
    print(healthcheck)

    streams = await ksqldb.ksql("LIST STREAMS;")
    print(streams)

if __name__ == "__main__":
    asyncio.run(main())
