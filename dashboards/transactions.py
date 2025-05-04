import streamlit as st
import pandas as pd
import plotly.express as px

def show_transactions_dashboard(transactions):
    st.subheader("Sales Transactions Overview")
    st.metric("Total Transactions", len(transactions))
    st.metric("Total Worth (AED)", f"{transactions['actual_worth'].sum():,.2f}")

    # Temporal Analysis
    monthly_volume = transactions.groupby(["year", "month"]).size().reset_index(name="transaction_count")
    fig = px.line(monthly_volume, x=pd.to_datetime(monthly_volume[["year", "month"]].assign(day=1)), y="transaction_count", title="Monthly Transaction Volume")
    st.plotly_chart(fig, use_container_width=True)

    # Area-wise Value Distribution
    area_worth = transactions.groupby("area_name_en")["actual_worth"].sum().nlargest(10)
    fig = px.bar(area_worth, title="Top 10 Areas by Transaction Worth")
    st.plotly_chart(fig, use_container_width=True)

    # Average Property Value
    avg_price = transactions["actual_worth"].mean()
    st.metric("Avg Property Price (AED)", f"{avg_price:,.2f}")

    # Interactive Filters
    years = sorted(transactions["year"].dropna().unique())
    areas = sorted(transactions["area_name_en"].dropna().unique())
    selected_year = st.selectbox("Filter by Year", options=years)
    selected_area = st.selectbox("Filter by Area", options=["All"] + areas)

    filtered_data = transactions.copy()
    if selected_year:
        filtered_data = filtered_data[filtered_data["year"] == selected_year]
    if selected_area != "All":
        filtered_data = filtered_data[filtered_data["area_name_en"] == selected_area]

    st.dataframe(filtered_data)

    # Outlier Detection
    st.subheader("Top 5 High-Value Transactions")
    st.dataframe(transactions.nlargest(5, "actual_worth")[["instance_date", "area_name_en", "actual_worth"]])

    st.subheader("Bottom 5 Transactions")
    st.dataframe(transactions.nsmallest(5, "actual_worth")[["instance_date", "area_name_en", "actual_worth"]]) 