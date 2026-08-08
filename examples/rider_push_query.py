"""Example 1"""

import asyncio

from jetblack_ksql_dbapi import AsyncKsqlDbClient


async def main() -> None:
    """Entrypoint"""

    ksqldb = AsyncKsqlDbClient()

    props = {
        "auto.offset.reset": "earliest"
    }

    sql = """
-- Mountain View lat, long: 37.4133, -122.1162
SELECT
    *
FROM
    riderLocations
WHERE
    GEO_DISTANCE(latitude, longitude, 37.4133, -122.1162) <= 5
EMIT CHANGES;
"""
    async for row in ksqldb.query_stream(sql, properties=props):
        print("run_query", row)

    print("Done")


if __name__ == "__main__":
    asyncio.run(main())
