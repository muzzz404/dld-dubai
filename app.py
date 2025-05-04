# streamlit_dashboard.py
import streamlit as st
import os
from auth import custom_login
from data_loader import load_data
from dashboards.transactions import show_transactions_dashboard
from dashboards.rentals import show_rentals_dashboard
from dashboards.area_analytics import show_area_analytics_dashboard
from dashboards.sales import show_sales_dashboard
from dashboards.comparing import show_comparing_dashboard

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'name' not in st.session_state:
    st.session_state['name'] = None

st.set_page_config(
    page_title="Real Estate Dashboard", 
    layout="wide",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Main app
if custom_login():
    st.title("🏠 Real Estate Analytics Dashboard")

    # Load data only when logged in
    transactions, rentals = load_data()

    # Dashboard Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Transactions", "📈 Rentals", "📍 Area Analytics", "💰 Sales Dashboard", "⚖️ Comparing Dashboard"])

    with tab1:
        show_transactions_dashboard(transactions)

    with tab2:
        show_rentals_dashboard(rentals)

    with tab3:
        show_area_analytics_dashboard(transactions)

    with tab4:
        show_sales_dashboard(transactions)
        
    with tab5:
        show_comparing_dashboard(transactions, rentals)
