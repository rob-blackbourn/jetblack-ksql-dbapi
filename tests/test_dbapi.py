from jetblack_ksqldb._dbapi import clean_query


def test_clean_query() -> None:
    query = """\
-- table with declared columns:
CREATE TABLE users (
     id BIGINT PRIMARY KEY,
     usertimestamp BIGINT,
     gender VARCHAR, /* a comment */
     region_id VARCHAR -- another comment
   ) WITH (
     KAFKA_TOPIC = 'my-users-topic',
     VALUE_FORMAT = 'JSON'
   );
"""
    cleaned = clean_query(query)
    assert cleaned
