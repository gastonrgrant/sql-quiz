CREATE SCHEMA IF NOT EXISTS quiz_private;

CREATE TABLE IF NOT EXISTS quiz_private.answers (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL CHECK (question_id BETWEEN 1 AND 5),
    sql_answer TEXT NOT NULL,
    saved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, question_id)
);

REVOKE ALL ON SCHEMA quiz_private
FROM PUBLIC, anon, authenticated, quiz_reader;

REVOKE ALL ON quiz_private.answers
FROM PUBLIC, anon, authenticated, quiz_reader;