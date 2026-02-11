"""Example 1"""

import asyncio

from jetblack_ksqldb import KsqlDbClient


async def run_query(ksqldb: KsqlDbClient) -> None:
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
    async for row in ksqldb.query(sql, timeout=5.0):
        print(row)


async def setup(ksqldb: KsqlDbClient) -> None:
    response = await ksqldb.ksql(
        """
CREATE STREAM riderLocations
(
    profileId VARCHAR,
    latitude  DOUBLE,
    longitude DOUBLE
)
WITH (
    kafka_topic='locations',
    value_format='json',
    partitions=1
);
"""
    )
    print(response)

    response = await ksqldb.ksql(
        """
-- Create the currentLocation table
CREATE TABLE currentLocation
AS
    SELECT profileId,
        LATEST_BY_OFFSET(latitude) AS la,
        LATEST_BY_OFFSET(longitude) AS lo
    FROM
        riderlocations
    GROUP BY
        profileId
    EMIT CHANGES;
"""
    )
    print(response)

    response = await ksqldb.ksql(
        """
-- Create the ridersNearMountainView table
CREATE TABLE ridersNearMountainView
AS
    SELECT
        ROUND(GEO_DISTANCE(la, lo, 37.4133, -122.1162), -1) AS distanceInMiles,
        COLLECT_LIST(profileId) AS riders,
        COUNT(*) AS count
    FROM
        currentLocation
    GROUP BY
        ROUND(GEO_DISTANCE(la, lo, 37.4133, -122.1162), -1);
 """
    )
    print(response)


async def main() -> None:
    """Entrypoint"""

    ksqldb = KsqlDbClient()

    # await setup(ksqldb)

    asyncio.create_task(run_query(ksqldb))

    stream_name = "riderLocations"
    rows = [
        {'profileId': 'c2309eec', 'latitude': 37.7877, 'longitude': -122.4205},
        {'profileId': '18f4ea86', 'latitude': 37.3903, 'longitude': -122.0643},
        {'profileId': '4ab5cbad', 'latitude': 37.3952, 'longitude': -122.0813},
        {'profileId': '8b6eae59', 'latitude': 37.3944, 'longitude': -122.0813},
        {'profileId': '4a7c7b41', 'latitude': 37.4049, 'longitude': -122.0822},
        {'profileId': '4ddad000', 'latitude': 37.7857, 'longitude': -122.4011},
    ]
    for row in rows:

        async for result in ksqldb.inserts_stream(stream_name, [row]):
            print(result)

        await asyncio.sleep(1)

    await asyncio.sleep(60)

    print("Done")


if __name__ == "__main__":
    asyncio.run(main())
