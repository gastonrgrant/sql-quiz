from contextlib import closing

import pandas as pd
import psycopg2
import sqlglot
from sqlglot import exp


def connect(setting):
    return psycopg2.connect(
        dbname=setting("POSTGRES_DB"),
        user=setting("POSTGRES_USER"),
        password=setting("POSTGRES_PASSWORD"),
        host=setting("DB_HOST"),
        port=setting("DB_PORT"),
        sslmode="require",
        connect_timeout=15,
    )


def verify_user(client, token):
    user = client.auth.get_user(token).user
    if user is None:
        raise ValueError("Sign in before running or saving answers.")
    return user


def validate_query(query):
    statements = sqlglot.parse(query, read="postgres")

    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise ValueError("Enter one SELECT query. CTEs are allowed.")

    tree = statements[0]

    blocked = {
        "insert", "update", "delete", "create", "drop", "alter",
        "command", "transaction", "commit", "rollback",
        "into", "lock", "copy", "grant", "revoke", "set",
    }

    for node in tree.walk():
        if node.key in blocked:
            raise ValueError("Only read-only SELECT queries are allowed.")

    # Allow the SQL functions needed for this quiz.
    allowed_functions = {
        "COUNT", "SUM", "AVG", "MIN", "MAX",
        "ROW_NUMBER", "RANK", "DENSE_RANK",
        "ROUND", "LOWER", "UPPER", "AND", "OR",
    }

    for function in tree.find_all(exp.Func):
        if function.sql_name().upper() not in allowed_functions:
            raise ValueError(
                "Use aggregate, ranking, rounding, or text-case functions."
            )

    # Block schema-qualified function calls.
    if any(tree.find_all(exp.Dot)):
        raise ValueError("Schema-qualified functions are not allowed.")

    allowed_tables = {
        "film", "actor", "film_actor", "category", "film_category",
        "customer", "payment", "rental", "inventory",
        "store", "staff", "address", "city", "country", "language",
    }
    cte_names = {
        cte.alias_or_name.lower()
        for cte in tree.find_all(exp.CTE)
    }

    for table in tree.find_all(exp.Table):
        name = table.name.lower()
        schema = table.db.lower()

        if table.catalog:
            raise ValueError("Cross-database queries are not allowed.")

        if schema:
            if schema != "pagila" or name not in allowed_tables:
                raise ValueError("Query tables in the pagila schema.")
        elif name not in allowed_tables | cte_names:
            raise ValueError("Query Pagila tables or your own CTEs.")

    return tree.sql(dialect="postgres")


def run_query(setting, client, token, query):
    verify_user(client, token)
    clean_query = validate_query(query)

    with closing(connect(setting)) as conn:
        conn.set_session(readonly=True)

        with conn:
            with conn.cursor() as cur:
                cur.execute("SET LOCAL ROLE quiz_reader")
                cur.execute("SET LOCAL search_path = pg_catalog, pagila")
                cur.execute("SET LOCAL statement_timeout = '5s'")
                cur.execute(clean_query)

                rows = cur.fetchmany(1001)
                columns = [column[0] for column in cur.description]

    if len(rows) > 1000:
        raise ValueError("Result exceeds 1,000 rows. Add a LIMIT.")

    return pd.DataFrame(rows, columns=columns)


def save_answer(setting, client, token, question_id, answer):
    user = verify_user(client, token)

    if question_id not in range(1, 6):
        raise ValueError("Invalid question.")

    if not answer.strip() or len(answer) > 20000:
        raise ValueError("Enter an answer under 20,000 characters.")

    with closing(connect(setting)) as conn:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO quiz_private.answers
                        (user_id, question_id, sql_answer)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, question_id)
                    DO UPDATE SET
                        sql_answer = EXCLUDED.sql_answer,
                        saved_at = NOW()
                    """,
                    (str(user.id), question_id, answer),
                )


def load_answers(setting, client, token):
    user = verify_user(client, token)

    with closing(connect(setting)) as conn:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT question_id, sql_answer
                    FROM quiz_private.answers
                    WHERE user_id = %s
                    """,
                    (str(user.id),),
                )
                return dict(cur.fetchall())