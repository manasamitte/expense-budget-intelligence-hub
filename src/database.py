from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "expense_budget_hub.db"


DEFAULT_CATEGORIES = [
    ("Food", "Expense", "🍔", "#FF6B6B"),
    ("Travel", "Expense", "🚇", "#4D96FF"),
    ("Education", "Expense", "📚", "#845EC2"),
    ("Housing", "Expense", "🏠", "#F9A826"),
    ("Bills", "Expense", "💡", "#00C9A7"),
    ("Shopping", "Expense", "🛍️", "#FF9671"),
    ("Entertainment", "Expense", "🎬", "#C34A36"),
    ("Health", "Expense", "🏥", "#2C73D2"),
    ("Savings", "Expense", "🏦", "#008F7A"),
    ("Other", "Expense", "📌", "#6C757D"),
    ("Pocket Money", "Income", "💰", "#00B894"),
    ("Salary", "Income", "💼", "#0984E3"),
    ("Freelance", "Income", "🧑‍💻", "#6C5CE7"),
    ("Scholarship", "Income", "🎓", "#E17055"),
    ("Gift", "Income", "🎁", "#E84393"),
    ("Other Income", "Income", "➕", "#00CEC9"),
]


def get_connection() -> sqlite3.Connection:
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def initialize_database() -> None:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL DEFAULT 'Student',
            monthly_income REAL NOT NULL DEFAULT 0,
            monthly_savings_target REAL NOT NULL DEFAULT 0,
            currency TEXT NOT NULL DEFAULT 'INR',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL,
            category_type TEXT NOT NULL CHECK(category_type IN ('Income', 'Expense')),
            icon TEXT DEFAULT '📌',
            color TEXT DEFAULT '#6C757D',
            UNIQUE(category_name, category_type)
        );

        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            transaction_type TEXT NOT NULL CHECK(transaction_type IN ('Income', 'Expense')),
            transaction_date TEXT NOT NULL,
            payment_method TEXT NOT NULL DEFAULT 'UPI',
            merchant TEXT,
            description TEXT,
            necessity_type TEXT NOT NULL DEFAULT 'Essential'
                CHECK(necessity_type IN ('Essential', 'Non-essential')),
            is_recurring INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(category_id) REFERENCES categories(category_id)
        );

        CREATE TABLE IF NOT EXISTS budgets (
            budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            budget_month TEXT NOT NULL,
            budget_limit REAL NOT NULL CHECK(budget_limit >= 0),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(category_id) REFERENCES categories(category_id),
            UNIQUE(user_id, category_id, budget_month)
        );

        CREATE TABLE IF NOT EXISTS savings_goals (
            goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            goal_name TEXT NOT NULL,
            target_amount REAL NOT NULL CHECK(target_amount > 0),
            current_amount REAL NOT NULL DEFAULT 0 CHECK(current_amount >= 0),
            target_date TEXT,
            status TEXT NOT NULL DEFAULT 'Active'
                CHECK(status IN ('Active', 'Completed', 'Paused')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        );
        """
    )

    user_count = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if user_count == 0:
        cursor.execute(
            """
            INSERT INTO users (name, monthly_income, monthly_savings_target, currency)
            VALUES (?, ?, ?, ?)
            """,
            ("Student", 0, 0, "INR"),
        )

    cursor.executemany(
        """
        INSERT OR IGNORE INTO categories (category_name, category_type, icon, color)
        VALUES (?, ?, ?, ?)
        """,
        DEFAULT_CATEGORIES,
    )

    connection.commit()
    connection.close()


def execute_query(query: str, parameters: Iterable[Any] = ()) -> None:
    connection = get_connection()
    connection.execute(query, tuple(parameters))
    connection.commit()
    connection.close()


def get_user() -> dict[str, Any]:
    connection = get_connection()
    user = connection.execute(
        """
        SELECT user_id, name, monthly_income, monthly_savings_target, currency
        FROM users
        ORDER BY user_id
        LIMIT 1
        """
    ).fetchone()
    connection.close()
    return dict(user)


def update_user(
    name: str,
    monthly_income: float,
    monthly_savings_target: float,
    currency: str,
) -> None:
    user = get_user()

    execute_query(
        """
        UPDATE users
        SET name = ?, monthly_income = ?, monthly_savings_target = ?, currency = ?
        WHERE user_id = ?
        """,
        (name.strip() or "Student", monthly_income, monthly_savings_target, currency, user["user_id"]),
    )


def get_categories(category_type: str | None = None) -> pd.DataFrame:
    connection = get_connection()

    if category_type:
        dataframe = pd.read_sql_query(
            """
            SELECT category_id, category_name, category_type, icon, color
            FROM categories
            WHERE category_type = ?
            ORDER BY category_name
            """,
            connection,
            params=(category_type,),
        )
    else:
        dataframe = pd.read_sql_query(
            """
            SELECT category_id, category_name, category_type, icon, color
            FROM categories
            ORDER BY category_type, category_name
            """,
            connection,
        )

    connection.close()
    return dataframe


def add_category(
    category_name: str,
    category_type: str,
    icon: str = "📌",
    color: str = "#6C757D",
) -> None:
    execute_query(
        """
        INSERT OR IGNORE INTO categories (category_name, category_type, icon, color)
        VALUES (?, ?, ?, ?)
        """,
        (category_name.strip(), category_type, icon.strip() or "📌", color),
    )


def get_category_id(category_name: str, category_type: str) -> int:
    connection = get_connection()
    result = connection.execute(
        """
        SELECT category_id
        FROM categories
        WHERE category_name = ? AND category_type = ?
        """,
        (category_name, category_type),
    ).fetchone()
    connection.close()

    if result is None:
        raise ValueError("Selected category was not found.")

    return int(result["category_id"])


def add_transaction(
    user_id: int,
    category_name: str,
    transaction_type: str,
    amount: float,
    transaction_date: str,
    payment_method: str,
    merchant: str,
    description: str,
    necessity_type: str,
    is_recurring: bool,
) -> None:
    category_id = get_category_id(category_name, transaction_type)

    execute_query(
        """
        INSERT INTO transactions (
            user_id,
            category_id,
            amount,
            transaction_type,
            transaction_date,
            payment_method,
            merchant,
            description,
            necessity_type,
            is_recurring
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            category_id,
            amount,
            transaction_type,
            transaction_date,
            payment_method,
            merchant.strip(),
            description.strip(),
            necessity_type,
            int(is_recurring),
        ),
    )


