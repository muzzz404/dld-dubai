import streamlit as st
import pandas as pd
import os
import numpy as np

# Load data efficiently using Parquet format with better caching and performance options
@st.cache_data(ttl=3600*24)  # Cache for 24 hours
def load_data(sample_size=None):
    """
    Load transaction and rental data with optimized performance
    
    Parameters:
    - sample_size: If provided, return a random sample of this size for faster development/testing
    """
    transactions_file = "transactions.parquet"
    rentals_file = "rentals.parquet"

    # Check for parquet files and create them if needed
    if not os.path.exists(transactions_file):
        st.info("Converting transactions CSV to optimized Parquet format (one-time operation)...")
        # Read CSV with date parsing and handle invalid dates
        raw_transactions = pd.read_csv(
            "transactions.csv", 
            usecols=["instance_date", "procedure_name_en", "property_type_en", "property_usage_en", 
                    "reg_type_en", "area_name_en", "building_name_en", "project_name_en", 
                    "master_project_en", "nearest_metro_en", "nearest_landmark_en", 
                    "nearest_mall_en", "rooms_en", "has_parking", "procedure_area", 
                    "actual_worth", "meter_sale_price"]
        )
        # Convert dates with error handling
        raw_transactions["instance_date"] = pd.to_datetime(raw_transactions["instance_date"], dayfirst=True, errors='coerce')
        # Remove rows with invalid dates
        raw_transactions = raw_transactions.dropna(subset=["instance_date"])
        raw_transactions.to_parquet(transactions_file)

    if not os.path.exists(rentals_file):
        st.info("Converting rentals CSV to optimized Parquet format (one-time operation)...")
        raw_rentals = pd.read_csv(
            "rentals.csv", 
            usecols=["area_name_en", "annual_amount", "contract_amount", "ejari_bus_property_type_en", 
                    "ejari_property_type_en", "ejari_property_sub_type_en", "contract_start_date", 
                    "contract_end_date", "contract_reg_type_en", "property_usage_en", 
                    "project_name_en", "master_project_en", "area_name_en", "actual_area", 
                    "nearest_landmark_en", "nearest_metro_en", "nearest_mall_en", "tenant_type_en"]
        )
        raw_rentals.to_parquet(rentals_file)

    # Load data from parquet (much faster than CSV)
    transactions = pd.read_parquet(transactions_file)
    # Double-check date parsing - just in case
    transactions["instance_date"] = pd.to_datetime(transactions["instance_date"], errors='coerce')
    transactions = transactions.dropna(subset=["instance_date"])
    
    # Add derived columns for analysis
    transactions["year"] = transactions["instance_date"].dt.year
    transactions["month"] = transactions["instance_date"].dt.month
    
    rentals = pd.read_parquet(rentals_file)

    # Take a random sample if requested (for faster development/testing)
    if sample_size is not None:
        if len(transactions) > sample_size:
            transactions = transactions.sample(sample_size, random_state=42)
        if len(rentals) > sample_size:
            rentals = rentals.sample(sample_size, random_state=42)

    return transactions, rentals

# Function for lazy loading - load data only when needed
def get_data(use_sample=False):
    """
    Lazy loading function that only loads data when needed.
    For development, use a sample of the data to speed up iteration time.
    """
    if "transactions" not in st.session_state or "rentals" not in st.session_state:
        sample_size = 10000 if use_sample else None
        st.session_state.transactions, st.session_state.rentals = load_data(sample_size)
    
    return st.session_state.transactions, st.session_state.rentals 