"""Example 1"""

import asyncio

from jetblack_ksqldb import AsyncKsqlDbClient


async def run_query(ksqldb: AsyncKsqlDbClient) -> None:
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
    async for row in ksqldb.query_stream(sql):
        print("run_query", row)
        # {
        #   'queryId': 'transient_RIDERLOCATIONS_6772440454185557945',
        #   'columnNames': ['PROFILEID', 'LATITUDE', 'LONGITUDE'],
        #   'columnTypes': ['STRING', 'DOUBLE', 'DOUBLE']
        # }
        #
        # ['4ab5cbad', 37.3952, -122.0813]
        # ['8b6eae59', 37.3944, -122.0813]
        # ['4a7c7b41', 37.4049, -122.0822]


async def setup(ksqldb: AsyncKsqlDbClient) -> None:
    response = await ksqldb.ksql(
        """DROP TABLE IF EXISTS ridersNearMountainView;"""
    )
    response = await ksqldb.ksql(
        """DROP TABLE IF EXISTS currentLocation;"""
    )
    response = await ksqldb.ksql(
        """DROP STREAM IF EXISTS riderLocations;"""
    )

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
    print("create stream", response)
    # [
    #   {
    #     '@type': 'currentStatus',
    #     'statementText': "CREATE STREAM RIDERLOCATIONS (PROFILEID STRING, LATITUDE DOUBLE, LONGITUDE DOUBLE) WITH (CLEANUP_POLICY='delete', KAFKA_TOPIC='locations', KEY_FORMAT='KAFKA', PARTITIONS=1, VALUE_FORMAT='JSON');",
    #     'commandId': 'stream/`RIDERLOCATIONS`/create',
    #     'commandStatus': {
    #       'status': 'SUCCESS',
    #       'message': 'Stream created',
    #       'queryId': None
    #     },
    #     'commandSequenceNumber': 2,
    #     'warnings': []
    #   }
    # ]

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
    print("create table 1", response)
    # [
    #   {
    #     '@type': 'currentStatus',
    #     'statementText': "CREATE TABLE CURRENTLOCATION WITH (CLEANUP_POLICY='compact', KAFKA_TOPIC='CURRENTLOCATION', PARTITIONS=1, REPLICAS=1, RETENTION_MS=604800000) AS SELECT\n  RIDERLOCATIONS.PROFILEID PROFILEID,\n  LATEST_BY_OFFSET(RIDERLOCATIONS.LATITUDE) LA,\n  LATEST_BY_OFFSET(RIDERLOCATIONS.LONGITUDE) LO\nFROM RIDERLOCATIONS RIDERLOCATIONS\nGROUP BY RIDERLOCATIONS.PROFILEID\nEMIT CHANGES;",
    #     'commandId': 'table/`CURRENTLOCATION`/create',
    #     'commandStatus': {
    #       'status': 'SUCCESS',
    #       'message': 'Created query with ID CTAS_CURRENTLOCATION_3',
    #       'queryId': 'CTAS_CURRENTLOCATION_3'
    #     },
    #     'commandSequenceNumber': 4,
    #     'warnings': []
    #   }
    # ]

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
    # [
    #   {
    #     '@type': 'currentStatus',
    #     'statementText': "CREATE TABLE RIDERSNEARMOUNTAINVIEW WITH (CLEANUP_POLICY='compact', KAFKA_TOPIC='RIDERSNEARMOUNTAINVIEW', PARTITIONS=1, REPLICAS=1, RETENTION_MS=604800000) AS SELECT\n  ROUND(GEO_DISTANCE(CURRENTLOCATION.LA, CURRENTLOCATION.LO, 37.4133, -122.1162), -1) DISTANCEINMILES,\n  COLLECT_LIST(CURRENTLOCATION.PROFILEID) RIDERS,\n  COUNT(*) COUNT\nFROM CURRENTLOCATION CURRENTLOCATION\nGROUP BY ROUND(GEO_DISTANCE(CURRENTLOCATION.LA, CURRENTLOCATION.LO, 37.4133, -122.1162), -1)\nEMIT CHANGES;",
    #     'commandId': 'table/`RIDERSNEARMOUNTAINVIEW`/create',
    #     'commandStatus': {
    #       'status': 'SUCCESS',
    #       'message': 'Created query with ID CTAS_RIDERSNEARMOUNTAINVIEW_5',
    #       'queryId': 'CTAS_RIDERSNEARMOUNTAINVIEW_5'
    #     },
    #     'commandSequenceNumber': 6,
    #     'warnings': []
    #   }
    # ]


async def main() -> None:
    """Entrypoint"""

    ksqldb = AsyncKsqlDbClient()

    await setup(ksqldb)

    query_task = asyncio.create_task(run_query(ksqldb))

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
            # {'seq': 0, 'status': 'ok'}
            # {'seq': 0, 'status': 'ok'}
            # {'seq': 0, 'status': 'ok'}
            # {'seq': 0, 'status': 'ok'}
            # {'seq': 0, 'status': 'ok'}
            # {'seq': 0, 'status': 'ok'}

        await asyncio.sleep(1)

    await asyncio.sleep(1)

    query_task.cancel()
    try:
        await query_task
    except asyncio.CancelledError:
        pass

    await ksqldb.close()

    print("Done")


if __name__ == "__main__":
    asyncio.run(main())