def get_transactions(
    start_date: str | None = None,
    end_date: str | None = None,
    transaction_type: str | None = None,
    category_name: str | None = None,
) -> pd.DataFrame:
    query = """
        SELECT
            t.transaction_id,
            t.amount,
            t.transaction_type,
            t.transaction_date,
            t.payment_method,
            COALESCE(t.merchant, '') AS merchant,
            COALESCE(t.description, '') AS description,
            t.necessity_type,
            t.is_recurring,
            c.category_name,
            c.icon,
            c.color
        FROM transactions t
        INNER JOIN categories c ON t.category_id = c.category_id
        WHERE 1 = 1
    """

    parameters: list[Any] = []

    if start_date:
        query += " AND DATE(t.transaction_date) >= DATE(?)"
        parameters.append(start_date)

    if end_date:
        query += " AND DATE(t.transaction_date) <= DATE(?)"
        parameters.append(end_date)

    if transaction_type and transaction_type != "All":
        query += " AND t.transaction_type = ?"
        parameters.append(transaction_type)

    if category_name and category_name != "All":
        query += " AND c.category_name = ?"
        parameters.append(category_name)

    query += " ORDER BY DATE(t.transaction_date) DESC, t.transaction_id DESC"

    connection = get_connection()
    dataframe = pd.read_sql_query(query, connection, params=parameters)
    connection.close()

    if not dataframe.empty:
        dataframe["transaction_date"] = pd.to_datetime(dataframe["transaction_date"])
        dataframe["is_recurring"] = dataframe["is_recurring"].astype(bool)

    return dataframe


def update_transaction(
    transaction_id: int,
    category_name: str,
    transaction_type: str,
    amount: float,
    transaction_date: str,
    payment_method: str,
    merchant: str,
    description: str,
    necessity_type: str,
    is_recurring: bool,
) -> None:
    category_id = get_category_id(category_name, transaction_type)

    execute_query(
        """
        UPDATE transactions
        SET
            category_id = ?,
            amount = ?,
            transaction_type = ?,
            transaction_date = ?,
            payment_method = ?,
            merchant = ?,
            description = ?,
            necessity_type = ?,
            is_recurring = ?
        WHERE transaction_id = ?
        """,
        (
            category_id,
            amount,
            transaction_type,
            transaction_date,
            payment_method,
            merchant.strip(),
            description.strip(),
            necessity_type,
            int(is_recurring),
            transaction_id,
        ),
    )


def delete_transaction(transaction_id: int) -> None:
    execute_query(
        "DELETE FROM transactions WHERE transaction_id = ?",
        (transaction_id,),
    )


