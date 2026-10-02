from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


COLORS = [
    "#6C63FF",
    "#00C2A8",
    "#FFB703",
    "#EF476F",
    "#118AB2",
    "#8338EC",
    "#FB8500",
    "#3A86FF",
    "#06D6A0",
    "#8E9AAF",
]


def empty_figure(message: str) -> go.Figure:
    figure = go.Figure()
    figure.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        showarrow=False,
        font={"size": 16, "color": "#94A3B8"},
    )
    figure.update_layout(
        height=340,
        template="plotly_white",
        xaxis={"visible": False},
        yaxis={"visible": False},
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    return figure


def apply_layout(figure: go.Figure, height: int = 360) -> go.Figure:
    figure.update_layout(
        height=height,
        template="plotly_white",
        margin={"l": 20, "r": 20, "t": 45, "b": 20},
        paper_bgcolor="white",
        plot_bgcolor="white",
        font={"family": "Inter, Arial, sans-serif", "color": "#1E293B"},
        legend={"orientation": "h", "y": -0.18},
    )

    figure.update_xaxes(
        showgrid=False,
        linecolor="#E2E8F0",
    )

    figure.update_yaxes(
        gridcolor="#F1F5F9",
        zerolinecolor="#E2E8F0",
    )

    return figure


def category_expense_chart(transactions: pd.DataFrame) -> go.Figure:
    expense_data = transactions[
        transactions["transaction_type"] == "Expense"
    ].copy()

    if expense_data.empty:
        return empty_figure("No expense data is available for this period.")

    grouped = (
        expense_data.groupby(["category_name", "color"], as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    )

    figure = px.pie(
        grouped,
        names="category_name",
        values="amount",
        hole=0.62,
        color="category_name",
        color_discrete_sequence=COLORS,
    )

    figure.update_traces(
        textposition="inside",
        textinfo="percent",
        hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>",
    )

    figure.update_layout(
        title="Expense distribution",
        annotations=[
            {
                "text": "Expenses",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 18, "color": "#475569"},
            }
        ],
    )

    return apply_layout(figure, 360)


def daily_cashflow_chart(transactions: pd.DataFrame) -> go.Figure:
    if transactions.empty:
        return empty_figure("Add transactions to view your cashflow trend.")

    grouped = (
        transactions.groupby(
            ["transaction_date", "transaction_type"],
            as_index=False,
        )["amount"]
        .sum()
    )

    figure = px.line(
        grouped,
        x="transaction_date",
        y="amount",
        color="transaction_type",
        markers=True,
        color_discrete_map={
            "Income": "#00B894",
            "Expense": "#EF476F",
        },
    )

    figure.update_traces(
        hovertemplate="%{x|%d %b %Y}<br>₹%{y:,.0f}<extra></extra>"
    )

    figure.update_layout(
        title="Daily cashflow",
        xaxis_title="Date",
        yaxis_title="Amount (₹)",
    )

    return apply_layout(figure, 360)


def budget_vs_spending_chart(budget_status: pd.DataFrame) -> go.Figure:
    if budget_status.empty:
        return empty_figure("Set category budgets to compare spending against them.")

    chart_data = budget_status.melt(
        id_vars=["category_name"],
        value_vars=["budget_limit", "actual_spend"],
        var_name="Metric",
        value_name="Amount",
    )

    chart_data["Metric"] = chart_data["Metric"].replace(
        {
            "budget_limit": "Budget",
            "actual_spend": "Spent",
        }
    )

    figure = px.bar(
        chart_data,
        x="category_name",
        y="Amount",
        color="Metric",
        barmode="group",
        color_discrete_map={
            "Budget": "#CBD5E1",
            "Spent": "#6C63FF",
        },
    )

    figure.update_traces(
        hovertemplate="<b>%{x}</b><br>%{fullData.name}: ₹%{y:,.0f}<extra></extra>"
    )

    figure.update_layout(
        title="Budget versus actual spending",
        xaxis_title="Category",
        yaxis_title="Amount (₹)",
    )

    return apply_layout(figure, 370)


def payment_method_chart(transactions: pd.DataFrame) -> go.Figure:
    expense_data = transactions[
        transactions["transaction_type"] == "Expense"
    ].copy()

    if expense_data.empty:
        return empty_figure("No expense data is available for payment analysis.")

    grouped = (
        expense_data.groupby("payment_method", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=True)
    )

    figure = px.bar(
        grouped,
        x="amount",
        y="payment_method",
        orientation="h",
        color="payment_method",
        color_discrete_sequence=COLORS,
    )

    figure.update_traces(
        hovertemplate="<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>"
    )

    figure.update_layout(
        title="Expenses by payment method",
        xaxis_title="Amount (₹)",
        yaxis_title="",
        showlegend=False,
    )

    return apply_layout(figure, 360)


def monthly_summary_chart(monthly_summary: pd.DataFrame) -> go.Figure:
    if monthly_summary.empty:
        return empty_figure("Add transactions across months to view a monthly comparison.")

    chart_data = monthly_summary.melt(
        id_vars=["month"],
        value_vars=["income", "expense", "balance"],
        var_name="Metric",
        value_name="Amount",
    )

    chart_data["Metric"] = chart_data["Metric"].replace(
        {
            "income": "Income",
            "expense": "Expense",
            "balance": "Balance",
        }
    )

    figure = px.bar(
        chart_data,
        x="month",
        y="Amount",
        color="Metric",
        barmode="group",
        color_discrete_map={
            "Income": "#00B894",
            "Expense": "#EF476F",
            "Balance": "#6C63FF",
        },
    )

    figure.update_traces(
        hovertemplate="<b>%{x}</b><br>%{fullData.name}: ₹%{y:,.0f}<extra></extra>"
    )

    figure.update_layout(
        title="Monthly financial summary",
        xaxis_title="Month",
        yaxis_title="Amount (₹)",
    )

    return apply_layout(figure, 380)