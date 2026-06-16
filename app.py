import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json
import os
from datetime import datetime, date, timedelta
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Expense Tracker Pro",
    page_icon="💳",
    layout="wide"
)

st.title("💳 Expense Tracker Pro")
st.markdown("Track spending, set budgets and "
            "get alerts before you overspend.")
st.markdown("---")

DATA_FILE = "expenses.json"
BUDGET_FILE = "budgets.json"

def load_json(path, default):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

CATEGORIES = {
    "Food & Dining":   "🍔",
    "Groceries":       "🛒",
    "Transport":       "🚗",
    "Rent/Housing":    "🏠",
    "Utilities":       "💡",
    "Entertainment":   "🎬",
    "Shopping":        "🛍️",
    "Health":          "🏥",
    "Education":       "📚",
    "Subscriptions":   "📱",
    "Travel":          "✈️",
    "Other":           "📦"
}

if 'expenses' not in st.session_state:
    st.session_state.expenses = load_json(
        DATA_FILE, [])
if 'budgets' not in st.session_state:
    st.session_state.budgets = load_json(
        BUDGET_FILE, {
            cat: 0 for cat in CATEGORIES
        })

# Sidebar — Add expense
st.sidebar.header("➕ Add Expense")

exp_date = st.sidebar.date_input(
    "Date:", date.today())
exp_category = st.sidebar.selectbox(
    "Category:", list(CATEGORIES.keys()))
exp_amount = st.sidebar.number_input(
    "Amount (₹):", min_value=0.0,
    value=100.0, step=10.0)
exp_note = st.sidebar.text_input(
    "Note (optional):",
    placeholder="e.g. Lunch with friends")
exp_recurring = st.sidebar.checkbox(
    "Recurring monthly expense")

if st.sidebar.button("💾 Add Expense",
                     type="primary"):
    st.session_state.expenses.append({
        'date':      str(exp_date),
        'category':  exp_category,
        'amount':    exp_amount,
        'note':      exp_note,
        'recurring': exp_recurring,
        'added_at':  str(datetime.now())
    })
    save_json(DATA_FILE,
              st.session_state.expenses)
    st.sidebar.success("✅ Expense added!")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Set Budgets")
with st.sidebar.expander("Edit monthly budgets"):
    for cat in CATEGORIES:
        st.session_state.budgets[cat] = \
            st.number_input(
                f"{CATEGORIES[cat]} {cat}",
                min_value=0,
                value=int(
                    st.session_state
                    .budgets.get(cat, 0)),
                step=500,
                key=f"budget_{cat}"
            )
    if st.button("💾 Save Budgets"):
        save_json(BUDGET_FILE,
                  st.session_state.budgets)
        st.success("Budgets saved!")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "🎯 Budget Tracker",
    "📈 Trends",
    "📋 All Expenses",
    "🔁 Recurring"
])

if not st.session_state.expenses:
    st.info(
        "👈 Add your first expense using "
        "the sidebar!")