def save_budget(
    user_id: int,
    category_name: str,
    budget_month: str,
    budget_limit: float,
) -> None:
    category_id = get_category_id(category_name, "Expense")

    execute_query(
        """
        INSERT INTO budgets (user_id, category_id, budget_month, budget_limit)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, category_id, budget_month)
        DO UPDATE SET budget_limit = excluded.budget_limit
        """,
        (user_id, category_id, budget_month, budget_limit),
    )


def get_budgets(budget_month: str) -> pd.DataFrame:
    connection = get_connection()

    dataframe = pd.read_sql_query(
        """
        SELECT
            b.budget_id,
            b.budget_month,
            b.budget_limit,
            c.category_id,
            c.category_name,
            c.icon,
            c.color
        FROM budgets b
        INNER JOIN categories c ON b.category_id = c.category_id
        WHERE b.budget_month = ?
        ORDER BY c.category_name
        """,
        connection,
        params=(budget_month,),
    )

    connection.close()
    return dataframe


def delete_budget(budget_id: int) -> None:
    execute_query(
        "DELETE FROM budgets WHERE budget_id = ?",
        (budget_id,),
    )


def add_goal(
    user_id: int,
    goal_name: str,
    target_amount: float,
    current_amount: float,
    target_date: str | None,
    status: str,
) -> None:
    execute_query(
        """
        INSERT INTO savings_goals (
            user_id,
            goal_name,
            target_amount,
            current_amount,
            target_date,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            goal_name.strip(),
            target_amount,
            current_amount,
            target_date,
            status,
        ),
    )


def get_goals() -> pd.DataFrame:
    connection = get_connection()

    dataframe = pd.read_sql_query(
        """
        SELECT
            goal_id,
            goal_name,
            target_amount,
            current_amount,
            target_date,
            status,
            created_at
        FROM savings_goals
        ORDER BY
            CASE status
                WHEN 'Active' THEN 1
                WHEN 'Paused' THEN 2
                ELSE 3
            END,
            target_date ASC
        """,
        connection,
    )

    connection.close()

    if not dataframe.empty:
        dataframe["target_date"] = pd.to_datetime(
            dataframe["target_date"],
            errors="coerce",
        )

    return dataframe


def update_goal_amount(goal_id: int, current_amount: float, status: str) -> None:
    execute_query(
        """
        UPDATE savings_goals
        SET current_amount = ?, status = ?
        WHERE goal_id = ?
        """,
        (current_amount, status, goal_id),
    )


def delete_goal(goal_id: int) -> None:
    execute_query(
        "DELETE FROM savings_goals WHERE goal_id = ?",
        (goal_id,),
    )


def import_transactions(dataframe: pd.DataFrame, user_id: int) -> tuple[int, list[str]]:
    required_columns = {
        "amount",
        "transaction_type",
        "transaction_date",
        "category_name",
    }

    normalized = dataframe.copy()
    normalized.columns = [
        str(column).strip().lower().replace(" ", "_")
        for column in normalized.columns
    ]

    missing_columns = required_columns - set(normalized.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        return 0, [f"Missing required CSV columns: {missing}"]

    optional_defaults = {
        "payment_method": "UPI",
        "merchant": "",
        "description": "",
        "necessity_type": "Essential",
        "is_recurring": False,
    }

    for column, default_value in optional_defaults.items():
        if column not in normalized.columns:
            normalized[column] = default_value

    inserted_rows = 0
    errors: list[str] = []

    for row_number, row in normalized.iterrows():
        try:
            transaction_type = str(row["transaction_type"]).strip().title()

            if transaction_type not in {"Income", "Expense"}:
                raise ValueError("transaction_type must be Income or Expense")

            amount = float(row["amount"])
            if amount <= 0:
                raise ValueError("amount must be greater than zero")

            category_name = str(row["category_name"]).strip()
            category_id = get_category_id(category_name, transaction_type)

            necessity_type = str(row["necessity_type"]).strip().title()
            if necessity_type not in {"Essential", "Non-essential"}:
                necessity_type = "Essential"

            recurring_value = str(row["is_recurring"]).strip().lower()
            is_recurring = recurring_value in {"true", "1", "yes", "y"}

            execute_query(
                """
                INSERT INTO transactions (
                    user_id,
                    category_id,
                    amount,
                    transaction_type,
                    transaction_date,
                    payment_method,
                    merchant,
                    description,
                    necessity_type,
                    is_recurring
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    category_id,
                    amount,
                    transaction_type,
                    str(row["transaction_date"]),
                    str(row["payment_method"]),
                    str(row["merchant"]),
                    str(row["description"]),
                    necessity_type,
                    int(is_recurring),
                ),
            )

            inserted_rows += 1

        except Exception as error:
            errors.append(f"Row {row_number + 2}: {error}")

    return inserted_rows, errors