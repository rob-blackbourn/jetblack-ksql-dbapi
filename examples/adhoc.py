"""Example 1"""

import jetblack_ksql_dbapi as ksql


def main() -> None:

    conn = ksql.connect("http://localhost:8088")

    cur = conn.cursor()

    cur.execute("DROP TABLE foo;")


if __name__ == "__main__":
    main()
