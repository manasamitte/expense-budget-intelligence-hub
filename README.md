# SpendWise — Student / Personal Expense & Budget Intelligence Hub

SpendWise is an interactive personal-finance web application built with Python, Streamlit, SQLite, Pandas, and Plotly.

It helps students and individuals track income and expenses, set category budgets, monitor savings goals, analyze spending patterns, and export financial reports.

## Features

- Add income and expense transactions
- Category-wise expense tracking
- SQLite database storage
- Monthly category budgets
- Budget warning and overspending alerts
- Interactive Plotly charts
- Transaction search, filters, updates, and deletion
- CSV import and CSV export
- Savings-goal tracker
- Financial summaries and smart spending insights
- Custom profile, monthly income, and savings target

## Tech Stack

- Python
- Streamlit
- SQLite
- Pandas
- Plotly
- Git and GitHub

## Installation

```bash
git clone <your-repository-url>
cd expense_budget_hub
python -m venv .venv
```

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
source .venv/bin/activate
```

Install packages:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
streamlit run app.py
```

## Project Structure

```text
expense_budget_hub/
├── app.py
├── requirements.txt
├── README.md
├── database/
├── data/
└── src/
    ├── analytics.py
    ├── charts.py
    ├── database.py
    └── ui.py
```

## Database Tables

- `users`
- `categories`
- `transactions`
- `budgets`
- `savings_goals`

## Future Improvements

- User authentication and multi-user accounts
- Receipt image upload with OCR
- PDF report generation
- Automatic expense categorization
- Spending prediction
- Email reminders and budget alerts
- Cloud database deployment