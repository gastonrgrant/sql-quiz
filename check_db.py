import os
from contextlib import closing

from dotenv import load_dotenv

from database import connect, validate_query
from quiz import QUESTIONS

load_dotenv()

assert len(QUESTIONS) == 5
assert sum(q["points"] for q in QUESTIONS) == 20

with closing(connect(os.environ.__getitem__)) as conn:
    conn.set_session(readonly=True)

    with conn:
        with conn.cursor() as cur:
            cur.execute("SET LOCAL ROLE quiz_reader")
            cur.execute("SET LOCAL search_path = pg_catalog, pagila")
            cur.execute("SET LOCAL statement_timeout = '10s'")

            for question in QUESTIONS:
                sql = validate_query(question["expected_sql"])
                cur.execute(sql)
                rows = cur.fetchall()

                assert rows, f"Question {question['id']} returned no rows"
                print(
                    f"Question {question['id']}: "
                    f"passed, {len(rows)} rows"
                )

            cur.execute("""
                SELECT has_schema_privilege(
                    current_user, 'quiz_private', 'USAGE'
                )
            """)
            assert not cur.fetchone()[0]
            print("Student role cannot access saved answers.")

print("Database checks passed. Quiz total: 20 points.")