else:
    df = pd.DataFrame(
        st.session_state.expenses)
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')
    current_month = pd.Period(
        date.today(), freq='M')
    month_df = df[df['month'] ==
                  current_month]

    # Tab 1 — Dashboard
    with tab1:
        st.markdown("### 📊 This Month")

        total_spent  = month_df['amount'].sum()
        total_budget = sum(
            st.session_state.budgets.values())
        remaining    = total_budget - total_spent
        days_left    = (
            date.today().replace(
                day=28) + timedelta(days=4)
        ).replace(day=1) - timedelta(days=1)
        days_left    = (days_left.day -
                        date.today().day)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Spent This Month",
                  f"₹{total_spent:,.0f}")
        c2.metric("Total Budget",
                  f"₹{total_budget:,.0f}")
        c3.metric("Remaining",
                  f"₹{remaining:,.0f}",
                  delta_color="normal" if
                  remaining >= 0 else "inverse")
        c4.metric("Days Left in Month",
                  days_left)

        if total_budget > 0:
            pct = total_spent / total_budget
            if pct > 1:
                st.error(
                    f"⚠️ You've exceeded your "
                    f"budget by "
                    f"₹{abs(remaining):,.0f}!")
            elif pct > 0.8:
                st.warning(
                    f"⚠️ You've used "
                    f"{pct:.0%} of your "
                    f"monthly budget!")
            st.progress(min(pct, 1.0))

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            cat_spend = month_df.groupby(
                'category')['amount'].sum()\
                .sort_values(ascending=False)
            fig = px.pie(
                values=cat_spend.values,
                names=cat_spend.index,
                title='Spending by Category',
                color_discrete_sequence=
                    px.colors.qualitative.Set3
            )
            fig.update_layout(height=350)
            st.plotly_chart(
                fig, use_container_width=True)

        with col2:
            daily = month_df.groupby(
                month_df['date'].dt.date
            )['amount'].sum().reset_index()
            fig2 = px.bar(
                daily, x='date', y='amount',
                title='Daily Spending',
                color_discrete_sequence=
                    ['#3498db']
            )
            fig2.update_layout(
                height=350,
                template='plotly_white')
            st.plotly_chart(
                fig2, use_container_width=True)

    # Tab 2 — Budget Tracker
    with tab2:
        st.markdown("### 🎯 Budget vs Actual")

        budget_rows = []
        for cat, budget in \
                st.session_state.budgets.items():
            spent = month_df[
                month_df['category'] == cat
            ]['amount'].sum()
            budget_rows.append({
                'Category': f"{CATEGORIES[cat]} {cat}",
                'Budget':   budget,
                'Spent':    spent,
                'Remaining':budget - spent,
                'Used %':   (spent/budget*100)
                            if budget > 0 else 0
            })

        budget_df = pd.DataFrame(budget_rows)
        budget_df = budget_df[
            budget_df['Budget'] > 0]

        if len(budget_df) > 0:
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(
                name='Budget',
                x=budget_df['Category'],
                y=budget_df['Budget'],
                marker_color='#bdc3c7'
            ))
            fig3.add_trace(go.Bar(
                name='Spent',
                x=budget_df['Category'],
                y=budget_df['Spent'],
                marker_color=[
                    '#e74c3c' if s > b
                    else '#2ecc71'
                    for s, b in zip(
                        budget_df['Spent'],
                        budget_df['Budget'])
                ]
            ))
            fig3.update_layout(
                title='Budget vs Actual '
                      'Spending',
                barmode='group',
                height=400,
                template='plotly_white'
            )
            st.plotly_chart(
                fig3,
                use_container_width=True)

            st.dataframe(
                budget_df,
                use_container_width=True,
                hide_index=True)
        else:
            st.info(
                "Set budgets in the sidebar "
                "to track them here!")

    # Tab 3 — Trends
    with tab3:
        st.markdown("### 📈 Spending Trends")

        monthly = df.groupby(
            df['month'].astype(str)
        )['amount'].sum().reset_index()
        monthly.columns = ['Month', 'Total']

        fig4 = px.line(
            monthly, x='Month', y='Total',
            title='Monthly Spending Trend',
            markers=True
        )
        fig4.update_layout(
            height=350,
            template='plotly_white')
        st.plotly_chart(
            fig4, use_container_width=True)

        cat_trend = df.groupby(
            [df['month'].astype(str),
             'category']
        )['amount'].sum().reset_index()
        fig5 = px.bar(
            cat_trend, x='month', y='amount',
            color='category',
            title='Category Spending Over Time',
            barmode='stack'
        )
        fig5.update_layout(
            height=400,
            template='plotly_white')
        st.plotly_chart(
            fig5, use_container_width=True)

    # Tab 4 — All Expenses
    with tab4:
        st.markdown("### 📋 All Expenses")
        display = df.sort_values(
            'date', ascending=False)[[
            'date', 'category', 'amount',
            'note'
        ]].copy()
        display['date'] = display['date']\
            .dt.strftime('%d %b %Y')
        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True)
        st.download_button(
            "⬇️ Download CSV",
            df.to_csv(index=False),
            "expenses.csv", "text/csv")

    # Tab 5 — Recurring
    with tab5:
        st.markdown("### 🔁 Recurring Expenses")
        recurring = df[df['recurring'] == True]
        if len(recurring) > 0:
            monthly_recurring = recurring\
                .groupby('category')[
                'amount'].mean()
            st.metric(
                "Total Monthly Recurring",
                f"₹{monthly_recurring.sum():,.0f}")
            st.dataframe(
                monthly_recurring.reset_index(),
                use_container_width=True,
                hide_index=True)
        else:
            st.info(
                "No recurring expenses "
                "marked yet!")

st.markdown("---")
st.markdown(
    "Built by **Jyotiraditya** | "
    "Expense Tracker Pro | "
    "Phase 3 Day 4 — Personal Finance"
)