from __future__ import annotations

import pandas as pd


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def calculate_kpis(transactions: pd.DataFrame) -> dict[str, float | str]:
    if transactions.empty:
        return {
            "income": 0.0,
            "expense": 0.0,
            "balance": 0.0,
            "savings_rate": 0.0,
            "expense_count": 0,
            "highest_category": "No data",
            "highest_category_amount": 0.0,
        }

    income = float(
        transactions.loc[
            transactions["transaction_type"] == "Income",
            "amount",
        ].sum()
    )

    expense_data = transactions[
        transactions["transaction_type"] == "Expense"
    ].copy()

    expense = float(expense_data["amount"].sum())
    balance = income - expense
    savings_rate = safe_divide(balance, income) * 100

    if expense_data.empty:
        highest_category = "No expense data"
        highest_category_amount = 0.0
    else:
        category_totals = (
            expense_data.groupby("category_name", as_index=False)["amount"]
            .sum()
            .sort_values("amount", ascending=False)
        )
        highest_category = str(category_totals.iloc[0]["category_name"])
        highest_category_amount = float(category_totals.iloc[0]["amount"])

    return {
        "income": income,
        "expense": expense,
        "balance": balance,
        "savings_rate": savings_rate,
        "expense_count": int(len(expense_data)),
        "highest_category": highest_category,
        "highest_category_amount": highest_category_amount,
    }


def calculate_budget_status(
    budgets: pd.DataFrame,
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    if budgets.empty:
        return pd.DataFrame(
            columns=[
                "budget_id",
                "category_name",
                "budget_limit",
                "actual_spend",
                "remaining",
                "usage_percentage",
                "status",
                "icon",
                "color",
            ]
        )

    expense_data = transactions[
        transactions["transaction_type"] == "Expense"
    ].copy()

    if expense_data.empty:
        spending = pd.DataFrame(
            columns=["category_name", "actual_spend"]
        )
    else:
        spending = (
            expense_data.groupby("category_name", as_index=False)["amount"]
            .sum()
            .rename(columns={"amount": "actual_spend"})
        )

    result = budgets.merge(
        spending,
        on="category_name",
        how="left",
    )

    result["actual_spend"] = result["actual_spend"].fillna(0.0)
    result["remaining"] = result["budget_limit"] - result["actual_spend"]

    result["usage_percentage"] = result.apply(
        lambda row: safe_divide(
            float(row["actual_spend"]),
            float(row["budget_limit"]),
        )
        * 100,
        axis=1,
    )

    def get_status(usage: float) -> str:
        if usage > 100:
            return "Exceeded"
        if usage >= 90:
            return "Near limit"
        if usage >= 70:
            return "Watch"
        return "Safe"

    result["status"] = result["usage_percentage"].apply(get_status)

    return result.sort_values(
        ["usage_percentage", "category_name"],
        ascending=[False, True],
    ).reset_index(drop=True)


def get_spending_insights(
    transactions: pd.DataFrame,
    budget_status: pd.DataFrame,
) -> list[dict[str, str]]:
    insights: list[dict[str, str]] = []

    if transactions.empty:
        return [
            {
                "title": "Start tracking",
                "message": "Add your first income or expense transaction to unlock personal insights.",
                "level": "info",
            }
        ]

    expense_data = transactions[
        transactions["transaction_type"] == "Expense"
    ].copy()

    if not expense_data.empty:
        total_expense = float(expense_data["amount"].sum())

        category_totals = (
            expense_data.groupby("category_name", as_index=False)["amount"]
            .sum()
            .sort_values("amount", ascending=False)
        )

        top = category_totals.iloc[0]
        top_share = safe_divide(float(top["amount"]), total_expense) * 100

        insights.append(
            {
                "title": "Largest spending category",
                "message": (
                    f"{top['category_name']} is your highest expense category, "
                    f"with ₹{float(top['amount']):,.0f} spent "
                    f"({top_share:.1f}% of total expenses)."
                ),
                "level": "info",
            }
        )

        essential_total = float(
            expense_data.loc[
                expense_data["necessity_type"] == "Essential",
                "amount",
            ].sum()
        )

        non_essential_total = float(
            expense_data.loc[
                expense_data["necessity_type"] == "Non-essential",
                "amount",
            ].sum()
        )

        non_essential_share = safe_divide(
            non_essential_total,
            total_expense,
        ) * 100

        if non_essential_share >= 35:
            insights.append(
                {
                    "title": "Non-essential spending is high",
                    "message": (
                        f"₹{non_essential_total:,.0f} "
                        f"({non_essential_share:.1f}%) of your expenses are marked "
                        "non-essential. Review entertainment, shopping, or impulse purchases."
                    ),
                    "level": "warning",
                }
            )
        elif essential_total > 0:
            insights.append(
                {
                    "title": "Spending mix",
                    "message": (
                        f"Your essential expenses are ₹{essential_total:,.0f}, while "
                        f"non-essential expenses are ₹{non_essential_total:,.0f}."
                    ),
                    "level": "success",
                }
            )

    if not budget_status.empty:
        exceeded = budget_status[
            budget_status["status"] == "Exceeded"
        ]

        near_limit = budget_status[
            budget_status["status"] == "Near limit"
        ]

        if not exceeded.empty:
            names = ", ".join(exceeded["category_name"].tolist())
            over_amount = float((-exceeded["remaining"]).sum())

            insights.append(
                {
                    "title": "Budget exceeded",
                    "message": (
                        f"You have exceeded the budget for {names} by a combined "
                        f"₹{over_amount:,.0f}. Consider reducing spending in these categories."
                    ),
                    "level": "error",
                }
            )
        elif not near_limit.empty:
            names = ", ".join(near_limit["category_name"].tolist())

            insights.append(
                {
                    "title": "Budget warning",
                    "message": (
                        f"You are close to the budget limit in {names}. "
                        "Track new purchases carefully for the rest of the month."
                    ),
                    "level": "warning",
                }
            )
        elif len(budget_status) > 0:
            insights.append(
                {
                    "title": "Budgets are healthy",
                    "message": (
                        "All configured categories are currently within their budget limits."
                    ),
                    "level": "success",
                }
            )

    recurring_count = int(
        expense_data["is_recurring"].sum()
    ) if not expense_data.empty else 0

    if recurring_count > 0:
        recurring_total = float(
            expense_data.loc[
                expense_data["is_recurring"],
                "amount",
            ].sum()
        )

        insights.append(
            {
                "title": "Recurring commitments",
                "message": (
                    f"You have {recurring_count} recurring expense record(s) totaling "
                    f"₹{recurring_total:,.0f} in the selected period."
                ),
                "level": "info",
            }
        )

    return insights[:4]


def get_monthly_summary(transactions: pd.DataFrame) -> pd.DataFrame:
    if transactions.empty:
        return pd.DataFrame(
            columns=["month", "income", "expense", "balance"]
        )

    dataframe = transactions.copy()
    dataframe["month"] = dataframe["transaction_date"].dt.to_period("M").astype(str)

    grouped = (
        dataframe.pivot_table(
            index="month",
            columns="transaction_type",
            values="amount",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )

    if "Income" not in grouped.columns:
        grouped["Income"] = 0.0

    if "Expense" not in grouped.columns:
        grouped["Expense"] = 0.0

    grouped = grouped.rename(
        columns={
            "Income": "income",
            "Expense": "expense",
        }
    )

    grouped["balance"] = grouped["income"] - grouped["expense"]

    return grouped.sort_values("month").reset_index(drop=True)