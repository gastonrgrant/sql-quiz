import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

load_dotenv(".env")


def prepare_sql(filename):
    sql = Path(filename).read_text(encoding="utf-8")

    # Load into a separate schema instead of public.
    sql = sql.replace("public.", "pagila.")
    sql = sql.replace(
        "ALTER SCHEMA public OWNER TO postgres;",
        "ALTER SCHEMA pagila OWNER TO postgres;",
    )
    sql = sql.replace(
        "set_config('search_path', '', false)",
        "set_config('search_path', 'pagila, pg_catalog', false)",
    )
    return sql


conn = psycopg2.connect(
    dbname=os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    host=os.environ["DB_HOST"],
    port=os.environ["DB_PORT"],
    sslmode="require",
    connect_timeout=15,
)

try:
    with conn:
        with conn.cursor() as cur:
            cur.execute("CREATE SCHEMA pagila;")

            print("Creating Pagila tables...", flush=True)
            cur.execute(prepare_sql("pagila-schema.sql"))

            print("Loading Pagila data...", flush=True)
            cur.execute(prepare_sql("pagila-data.sql"))

            cur.execute("""
                GRANT USAGE ON SCHEMA pagila TO quiz_reader;
                GRANT SELECT ON ALL TABLES IN SCHEMA pagila
                TO quiz_reader;
            """)

            cur.execute("""
                SELECT 'films', COUNT(*) FROM pagila.film
                UNION ALL
                SELECT 'actors', COUNT(*) FROM pagila.actor
                UNION ALL
                SELECT 'customers', COUNT(*) FROM pagila.customer
                UNION ALL
                SELECT 'rentals', COUNT(*) FROM pagila.rental
                UNION ALL
                SELECT 'payments', COUNT(*) FROM pagila.payment;
            """)

            for table, count in cur.fetchall():
                print(f"{table}: {count}")

    print("Pagila imported successfully.")

finally:
    conn.close()