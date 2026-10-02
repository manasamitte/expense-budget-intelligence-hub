from __future__ import annotations

import streamlit as st


def configure_page() -> None:
    st.set_page_config(
        page_title="SpendWise | Budget Intelligence Hub",
        page_icon="💸",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');

            html, body, [class*="css"] {
                font-family: 'Inter', sans-serif;
            }

            .stApp {
                background:
                    radial-gradient(circle at 5% 5%, rgba(108, 99, 255, 0.10), transparent 24rem),
                    radial-gradient(circle at 95% 10%, rgba(0, 194, 168, 0.10), transparent 24rem),
                    #F8FAFC;
            }

            #MainMenu,
            footer,
            header {
                visibility: hidden;
            }

            .block-container {
                padding-top: 1.25rem;
                padding-bottom: 2rem;
                max-width: 1500px;
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #111827 0%, #172554 100%);
            }

            [data-testid="stSidebar"] * {
                color: #F8FAFC;
            }

            [data-testid="stSidebarNav"] a {
                border-radius: 10px;
                margin: 0.12rem 0.45rem;
                padding: 0.45rem 0.6rem;
            }

            [data-testid="stSidebarNav"] a:hover {
                background-color: rgba(255,255,255,0.12);
            }

            .hero-card {
                background: linear-gradient(125deg, #312E81 0%, #4F46E5 48%, #14B8A6 120%);
                border-radius: 24px;
                color: #FFFFFF;
                padding: 2rem 2.1rem;
                margin-bottom: 1.2rem;
                box-shadow: 0 18px 45px rgba(79, 70, 229, 0.22);
            }

            .hero-card h1 {
                font-family: 'Space Grotesk', sans-serif;
                font-size: 2.15rem;
                line-height: 1.15;
                margin: 0;
                letter-spacing: -0.035em;
            }

            .hero-card p {
                font-size: 1.02rem;
                margin: 0.65rem 0 0 0;
                color: rgba(255,255,255,0.88);
            }

            .section-title {
                font-family: 'Space Grotesk', sans-serif;
                color: #0F172A;
                font-size: 1.3rem;
                font-weight: 700;
                margin-top: 1rem;
                margin-bottom: 0.25rem;
            }

            .section-subtitle {
                color: #64748B;
                margin-bottom: 1rem;
            }

            .metric-card {
                background: rgba(255,255,255,0.96);
                border: 1px solid #E2E8F0;
                border-radius: 18px;
                padding: 1.05rem 1.15rem;
                min-height: 118px;
                box-shadow: 0 7px 20px rgba(15, 23, 42, 0.05);
            }

            .metric-label {
                color: #64748B;
                font-size: 0.82rem;
                font-weight: 600;
                margin-bottom: 0.45rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            .metric-value {
                color: #0F172A;
                font-family: 'Space Grotesk', sans-serif;
                font-size: 1.75rem;
                font-weight: 700;
                line-height: 1.1;
            }

            .metric-note {
                color: #64748B;
                font-size: 0.78rem;
                margin-top: 0.45rem;
            }

            .panel-card {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 18px;
                padding: 1rem 1.1rem;
                box-shadow: 0 7px 20px rgba(15, 23, 42, 0.04);
            }

            .budget-card {
                border: 1px solid #E2E8F0;
                border-left: 6px solid #6C63FF;
                border-radius: 14px;
                background: #FFFFFF;
                padding: 0.9rem 1rem;
                margin-bottom: 0.75rem;
                box-shadow: 0 5px 15px rgba(15, 23, 42, 0.035);
            }

            .budget-card h4 {
                margin: 0 0 0.4rem 0;
                color: #0F172A;
            }

            .budget-card p {
                color: #475569;
                margin: 0.18rem 0;
                font-size: 0.9rem;
            }

            .status-safe {
                color: #047857;
                font-weight: 700;
            }

            .status-watch {
                color: #B45309;
                font-weight: 700;
            }

            .status-near {
                color: #C2410C;
                font-weight: 700;
            }

            .status-exceeded {
                color: #DC2626;
                font-weight: 700;
            }

            .small-muted {
                color: #64748B;
                font-size: 0.88rem;
            }

            .stButton > button,
            .stDownloadButton > button {
                border-radius: 10px;
                font-weight: 600;
                border: 0;
                padding: 0.55rem 1rem;
            }

            .stButton > button[kind="primary"] {
                background: linear-gradient(90deg, #4F46E5, #06B6D4);
                color: white;
            }

            .stButton > button[kind="primary"]:hover {
                background: linear-gradient(90deg, #4338CA, #0891B2);
                color: white;
            }

            [data-testid="stMetric"] {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                padding: 0.9rem;
                border-radius: 14px;
            }

            div[data-testid="stDataFrame"] {
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                overflow: hidden;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, icon: str = "💸") -> None:
    st.markdown(
        f"""
        <div class="hero-card">
            <h1>{icon} {title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str, subtitle: str | None = None) -> None:
    st.markdown(
        f'<div class="section-title">{title}</div>',
        unsafe_allow_html=True,
    )

    if subtitle:
        st.markdown(
            f'<div class="section-subtitle">{subtitle}</div>',
            unsafe_allow_html=True,
        )


def metric_card(
    label: str,
    value: str,
    note: str = "",
) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def budget_card(
    category: str,
    budget: float,
    spent: float,
    remaining: float,
    usage: float,
    status: str,
    icon: str = "📌",
) -> None:
    status_class = {
        "Safe": "status-safe",
        "Watch": "status-watch",
        "Near limit": "status-near",
        "Exceeded": "status-exceeded",
    }.get(status, "status-safe")

    remaining_text = (
        f"₹{remaining:,.0f} remaining"
        if remaining >= 0
        else f"₹{abs(remaining):,.0f} over budget"
    )

    st.markdown(
        f"""
        <div class="budget-card">
            <h4>{icon} {category}</h4>
            <p>Spent <b>₹{spent:,.0f}</b> of ₹{budget:,.0f}</p>
            <p>{remaining_text} · <span class="{status_class}">{status}</span></p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_insight(title: str, message: str, level: str) -> None:
    text = f"**{title}:** {message}"

    if level == "success":
        st.success(text)
    elif level == "warning":
        st.warning(text)
    elif level == "error":
        st.error(text)
    else:
        st.info(text)