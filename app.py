from __future__ import annotations

import calendar
from datetime import date, timedelta
from io import BytesIO

import pandas as pd
import streamlit as st

from src.analytics import (
    calculate_budget_status,
    calculate_kpis,
    get_monthly_summary,
    get_spending_insights,
)
from src.charts import (
    budget_vs_spending_chart,
    category_expense_chart,
    daily_cashflow_chart,
    monthly_summary_chart,
    payment_method_chart,
)
from src.database import (
    add_category,
    add_goal,
    add_transaction,
    delete_budget,
    delete_goal,
    delete_transaction,
    get_budgets,
    get_categories,
    get_goals,
    get_transactions,
    get_user,
    import_transactions,
    initialize_database,
    save_budget,
    update_goal_amount,
    update_transaction,
    update_user,
)
from src.ui import (
    budget_card,
    configure_page,
    hero,
    inject_custom_css,
    metric_card,
    section_title,
    show_insight,
)


configure_page()
initialize_database()
inject_custom_css()


PAYMENT_METHODS = [
    "UPI",
    "Cash",
    "Debit Card",
    "Credit Card",
    "Net Banking",
    "Wallet",
    "Other",
]

CURRENCIES = ["INR", "USD", "EUR", "GBP"]


def get_month_bounds(selected_date: date) -> tuple[date, date]:
    first_day = selected_date.replace(day=1)
    last_day_number = calendar.monthrange(
        selected_date.year,
        selected_date.month,
    )[1]
    last_day = selected_date.replace(day=last_day_number)
    return first_day, last_day


def month_key(selected_date: date) -> str:
    return selected_date.strftime("%Y-%m")


def format_currency(value: float, currency: str = "INR") -> str:
    symbols = {
        "INR": "₹",
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
    }
    symbol = symbols.get(currency, "₹")
    return f"{symbol}{value:,.0f}"


def status_badge(status: str) -> str:
    color_map = {
        "Safe": "#DCFCE7",
        "Watch": "#FEF3C7",
        "Near limit": "#FFEDD5",
        "Exceeded": "#FEE2E2",
    }
    text_map = {
        "Safe": "#047857",
        "Watch": "#B45309",
        "Near limit": "#C2410C",
        "Exceeded": "#DC2626",
    }

    background = color_map.get(status, "#E2E8F0")
    color = text_map.get(status, "#334155")

    return (
        f"<span style='background:{background}; color:{color}; "
        "padding:0.28rem 0.55rem; border-radius:999px; "
        "font-size:0.78rem; font-weight:700;'>"
        f"{status}</span>"
    )


def month_filter_widget(key_prefix: str) -> tuple[date, date]:
    today = date.today()
    default_start, default_end = get_month_bounds(today)

    selected_range = st.date_input(
        "Select date range",
        value=(default_start, default_end),
        max_value=today,
        key=f"{key_prefix}_date_range",
    )

    if isinstance(selected_range, tuple) and len(selected_range) == 2:
        return selected_range[0], selected_range[1]

    if isinstance(selected_range, list) and len(selected_range) == 2:
        return selected_range[0], selected_range[1]

    if isinstance(selected_range, date):
        return selected_range, selected_range

    return default_start, default_end


def show_sidebar() -> None:
    user = get_user()

    with st.sidebar:
        st.markdown("## 💸 SpendWise")
        st.caption("Your personal budget intelligence hub")
        st.divider()

        st.markdown(f"### Hello, {user['name']} 👋")
        st.caption(
            f"Monthly target: {format_currency(float(user['monthly_savings_target']), user['currency'])}"
        )

        st.divider()

        st.markdown("### Quick tips")
        st.caption("• Add expenses daily")
        st.caption("• Set realistic category budgets")
        st.caption("• Review non-essential spending weekly")
        st.caption("• Export a report at month end")

        st.divider()
        st.caption("Built with Python, Streamlit, SQLite & Pandas")


