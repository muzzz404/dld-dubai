import streamlit as st
import pandas as pd
import plotly.express as px

def show_area_analytics_dashboard(transactions):
    st.subheader("Detailed Area & Property Breakdown")

    # Filters
    selected_areas = st.multiselect("Select Areas", options=sorted(transactions["area_name_en"].dropna().unique()))
    filtered_area_data = transactions[transactions["area_name_en"].isin(selected_areas)] if selected_areas else transactions

    # Metrics
    st.metric("Average Sale Value", f"{filtered_area_data['actual_worth'].mean():,.2f} AED")
    st.metric("Median Sale Value", f"{filtered_area_data['actual_worth'].median():,.2f} AED")
    st.metric("Top Sale Value", f"{filtered_area_data['actual_worth'].max():,.2f} AED")
    st.metric("Least Sale Value", f"{filtered_area_data['actual_worth'].min():,.2f} AED")

    # Area Sales Trend
    if not filtered_area_data.empty:
        trend = filtered_area_data.groupby(["year", "month"])["actual_worth"].sum().reset_index()
        fig = px.line(trend, x=pd.to_datetime(trend[["year", "month"]].assign(day=1)), y="actual_worth", title="Monthly Sales Trend for Selected Areas")
        st.plotly_chart(fig, use_container_width=True)

    # Top Buildings
    if "building_name_en" in filtered_area_data.columns:
        building_worth = filtered_area_data.groupby("building_name_en")["actual_worth"].sum().nlargest(10)
        fig = px.bar(building_worth, title="Top Buildings by Sales")
        st.plotly_chart(fig, use_container_width=True)

    # Top Projects
    if "project_name_en" in filtered_area_data.columns:
        project_worth = filtered_area_data.groupby("project_name_en")["actual_worth"].sum().nlargest(10)
        fig = px.bar(project_worth, title="Top Projects by Sales")
        st.plotly_chart(fig, use_container_width=True)

    # Full Table
    st.dataframe(filtered_area_data.sort_values(by="actual_worth", ascending=False)) 