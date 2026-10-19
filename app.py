import os

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

from database import load_answers, run_query, save_answer
from quiz import QUESTIONS

load_dotenv()

st.set_page_config(page_title="Pagila SQL Quiz", layout="wide")


def setting(name):
    value = os.getenv(name)
    if value:
        return value
    return st.secrets[name]


# Keep each browser session's authentication separate.
if "supabase" not in st.session_state:
    st.session_state.supabase = create_client(
        setting("SUPABASE_URL"),
        setting("SUPABASE_KEY"),
    )

supabase = st.session_state.supabase

st.title("Pagila SQL Quiz")
st.caption("5 SQL questions • 4 points each • 20 points total")

# Signed-out users cannot access the query or save controls.
if "access_token" not in st.session_state:
    st.info("Create an account, then sign in to run SQL and save answers.")

    login_tab, signup_tab = st.tabs(["Sign in", "Create account"])

    with login_tab:
        with st.form("login"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in")

        if submitted:
            try:
                response = supabase.auth.sign_in_with_password(
                    {
                        "email": email.strip(),
                        "password": password,
                    }
                )

                if response.session:
                    st.session_state.access_token = (
                        response.session.access_token
                    )
                    st.rerun()
                else:
                    st.error("Sign-in did not return a session.")

            except Exception:
                st.error(
                    "Sign-in failed. Create an account first if you "
                    "haven't registered, then use that account's password."
                )

    with signup_tab:
        st.write(
            "Choose a new password for this quiz account. "
            "You do not need your database or email account password."
        )

        with st.form("signup"):
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input(
                "Choose a password (at least 8 characters)",
                type="password",
                key="signup_password",
            )
            registered = st.form_submit_button("Create account")

        if registered:
            if len(new_password) < 8:
                st.error("Use a password with at least 8 characters.")
            else:
                try:
                    supabase.auth.sign_up(
                        {
                            "email": new_email.strip(),
                            "password": new_password,
                        }
                    )
                    st.success(
                        "Registration submitted. Open Sign in to log in. "
                        "If email confirmation is enabled, check your inbox."
                    )
                except Exception:
                    st.error(
                        "Registration failed. Try another email or "
                        "check the password requirements."
                    )

    st.stop()

# Verify authentication with Supabase on every page run.
try:
    token = st.session_state.access_token
    user = supabase.auth.get_user(token).user

    if user is None:
        raise ValueError("No authenticated user")

except Exception:
    st.session_state.clear()
    st.error("Your session expired. Refresh the page and sign in again.")
    st.stop()

st.success(f"Signed in as {user.email}")

if st.button("Sign out"):
    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    st.session_state.clear()
    st.rerun()

st.header("DVD Rental SQL Quiz")
st.write(
    "Choose a question, write PostgreSQL, and run it against "
    "the live Pagila database. Save your answer when ready."
)

with st.expander("Database tables and columns"):
    st.code(
        """
pagila.film
    film_id, title, rating, rental_rate, length

pagila.actor
    actor_id, first_name, last_name

pagila.film_actor
    actor_id, film_id

pagila.category
    category_id, name

pagila.film_category
    film_id, category_id

pagila.customer
    customer_id, first_name, last_name

pagila.payment
    payment_id, customer_id, amount, payment_date
""",
        language="text",
    )

if "saved_answers" not in st.session_state:
    try:
        st.session_state.saved_answers = load_answers(
            setting, supabase, token
        )
    except Exception:
        st.error(
            "Could not load saved answers. "
            "Check the database connection and quiz_private.answers table."
        )
        st.stop()

question = st.selectbox(
    "Choose a question",
    QUESTIONS,
    format_func=lambda q: (
        f"Question {q['id']}: {q['title']} — {q['points']} points"
    ),
)

question_id = question["id"]

st.subheader(question["title"])
st.write(question["prompt"])

with st.expander("Hint, expected SQL, and expected result"):
    st.write(question["hint"])
    st.code(question["expected_sql"], language="sql")

    if st.button("Show expected result", key=f"hint_{question_id}"):
        try:
            expected = run_query(
                setting,
                supabase,
                token,
                question["expected_sql"],
            )
            st.session_state[f"expected_{question_id}"] = expected
        except Exception as error:
            st.error(f"Could not run expected SQL: {error}")

    expected_key = f"expected_{question_id}"

    if expected_key in st.session_state:
        expected = st.session_state[expected_key]
        st.dataframe(expected, hide_index=True)
        st.caption(f"{len(expected)} rows")

editor_key = f"answer_{question_id}"

if editor_key not in st.session_state:
    st.session_state[editor_key] = (
        st.session_state.saved_answers.get(question_id, "")
    )

with st.form(f"question_form_{question_id}"):
    answer = st.text_area(
        "Your SQL",
        height=260,
        key=editor_key,
        placeholder="SELECT ...",
    )

    run_column, save_column = st.columns(2)

    with run_column:
        run_clicked = st.form_submit_button("Run SQL")

    with save_column:
        save_clicked = st.form_submit_button("Save answer")

if run_clicked:
    try:
        result = run_query(setting, supabase, token, answer)
        st.session_state[f"result_{question_id}"] = result
    except Exception as error:
        st.session_state.pop(f"result_{question_id}", None)
        st.error(f"Query failed: {error}")

if save_clicked:
    try:
        save_answer(
            setting,
            supabase,
            token,
            question_id,
            answer,
        )
        st.session_state.saved_answers[question_id] = answer
        st.success("Answer saved to the database.")
    except Exception:
        st.error(
            "Could not save the answer. "
            "Check your connection and session, and enter a nonempty answer."
        )

result_key = f"result_{question_id}"

if result_key in st.session_state:
    result = st.session_state[result_key]
    st.subheader("Your query result")
    st.dataframe(result, hide_index=True)
    st.caption(f"{len(result)} rows")

st.caption(
    f"Saved answers: {len(st.session_state.saved_answers)} / 5"
)