def dashboard_page() -> None:
    user = get_user()
    hero(
        "Financial clarity, one transaction at a time",
        (
            f"Welcome back, {user['name']}. Monitor your spending, "
            "protect your budget, and grow your savings."
        ),
        "✨",
    )

    filter_col, summary_col = st.columns([2, 1])

    with filter_col:
        start_date, end_date = month_filter_widget("dashboard")

    with summary_col:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info(
            f"Viewing: **{start_date.strftime('%d %b %Y')}** to "
            f"**{end_date.strftime('%d %b %Y')}**"
        )

    transactions = get_transactions(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
    )

    selected_month_key = month_key(start_date)
    budgets = get_budgets(selected_month_key)
    budget_status = calculate_budget_status(budgets, transactions)
    kpis = calculate_kpis(transactions)
    currency = user["currency"]

    metric_columns = st.columns(4)

    with metric_columns[0]:
        metric_card(
            "Total income",
            format_currency(float(kpis["income"]), currency),
            "Money received in this period",
        )

    with metric_columns[1]:
        metric_card(
            "Total expenses",
            format_currency(float(kpis["expense"]), currency),
            f"{int(kpis['expense_count'])} expense record(s)",
        )

    with metric_columns[2]:
        balance_note = (
            "Positive cash balance"
            if float(kpis["balance"]) >= 0
            else "Expenses exceed income"
        )
        metric_card(
            "Current balance",
            format_currency(float(kpis["balance"]), currency),
            balance_note,
        )

    with metric_columns[3]:
        metric_card(
            "Savings rate",
            f"{float(kpis['savings_rate']):.1f}%",
            f"Top spend: {kpis['highest_category']}",
        )

    st.write("")

    section_title(
        "Budget pulse",
        "A quick look at how your category budgets are performing.",
    )

    if budget_status.empty:
        st.info(
            "You have not configured any budget for this month. "
            "Open **Budget Planner** from the sidebar to get started."
        )
    else:
        budget_columns = st.columns(3)

        for index, row in budget_status.head(6).iterrows():
            with budget_columns[index % 3]:
                budget_card(
                    category=str(row["category_name"]),
                    budget=float(row["budget_limit"]),
                    spent=float(row["actual_spend"]),
                    remaining=float(row["remaining"]),
                    usage=float(row["usage_percentage"]),
                    status=str(row["status"]),
                    icon=str(row["icon"]),
                )

    st.write("")

    chart_col_1, chart_col_2 = st.columns(2)

    with chart_col_1:
        st.plotly_chart(
            category_expense_chart(transactions),
            use_container_width=True,
        )

    with chart_col_2:
        st.plotly_chart(
            daily_cashflow_chart(transactions),
            use_container_width=True,
        )

    chart_col_3, chart_col_4 = st.columns(2)

    with chart_col_3:
        st.plotly_chart(
            budget_vs_spending_chart(budget_status),
            use_container_width=True,
        )

    with chart_col_4:
        st.plotly_chart(
            payment_method_chart(transactions),
            use_container_width=True,
        )

    section_title(
        "Smart insights",
        "Automatically generated observations from your selected financial data.",
    )

    insights = get_spending_insights(transactions, budget_status)

    for insight in insights:
        show_insight(
            insight["title"],
            insight["message"],
            insight["level"],
        )

    section_title(
        "Recent transactions",
        "Your latest income and expense records.",
    )

    if transactions.empty:
        st.info("No transactions found in the selected period.")
    else:
        recent = transactions.head(8).copy()
        recent["transaction_date"] = recent["transaction_date"].dt.strftime("%d %b %Y")
        recent["amount"] = recent.apply(
            lambda row: (
                "+ " if row["transaction_type"] == "Income" else "- "
            )
            + format_currency(float(row["amount"]), currency),
            axis=1,
        )

        display_columns = [
            "transaction_date",
            "icon",
            "category_name",
            "merchant",
            "payment_method",
            "amount",
        ]

        st.dataframe(
            recent[display_columns].rename(
                columns={
                    "transaction_date": "Date",
                    "icon": "",
                    "category_name": "Category",
                    "merchant": "Merchant",
                    "payment_method": "Payment",
                    "amount": "Amount",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )


def add_transaction_page() -> None:
    user = get_user()
    hero(
        "Add a transaction",
        "Record your income and expenses in seconds. Small daily entries create powerful monthly insights.",
        "➕",
    )

    type_col, category_col = st.columns(2)

    with type_col:
        transaction_type = st.radio(
            "Transaction type",
            ["Expense", "Income"],
            horizontal=True,
        )

    categories = get_categories(transaction_type)
    category_options = categories["category_name"].tolist()

    with category_col:
        category_name = st.selectbox(
            "Category",
            category_options,
        )

    with st.form("transaction_form", clear_on_submit=True):
        amount_col, date_col, method_col = st.columns(3)

        with amount_col:
            amount = st.number_input(
                "Amount (₹)",
                min_value=1.0,
                value=100.0,
                step=10.0,
            )

        with date_col:
            transaction_date = st.date_input(
                "Transaction date",
                value=date.today(),
            )

        with method_col:
            payment_method = st.selectbox(
                "Payment method",
                PAYMENT_METHODS,
            )

        merchant_col, necessity_col = st.columns(2)

        with merchant_col:
            merchant = st.text_input(
                "Merchant / Place",
                placeholder="Example: College canteen, Metro, Amazon",
            )

        with necessity_col:
            necessity_type = st.selectbox(
                "Spending type",
                ["Essential", "Non-essential"],
                disabled=transaction_type == "Income",
            )

        description = st.text_area(
            "Description / Note",
            placeholder="Example: Lunch after college",
        )

        is_recurring = st.checkbox(
            "This is a recurring monthly transaction",
        )

        submitted = st.form_submit_button(
            "Save transaction",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        try:
            add_transaction(
                user_id=int(user["user_id"]),
                category_name=category_name,
                transaction_type=transaction_type,
                amount=float(amount),
                transaction_date=transaction_date.isoformat(),
                payment_method=payment_method,
                merchant=merchant,
                description=description,
                necessity_type=(
                    "Essential"
                    if transaction_type == "Income"
                    else necessity_type
                ),
                is_recurring=is_recurring,
            )
            st.success(
                f"{transaction_type} of {format_currency(float(amount), user['currency'])} saved successfully."
            )
        except Exception as error:
            st.error(f"Unable to save transaction: {error}")

    st.divider()
    section_title(
        "Add a custom category",
        "Create a category when the default list does not match your needs.",
    )

    with st.expander("Create category"):
        with st.form("category_form", clear_on_submit=True):
            custom_name = st.text_input(
                "New category name",
                placeholder="Example: Pets, Sports, Side Project",
            )

            custom_type = st.radio(
                "Category type",
                ["Expense", "Income"],
                horizontal=True,
            )

            custom_icon = st.text_input(
                "Icon",
                value="📌",
                max_chars=3,
            )

            custom_color = st.color_picker(
                "Category color",
                value="#6C63FF",
            )

            category_submitted = st.form_submit_button(
                "Create category",
                type="primary",
            )

        if category_submitted:
            if not custom_name.strip():
                st.warning("Enter a category name first.")
            else:
                add_category(
                    category_name=custom_name,
                    category_type=custom_type,
                    icon=custom_icon,
                    color=custom_color,
                )
                st.success(f"Category '{custom_name.strip()}' is ready to use.")


def transactions_page() -> None:
    user = get_user()
    hero(
        "Transactions centre",
        "Search, filter, update, delete, import, and export your financial records.",
        "🧾",
    )

    all_categories = get_categories()
    all_category_options = ["All"] + all_categories["category_name"].tolist()

    filter_col_1, filter_col_2, filter_col_3 = st.columns(3)

    with filter_col_1:
        start_date, end_date = month_filter_widget("transactions")

    with filter_col_2:
        transaction_type = st.selectbox(
            "Transaction type filter",
            ["All", "Income", "Expense"],
        )

    with filter_col_3:
        selected_category = st.selectbox(
            "Category filter",
            all_category_options,
        )

    transactions = get_transactions(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        transaction_type=transaction_type,
        category_name=selected_category,
    )

    section_title(
        "Filtered records",
        f"{len(transactions)} record(s) found for the selected filters.",
    )

    if transactions.empty:
        st.info("No records match your filters.")
    else:
        display = transactions.copy()
        display["transaction_date"] = display["transaction_date"].dt.strftime("%d %b %Y")
        display["amount"] = display.apply(
            lambda row: (
                "+ " if row["transaction_type"] == "Income" else "- "
            )
            + format_currency(float(row["amount"]), user["currency"]),
            axis=1,
        )
        display["is_recurring"] = display["is_recurring"].map(
            {True: "Yes", False: "No"}
        )

        st.dataframe(
            display[
                [
                    "transaction_id",
                    "transaction_date",
                    "transaction_type",
                    "icon",
                    "category_name",
                    "amount",
                    "payment_method",
                    "merchant",
                    "necessity_type",
                    "is_recurring",
                    "description",
                ]
            ].rename(
                columns={
                    "transaction_id": "ID",
                    "transaction_date": "Date",
                    "transaction_type": "Type",
                    "icon": "",
                    "category_name": "Category",
                    "amount": "Amount",
                    "payment_method": "Payment",
                    "merchant": "Merchant",
                    "necessity_type": "Spending type",
                    "is_recurring": "Recurring",
                    "description": "Note",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        export_data = transactions.copy()
        export_data["transaction_date"] = export_data["transaction_date"].dt.strftime(
            "%Y-%m-%d"
        )

        csv_bytes = export_data.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="⬇️ Download filtered transactions as CSV",
            data=csv_bytes,
            file_name="spendwise_transactions.csv",
            mime="text/csv",
        )

    st.divider()

    edit_col, delete_col = st.columns(2)

    with edit_col:
        section_title(
            "Edit transaction",
            "Select a transaction ID from the table above to update it.",
        )

        if transactions.empty:
            st.caption("No transaction is available to edit.")
        else:
            transaction_ids = transactions["transaction_id"].tolist()
            selected_id = st.selectbox(
                "Transaction ID to edit",
                transaction_ids,
                key="edit_transaction_id",
            )

            selected_row = transactions[
                transactions["transaction_id"] == selected_id
            ].iloc[0]

            selected_type = str(selected_row["transaction_type"])
            edit_categories = get_categories(selected_type)["category_name"].tolist()
            selected_category_index = edit_categories.index(
                selected_row["category_name"]
            )

            with st.form("edit_transaction_form"):
                edit_amount = st.number_input(
                    "Amount (₹)",
                    min_value=1.0,
                    value=float(selected_row["amount"]),
                    step=10.0,
                    key="edit_amount",
                )

                edit_date = st.date_input(
                    "Date",
                    value=selected_row["transaction_date"].date(),
                    key="edit_date",
                )

                edit_category = st.selectbox(
                    "Category",
                    edit_categories,
                    index=selected_category_index,
                    key="edit_category",
                )

                edit_payment = st.selectbox(
                    "Payment method",
                    PAYMENT_METHODS,
                    index=PAYMENT_METHODS.index(
                        selected_row["payment_method"]
                    )
                    if selected_row["payment_method"] in PAYMENT_METHODS
                    else 0,
                    key="edit_payment",
                )

                edit_merchant = st.text_input(
                    "Merchant / Place",
                    value=str(selected_row["merchant"]),
                    key="edit_merchant",
                )

                spending_types = ["Essential", "Non-essential"]
                edit_necessity = st.selectbox(
                    "Spending type",
                    spending_types,
                    index=spending_types.index(
                        selected_row["necessity_type"]
                    )
                    if selected_row["necessity_type"] in spending_types
                    else 0,
                    disabled=selected_type == "Income",
                    key="edit_necessity",
                )

                edit_description = st.text_area(
                    "Description / Note",
                    value=str(selected_row["description"]),
                    key="edit_description",
                )

                edit_recurring = st.checkbox(
                    "Recurring transaction",
                    value=bool(selected_row["is_recurring"]),
                    key="edit_recurring",
                )

                update_submitted = st.form_submit_button(
                    "Update transaction",
                    type="primary",
                    use_container_width=True,
                )

            if update_submitted:
                update_transaction(
                    transaction_id=int(selected_id),
                    category_name=edit_category,
                    transaction_type=selected_type,
                    amount=float(edit_amount),
                    transaction_date=edit_date.isoformat(),
                    payment_method=edit_payment,
                    merchant=edit_merchant,
                    description=edit_description,
                    necessity_type=(
                        "Essential"
                        if selected_type == "Income"
                        else edit_necessity
                    ),
                    is_recurring=edit_recurring,
                )
                st.success("Transaction updated. Refreshing records...")
                st.rerun()

    with delete_col:
        section_title(
            "Delete transaction",
            "Deletion is permanent, so review the selected record before confirming.",
        )

        if transactions.empty:
            st.caption("No transaction is available to delete.")
        else:
            delete_id = st.selectbox(
                "Transaction ID to delete",
                transactions["transaction_id"].tolist(),
                key="delete_transaction_id",
            )

            selected_delete_row = transactions[
                transactions["transaction_id"] == delete_id
            ].iloc[0]

            st.warning(
                f"Selected: {selected_delete_row['category_name']} — "
                f"{format_currency(float(selected_delete_row['amount']), user['currency'])} "
                f"on {selected_delete_row['transaction_date'].strftime('%d %b %Y')}."
            )

            confirm_delete = st.checkbox(
                "I understand that this action cannot be undone.",
                key="confirm_transaction_delete",
            )

            if st.button(
                "Delete selected transaction",
                type="primary",
                disabled=not confirm_delete,
                use_container_width=True,
            ):
                delete_transaction(int(delete_id))
                st.success("Transaction deleted.")
                st.rerun()

    st.divider()
    section_title(
        "Import transactions from CSV",
        "Use this for bulk upload. Required columns: amount, transaction_type, transaction_date, category_name.",
    )

    template_dataframe = pd.DataFrame(
        [
            {
                "amount": 180,
                "transaction_type": "Expense",
                "transaction_date": "2026-10-02",
                "category_name": "Food",
                "payment_method": "UPI",
                "merchant": "College Canteen",
                "description": "Lunch",
                "necessity_type": "Essential",
                "is_recurring": False,
            },
            {
                "amount": 8000,
                "transaction_type": "Income",
                "transaction_date": "2026-10-01",
                "category_name": "Pocket Money",
                "payment_method": "UPI",
                "merchant": "Family",
                "description": "Monthly allowance",
                "necessity_type": "Essential",
                "is_recurring": False,
            },
        ]
    )

    st.download_button(
        "⬇️ Download CSV template",
        data=template_dataframe.to_csv(index=False).encode("utf-8"),
        file_name="spendwise_import_template.csv",
        mime="text/csv",
    )

    uploaded_file = st.file_uploader(
        "Upload a CSV file",
        type=["csv"],
        key="transaction_csv_upload",
    )

    if uploaded_file is not None:
        try:
            uploaded_dataframe = pd.read_csv(uploaded_file)
            st.dataframe(uploaded_dataframe.head(), use_container_width=True)

            if st.button(
                "Import uploaded transactions",
                type="primary",
            ):
                inserted, errors = import_transactions(
                    uploaded_dataframe,
                    int(user["user_id"]),
                )

                if inserted > 0:
                    st.success(f"{inserted} transaction(s) imported successfully.")

                if errors:
                    with st.expander(f"View {len(errors)} import issue(s)"):
                        for error in errors:
                            st.write(f"- {error}")

        except Exception as error:
            st.error(f"Could not read this CSV file: {error}")


def budget_planner_page() -> None:
    user = get_user()
    hero(
        "Budget planner",
        "Set spending limits by category and use the dashboard to stay in control throughout the month.",
        "🎯",
    )

    selected_month_date = st.date_input(
        "Choose a month",
        value=date.today().replace(day=1),
    )
    selected_month = month_key(selected_month_date)

    expense_categories = get_categories("Expense")

    set_col, overview_col = st.columns([1, 1.35])

    with set_col:
        section_title(
            "Set or update a budget",
            f"Budget month: {selected_month_date.strftime('%B %Y')}",
        )

        with st.form("budget_form", clear_on_submit=True):
            budget_category = st.selectbox(
                "Expense category",
                expense_categories["category_name"].tolist(),
            )

            budget_limit = st.number_input(
                "Monthly budget limit (₹)",
                min_value=0.0,
                value=1000.0,
                step=100.0,
            )

            budget_submit = st.form_submit_button(
                "Save budget",
                type="primary",
                use_container_width=True,
            )

        if budget_submit:
            save_budget(
                user_id=int(user["user_id"]),
                category_name=budget_category,
                budget_month=selected_month,
                budget_limit=float(budget_limit),
            )
            st.success(
                f"Budget saved for {budget_category}: "
                f"{format_currency(float(budget_limit), user['currency'])}"
            )
            st.rerun()

    with overview_col:
        month_start, month_end = get_month_bounds(selected_month_date)
        transactions = get_transactions(
            start_date=month_start.isoformat(),
            end_date=month_end.isoformat(),
        )
        budgets = get_budgets(selected_month)
        budget_status = calculate_budget_status(budgets, transactions)

        total_budget = float(
            budget_status["budget_limit"].sum()
        ) if not budget_status.empty else 0.0

        total_spent = float(
            budget_status["actual_spend"].sum()
        ) if not budget_status.empty else 0.0

        overall_remaining = total_budget - total_spent

        overall_columns = st.columns(3)

        with overall_columns[0]:
            metric_card(
                "Total budget",
                format_currency(total_budget, user["currency"]),
                "Across configured categories",
            )

        with overall_columns[1]:
            metric_card(
                "Budgeted spend",
                format_currency(total_spent, user["currency"]),
                "Actual spending in budgeted categories",
            )

        with overall_columns[2]:
            metric_card(
                "Remaining",
                format_currency(overall_remaining, user["currency"]),
                "Negative means budget exceeded",
            )

    st.write("")
    section_title(
        "Category budget status",
        "Review categories in red and orange first—they need attention.",
    )

    if budget_status.empty:
        st.info("No budgets are set for this month yet.")
    else:
        left_col, right_col = st.columns([1, 1.4])

        with left_col:
            for _, row in budget_status.iterrows():
                budget_card(
                    category=str(row["category_name"]),
                    budget=float(row["budget_limit"]),
                    spent=float(row["actual_spend"]),
                    remaining=float(row["remaining"]),
                    usage=float(row["usage_percentage"]),
                    status=str(row["status"]),
                    icon=str(row["icon"]),
                )

                st.progress(
                    min(float(row["usage_percentage"]) / 100, 1.0)
                )

        with right_col:
            st.plotly_chart(
                budget_vs_spending_chart(budget_status),
                use_container_width=True,
            )

            table_data = budget_status.copy()
            table_data["Budget"] = table_data["budget_limit"].apply(
                lambda value: format_currency(float(value), user["currency"])
            )
            table_data["Spent"] = table_data["actual_spend"].apply(
                lambda value: format_currency(float(value), user["currency"])
            )
            table_data["Remaining"] = table_data["remaining"].apply(
                lambda value: format_currency(float(value), user["currency"])
            )
            table_data["Usage"] = table_data["usage_percentage"].apply(
                lambda value: f"{float(value):.1f}%"
            )

            st.dataframe(
                table_data[
                    [
                        "icon",
                        "category_name",
                        "Budget",
                        "Spent",
                        "Remaining",
                        "Usage",
                        "status",
                    ]
                ].rename(
                    columns={
                        "icon": "",
                        "category_name": "Category",
                        "status": "Status",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

        st.divider()
        section_title(
            "Remove budget",
            "You can remove an unwanted category budget here.",
        )

        selected_budget_id = st.selectbox(
            "Choose a saved budget",
            budget_status["budget_id"].tolist(),
            format_func=lambda budget_id: (
                budget_status[
                    budget_status["budget_id"] == budget_id
                ].iloc[0]["category_name"]
            ),
        )

        confirm_budget_delete = st.checkbox(
            "I want to remove this budget.",
        )

        if st.button(
            "Remove selected budget",
            disabled=not confirm_budget_delete,
        ):
            delete_budget(int(selected_budget_id))
            st.success("Budget removed.")
            st.rerun()


def savings_goals_page() -> None:
    user = get_user()
    hero(
        "Savings goals",
        "Turn financial discipline into progress toward the things that matter to you.",
        "🏆",
    )

    add_col, goals_col = st.columns([1, 1.35])

    with add_col:
        section_title(
            "Create a savings goal",
            "Examples: Laptop Fund, Emergency Fund, Travel Fund, Course Fee.",
        )

        with st.form("goal_form", clear_on_submit=True):
            goal_name = st.text_input(
                "Goal name",
                placeholder="Example: Buy a laptop",
            )

            target_amount = st.number_input(
                "Target amount (₹)",
                min_value=1.0,
                value=25000.0,
                step=500.0,
            )

            current_amount = st.number_input(
                "Amount already saved (₹)",
                min_value=0.0,
                value=0.0,
                step=100.0,
            )

            target_date = st.date_input(
                "Target date",
                value=date.today() + timedelta(days=180),
            )

            goal_status = st.selectbox(
                "Goal status",
                ["Active", "Paused", "Completed"],
            )

            goal_submit = st.form_submit_button(
                "Create savings goal",
                type="primary",
                use_container_width=True,
            )

        if goal_submit:
            if not goal_name.strip():
                st.warning("Please provide a name for the savings goal.")
            elif current_amount > target_amount:
                st.warning("Current savings cannot exceed the target amount.")
            else:
                add_goal(
                    user_id=int(user["user_id"]),
                    goal_name=goal_name,
                    target_amount=float(target_amount),
                    current_amount=float(current_amount),
                    target_date=target_date.isoformat(),
                    status=goal_status,
                )
                st.success("Savings goal created.")
                st.rerun()

    with goals_col:
        section_title(
            "Your goal progress",
            "Update your saved amount whenever you contribute more money.",
        )

        goals = get_goals()

        if goals.empty:
            st.info("No savings goals yet. Create your first goal from the left panel.")
        else:
            for _, goal in goals.iterrows():
                progress = min(
                    float(goal["current_amount"]) / float(goal["target_amount"]),
                    1.0,
                )

                goal_status = str(goal["status"])
                target_date_text = (
                    goal["target_date"].strftime("%d %b %Y")
                    if pd.notna(goal["target_date"])
                    else "No target date"
                )

                with st.container(border=True):
                    goal_header_col, goal_status_col = st.columns([3, 1])

                    with goal_header_col:
                        st.markdown(f"### 🎯 {goal['goal_name']}")
                        st.caption(
                            f"Target date: {target_date_text}"
                        )

                    with goal_status_col:
                        st.markdown(
                            f"<br>{status_badge(goal_status)}",
                            unsafe_allow_html=True,
                        )

                    st.progress(progress)

                    goal_metric_col_1, goal_metric_col_2, goal_metric_col_3 = st.columns(3)

                    with goal_metric_col_1:
                        st.metric(
                            "Saved",
                            format_currency(
                                float(goal["current_amount"]),
                                user["currency"],
                            ),
                        )

                    with goal_metric_col_2:
                        st.metric(
                            "Target",
                            format_currency(
                                float(goal["target_amount"]),
                                user["currency"],
                            ),
                        )

                    with goal_metric_col_3:
                        st.metric(
                            "Progress",
                            f"{progress * 100:.1f}%",
                        )

                    with st.expander("Update this goal"):
                        new_amount = st.number_input(
                            "Updated saved amount (₹)",
                            min_value=0.0,
                            value=float(goal["current_amount"]),
                            step=100.0,
                            key=f"goal_amount_{goal['goal_id']}",
                        )

                        new_status = st.selectbox(
                            "Status",
                            ["Active", "Paused", "Completed"],
                            index=[
                                "Active",
                                "Paused",
                                "Completed",
                            ].index(goal_status),
                            key=f"goal_status_{goal['goal_id']}",
                        )

                        if st.button(
                            "Save goal update",
                            key=f"save_goal_{goal['goal_id']}",
                            type="primary",
                        ):
                            if new_amount > float(goal["target_amount"]):
                                st.warning(
                                    "Saved amount cannot be more than the target amount."
                                )
                            else:
                                final_status = (
                                    "Completed"
                                    if new_amount >= float(goal["target_amount"])
                                    else new_status
                                )
                                update_goal_amount(
                                    int(goal["goal_id"]),
                                    float(new_amount),
                                    final_status,
                                )
                                st.success("Goal updated.")
                                st.rerun()

                        confirm_delete_goal = st.checkbox(
                            "I want to permanently delete this goal.",
                            key=f"delete_confirm_{goal['goal_id']}",
                        )

                        if st.button(
                            "Delete this goal",
                            key=f"delete_goal_{goal['goal_id']}",
                            disabled=not confirm_delete_goal,
                        ):
                            delete_goal(int(goal["goal_id"]))
                            st.success("Goal deleted.")
                            st.rerun()


def reports_page() -> None:
    user = get_user()
    hero(
        "Reports and deeper analytics",
        "Use longer time periods to discover trends and export a complete financial record.",
        "📊",
    )

    report_start, report_end = month_filter_widget("reports")

    transactions = get_transactions(
        start_date=report_start.isoformat(),
        end_date=report_end.isoformat(),
    )

    kpis = calculate_kpis(transactions)

    report_metric_columns = st.columns(4)

    with report_metric_columns[0]:
        metric_card(
            "Income",
            format_currency(float(kpis["income"]), user["currency"]),
            "For selected report period",
        )

    with report_metric_columns[1]:
        metric_card(
            "Expenses",
            format_currency(float(kpis["expense"]), user["currency"]),
            "For selected report period",
        )

    with report_metric_columns[2]:
        metric_card(
            "Net balance",
            format_currency(float(kpis["balance"]), user["currency"]),
            "Income minus expense",
        )

    with report_metric_columns[3]:
        metric_card(
            "Total records",
            str(len(transactions)),
            "Income and expense entries",
        )

    monthly_summary = get_monthly_summary(transactions)

    st.plotly_chart(
        monthly_summary_chart(monthly_summary),
        use_container_width=True,
    )

    if not transactions.empty:
        expense_data = transactions[
            transactions["transaction_type"] == "Expense"
        ].copy()

        summary_by_category = (
            expense_data.groupby("category_name", as_index=False)["amount"]
            .sum()
            .sort_values("amount", ascending=False)
        )

        section_title(
            "Category expense report",
            "Compare your largest expense categories during the selected period.",
        )

        if summary_by_category.empty:
            st.info("No expense records in the selected period.")
        else:
            summary_by_category["Amount"] = summary_by_category["amount"].apply(
                lambda value: format_currency(float(value), user["currency"])
            )

            total_expense = float(expense_data["amount"].sum())
            summary_by_category["Share of expenses"] = summary_by_category["amount"].apply(
                lambda value: (
                    f"{(float(value) / total_expense * 100):.1f}%"
                    if total_expense > 0
                    else "0.0%"
                )
            )

            st.dataframe(
                summary_by_category[
                    ["category_name", "Amount", "Share of expenses"]
                ].rename(
                    columns={
                        "category_name": "Category",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

        st.divider()
        section_title(
            "Download report data",
            "Export your selected transactions and keep a personal monthly record.",
        )

        report_export = transactions.copy()
        report_export["transaction_date"] = report_export["transaction_date"].dt.strftime(
            "%Y-%m-%d"
        )

        st.download_button(
            "⬇️ Download detailed CSV report",
            data=report_export.to_csv(index=False).encode("utf-8"),
            file_name=(
                f"spendwise_report_{report_start.isoformat()}_to_"
                f"{report_end.isoformat()}.csv"
            ),
            mime="text/csv",
            type="primary",
        )

        summary_export = monthly_summary.copy()
        st.download_button(
            "⬇️ Download monthly summary CSV",
            data=summary_export.to_csv(index=False).encode("utf-8"),
            file_name="spendwise_monthly_summary.csv",
            mime="text/csv",
        )
    else:
        st.info("Add transactions to generate downloadable reports.")


def settings_page() -> None:
    user = get_user()
    hero(
        "Profile and settings",
        "Customize your personal finance preferences and targets.",
        "⚙️",
    )

    settings_col, about_col = st.columns([1, 1])

    with settings_col:
        section_title(
            "Financial profile",
            "These values personalize your dashboard and saving strategy.",
        )

        with st.form("user_settings_form"):
            user_name = st.text_input(
                "Your name",
                value=str(user["name"]),
            )

            monthly_income = st.number_input(
                "Expected monthly income / allowance (₹)",
                min_value=0.0,
                value=float(user["monthly_income"]),
                step=500.0,
            )

            monthly_target = st.number_input(
                "Monthly savings target (₹)",
                min_value=0.0,
                value=float(user["monthly_savings_target"]),
                step=100.0,
            )

            current_currency = str(user["currency"])
            currency_index = (
                CURRENCIES.index(current_currency)
                if current_currency in CURRENCIES
                else 0
            )

            currency = st.selectbox(
                "Currency",
                CURRENCIES,
                index=currency_index,
            )

            profile_submitted = st.form_submit_button(
                "Save profile settings",
                type="primary",
                use_container_width=True,
            )

        if profile_submitted:
            update_user(
                name=user_name,
                monthly_income=float(monthly_income),
                monthly_savings_target=float(monthly_target),
                currency=currency,
            )
            st.success("Profile settings saved.")
            st.rerun()

    with about_col:
        section_title(
            "Your monthly plan",
            "A simple recommended spending limit based on your expected income and savings target.",
        )

        planned_spending = max(
            float(user["monthly_income"]) - float(user["monthly_savings_target"]),
            0,
        )

        metric_card(
            "Expected monthly income",
            format_currency(float(user["monthly_income"]), user["currency"]),
            "Allowance, salary, scholarship, or combined income",
        )

        st.write("")

        metric_card(
            "Savings target",
            format_currency(
                float(user["monthly_savings_target"]),
                user["currency"],
            ),
            "Set aside this amount before optional spending",
        )

        st.write("")

        metric_card(
            "Recommended spending ceiling",
            format_currency(planned_spending, user["currency"]),
            "Income minus your monthly savings target",
        )

        st.divider()
        st.info(
            "This app is an expense-tracking and budgeting tool. "
            "It does not provide investment, tax, or financial advice."
        )

    st.divider()
    section_title(
        "Project technology stack",
        "A short summary you can use in your college project documentation or GitHub README.",
    )

    st.markdown(
        """
        | Technology | Use in this project |
        |---|---|
        | Python | Application logic, calculations, data validation, and database operations |
        | Streamlit | Interactive multipage web dashboard and forms |
        | SQLite | Lightweight local database for transactions, budgets, and goals |
        | Pandas | Data analysis, aggregations, CSV import/export, and report creation |
        | Plotly | Interactive financial charts |
        | Git and GitHub | Version control, project collaboration, and portfolio hosting |
        """
    )


show_sidebar()

navigation = st.navigation(
    {
        "Overview": [
            st.Page(
                dashboard_page,
                title="Dashboard",
                icon="🏠",
                default=True,
            ),
        ],
        "Money management": [
            st.Page(
                add_transaction_page,
                title="Add transaction",
                icon="➕",
            ),
            st.Page(
                transactions_page,
                title="Transactions",
                icon="🧾",
            ),
            st.Page(
                budget_planner_page,
                title="Budget planner",
                icon="🎯",
            ),
            st.Page(
                savings_goals_page,
                title="Savings goals",
                icon="🏆",
            ),
        ],
        "Analysis": [
            st.Page(
                reports_page,
                title="Reports",
                icon="📊",
            ),
        ],
        "Account": [
            st.Page(
                settings_page,
                title="Settings",
                icon="⚙️",
            ),
        ],
    }
)

navigation.run()