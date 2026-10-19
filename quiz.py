QUESTIONS = [
    {
        "id": 1,
        "title": "PG-13 films",
        "points": 4,
        "prompt": (
            "Return film_id, title, and rental_rate for the first "
            "10 PG-13 films ordered by film_id."
        ),
        "hint": "Filter film using WHERE, then ORDER BY and LIMIT.",
        "expected_sql": """
SELECT film_id, title, rental_rate
FROM pagila.film
WHERE rating = 'PG-13'
ORDER BY film_id
LIMIT 10;
""",
    },
    {
        "id": 2,
        "title": "Films featuring Penelope Guiness",
        "points": 4,
        "prompt": (
            "Return film_id and title for all films featuring the actor "
            "PENELOPE GUINESS. Order by film_id."
        ),
        "hint": (
            "Join film, film_actor, and actor. Filter on the actor's "
            "first_name and last_name."
        ),
        "expected_sql": """
SELECT f.film_id, f.title
FROM pagila.film AS f
JOIN pagila.film_actor AS fa
    ON f.film_id = fa.film_id
JOIN pagila.actor AS a
    ON fa.actor_id = a.actor_id
WHERE a.first_name = 'PENELOPE'
  AND a.last_name = 'GUINESS'
ORDER BY f.film_id;
""",
    },
    {
        "id": 3,
        "title": "Largest film categories",
        "points": 4,
        "prompt": (
            "Return the five categories with the most films. Show "
            "category name as category and film count as film_count. "
            "Order by film_count descending, then category ascending."
        ),
        "hint": (
            "Join category and film_category, GROUP BY category, "
            "then sort and LIMIT 5."
        ),
        "expected_sql": """
SELECT c.name AS category, COUNT(*) AS film_count
FROM pagila.category AS c
JOIN pagila.film_category AS fc
    ON c.category_id = fc.category_id
GROUP BY c.category_id, c.name
ORDER BY film_count DESC, category ASC
LIMIT 5;
""",
    },
    {
        "id": 4,
        "title": "Top-spending customers",
        "points": 4,
        "prompt": (
            "Return the five customers with the highest total payments. "
            "Show customer_id, first_name, last_name, and SUM(amount) "
            "as total_spent. Order by total_spent descending, "
            "then customer_id ascending."
        ),
        "hint": (
            "Join customer and payment, GROUP BY the customer, "
            "then sort and LIMIT 5."
        ),
        "expected_sql": """
SELECT c.customer_id, c.first_name, c.last_name,
       SUM(p.amount) AS total_spent
FROM pagila.customer AS c
JOIN pagila.payment AS p
    ON c.customer_id = p.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name
ORDER BY total_spent DESC, c.customer_id ASC
LIMIT 5;
""",
    },
    {
        "id": 5,
        "title": "Each customer's largest payment",
        "points": 4,
        "prompt": (
            "Use a CTE and ROW_NUMBER() to find each customer's "
            "largest payment. If amounts tie, choose the payment "
            "with the smallest payment_id. Return customer_id, "
            "payment_id, and amount. Order by customer_id."
        ),
        "hint": (
            "Inside the CTE, use ROW_NUMBER() partitioned by customer_id "
            "and ordered by amount descending, then payment_id ascending. "
            "In the outer query, keep rows numbered 1."
        ),
        "expected_sql": """
WITH ranked_payments AS (
    SELECT
        customer_id,
        payment_id,
        amount,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY amount DESC, payment_id ASC
        ) AS row_num
    FROM pagila.payment
)
SELECT customer_id, payment_id, amount
FROM ranked_payments
WHERE row_num = 1
ORDER BY customer_id;
""",
    },
]