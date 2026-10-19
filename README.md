# Pagila SQL Quiz

**Author:** Gaston Grant

**Quiz site:** https://sql-quiz-lvk9tnmy9n2cj72fwtc6zd.streamlit.app

**Repository:** https://github.com/gastonrgrant/sql-quiz

## How to use the quiz

1. Open the quiz site.
2. Select **Create account**, enter your email, and choose a password.
3. Sign in with your quiz account.
4. Choose a question and enter PostgreSQL in the SQL editor.
5. Click **Run SQL** to see results from the hosted database.
6. Click **Save answer** to store your answer.
7. Expand the hint to view the expected SQL. Click **Show expected result**
   to display its result table.

No database password is needed to take the quiz. Signed-out users cannot
run queries or save answers. Saved answers are associated with the
authenticated user's ID and load when that user signs in again.

Answers are assessed by comparing result sets with the expected results,
rather than requiring identical SQL text. The app does not automatically
assign grades.

## Quiz: 20 points

| Question | Topic | Points |
|---|---|---:|
| 1 | Filter PG-13 films and return the first 10 by film ID | 4 |
| 2 | Join tables to find films featuring Penelope Guiness | 4 |
| 3 | Group and count films by category | 4 |
| 4 | Sum payments to find the top-spending customers | 4 |
| 5 | Use a CTE and ROW_NUMBER to find each customer's largest payment | 4 |
| **Total** | | **20** |

Each question includes a prompt, hint, expected SQL, and a button to
display the expected result from the database.

## System

- **Frontend and Python backend:** Streamlit Community Cloud.
- **Hosted PostgreSQL and authentication:** Supabase.
- **Database connection:** psycopg2 through the Supabase Session pooler,
  port 5432, with `sslmode=require`.
- **Automation:** GitHub Actions runs `check_db.py` on pushes to `main`
  and can also be started manually.

Supabase Auth verifies the user's token before query execution and
answer storage. Student SQL runs as `quiz_reader` in a read-only
transaction. SQL validation permits a single SELECT statement, including
CTEs, against allowed Pagila tables. Queries have a five-second timeout
and a 1,000-row result limit.

Saved answers are stored in `quiz_private.answers`. The student query
role has no access to that schema. Saving and loading answers use
parameterized SQL, with the user ID obtained from Supabase Auth.

## Dataset

Source: https://github.com/devrimgunduz/pagila/tree/pagila-v3.0.0

Pagila is an existing sample DVD rental database. This project uses
release `pagila-v3.0.0`, loaded into the separate `pagila` schema.

The imported data includes:

- 1,000 films
- 200 actors
- 599 customers
- 16,044 rentals
- 16,049 payments

The source SQL files are `pagila-schema.sql` and `pagila-data.sql`.
`load_pagila.py` adapts their schema references and imports them.
Pagila is distributed under the PostgreSQL License; see its source
repository for license details.

## Local setup

Use Python 3.12.

```bash
git clone https://github.com/gastonrgrant/sql-quiz.git
cd sql-quiz
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a Supabase project. Enable email sign-up and email/password login.
For this class demo, email confirmation is disabled so a new user can
register and sign in immediately.

Create a local `.env` with your own project's settings:

```dotenv
POSTGRES_DB=postgres
POSTGRES_USER=postgres.YOUR_PROJECT_REF
POSTGRES_PASSWORD="YOUR_DATABASE_PASSWORD"
DB_HOST=YOUR_SESSION_POOLER_HOST
DB_PORT=5432
DB_SSLMODE=require
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_KEY="YOUR_PUBLISHABLE_KEY"
```

Keep `.env` out of git; it is listed in `.gitignore`.

In the Supabase SQL Editor, create the student role:

```sql
CREATE ROLE quiz_reader NOLOGIN;
GRANT quiz_reader TO postgres;
```

Run the contents of `quiz_setup.sql` in the SQL Editor to create the
private answer table and restrict access.

Import the dataset once into a project without a `pagila` schema:

```bash
python load_pagila.py
```

The loader also grants the student role read access to Pagila.
Do not rerun the import against an already imported schema.

Start the app:

```bash
streamlit run app.py
```

## GitHub Actions and Secrets

In the repository, open **Settings → Secrets and variables → Actions**.
Create a repository secret named `POSTGRES_PASSWORD` containing the
database password without surrounding quotes.

The workflow `.github/workflows/check-db.yml` reads that secret through
`${{ secrets.POSTGRES_PASSWORD }}`. The password is not written into
the workflow.

For another Supabase project, update the workflow's nonsecret host and
username settings.

The check connects to hosted Postgres, runs all five expected answer
queries as `quiz_reader`, checks that they return rows, verifies that
the quiz totals 20 points, and checks that the student role cannot
access the private answer schema.

View runs here: https://github.com/gastonrgrant/sql-quiz/actions

Run the same check locally with:

```bash
python check_db.py
```

## Deployment

Deploy `app.py` from the repository's `main` branch on Streamlit Community
Cloud using Python 3.12.

In Streamlit's Secrets settings, enter the same configuration keys as
`.env`, using TOML syntax with quoted string values. Database credentials
stay in Streamlit Secrets and GitHub Secrets, rather than source code.

## Files

| File | Purpose |
|---|---|
| `app.py` | Registration, sign-in, questions, SQL editor, results, and saving |
| `database.py` | Auth verification, query validation, database access, answer storage |
| `quiz.py` | Five questions and expected SQL |
| `quiz_setup.sql` | Private answer table and access restrictions |
| `load_pagila.py` | Dataset import and student read permissions |
| `pagila-schema.sql` | Upstream dataset schema |
| `pagila-data.sql` | Upstream dataset rows |
| `check_db.py` | Live database and quiz checks |
| `.github/workflows/check-db.yml` | GitHub Actions workflow |

## Extra credit scope

Answer saving and loading use parameterized SQL. Student SQL is parsed
and restricted before execution. An audit log is not implemented.