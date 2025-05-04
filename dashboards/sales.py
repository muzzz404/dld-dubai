import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import format_currency, calculate_statistics
import numpy as np
from datetime import datetime, timedelta

def create_mapbox_visualization(filtered_data, color_column='actual_worth', size_column='actual_worth', 
                               title="Property Price Distribution Map"):
    """
    Create a mapbox scatter plot of properties
    
    Parameters:
    - filtered_data: DataFrame with latitude and longitude columns
    - color_column: Column to use for color scale
    - size_column: Column to use for point size
    """
    # Check if required columns exist
    if 'latitude' not in filtered_data.columns or 'longitude' not in filtered_data.columns:
        st.warning("Map visualization requires latitude and longitude data, which is missing from the dataset.")
        return None
    
    # Create the scatter mapbox
    fig = px.scatter_mapbox(
        filtered_data, 
        lat='latitude', 
        lon='longitude',
        color=color_column,
        size=filtered_data[size_column] / filtered_data[size_column].max() * 20,  # Normalize size
        color_continuous_scale=px.colors.sequential.Viridis,
        hover_name='area_name_en',
        hover_data={
            'property_type_en': True,
            'actual_worth': ':,.2f AED',
            'meter_sale_price': ':,.2f AED/m²',
            'latitude': False,
            'longitude': False
        },
        zoom=10,
        height=600,
        title=title
    )
    
    # Update layout
    fig.update_layout(
        mapbox_style="open-street-map",  # Use open street map as default (no token required)
        margin={"r": 0, "t": 50, "l": 0, "b": 0}
    )
    
    return fig

def calculate_roi(purchase_price, annual_rent, annual_expenses_percent=0.2, vacancy_rate=0.05):
    """
    Calculate Return on Investment for a property
    
    Parameters:
    - purchase_price: Purchase price of the property
    - annual_rent: Annual rental income
    - annual_expenses_percent: Annual expenses as percentage of purchase price
    - vacancy_rate: Expected vacancy rate
    
    Returns:
    - roi_percent: ROI as a percentage
    - cash_flow: Annual cash flow
    """
    annual_expenses = purchase_price * annual_expenses_percent
    effective_annual_rent = annual_rent * (1 - vacancy_rate)
    cash_flow = effective_annual_rent - annual_expenses
    roi_percent = (cash_flow / purchase_price) * 100
    
    return roi_percent, cash_flow

def create_price_heatmap(data, x_column, y_column, price_column='actual_worth', aggfunc='mean'):
    """
    Create a price heatmap visualization
    
    Parameters:
    - data: DataFrame containing the data
    - x_column: Column to use for x-axis
    - y_column: Column to use for y-axis
    - price_column: Column containing price data
    - aggfunc: Aggregation function ('mean', 'median', 'count', etc.)
    """
    # Create pivot table
    pivot_data = pd.pivot_table(
        data,
        values=price_column,
        index=y_column,
        columns=x_column,
        aggfunc=aggfunc,
        fill_value=0
    )
    
    # Create heatmap
    fig = px.imshow(
        pivot_data,
        labels=dict(x=x_column, y=y_column, color=f"{aggfunc.capitalize()} {price_column}"),
        x=pivot_data.columns,
        y=pivot_data.index,
        color_continuous_scale="Viridis"
    )
    
    fig.update_layout(
        title=f"{aggfunc.capitalize()} {price_column} by {y_column} and {x_column}",
        xaxis={'side': 'top'}
    )
    
    return fig

def show_sales_dashboard(transactions):
    st.header("💰 Property Sales Performance Dashboard")
    st.markdown("""This dashboard provides a comprehensive overview of Dubai's property sales transactions, 
                highlighting market activity and price trends based on the actual dataset with market context.""")
    
    # Add market insights and benchmark data in an expandable container
    with st.expander("📈 Market Insights & Benchmarks", expanded=True):
        st.info("""
        **2024-2025 Market Context:**
        - Dubai hit 180,900 property sales in 2024, up 36% from 2023
        - Q1 2025 sales volume rose another 23% YoY to AED 114 billion
        - Average sale price reached ~AED 2.7 million in Q1 2025
        - Price per sqft: ~AED 1,600 for off-plan sales, AED 1,300 for ready homes in 2024
        - Apartments dominated with ~82% of sales, while villas were 18%
        """)
    
    # Filters section
    st.subheader("📊 Interactive Filters")
    
    filter_col1, filter_col2, filter_col3, filter_col4, filter_col5, filter_col6 = st.columns(6)
    
    with filter_col1:
        if 'instance_date' in transactions.columns:
            min_date = transactions['instance_date'].min().date()
            max_date = transactions['instance_date'].max().date()
            date_range = st.date_input(
                "Date Range",
                [min_date, max_date],
                min_value=min_date,
                max_value=max_date
            )
    
    with filter_col2:
        if 'area_name_en' in transactions.columns:
            areas = ['All'] + sorted(transactions['area_name_en'].dropna().unique().tolist())
            selected_area = st.selectbox("Area", areas)
    
    with filter_col3:
        if 'property_type_en' in transactions.columns:
            property_types = ['All'] + sorted(transactions['property_type_en'].dropna().unique().tolist())
            selected_property_type = st.selectbox("Property Type", property_types)
    
    with filter_col4:
        if 'property_usage_en' in transactions.columns:
            usage_types = ['All'] + sorted(transactions['property_usage_en'].dropna().unique().tolist())
            selected_usage = st.selectbox("Property Usage", usage_types)
    
    with filter_col5:
        if 'project_name_en' in transactions.columns:
            projects = ['All'] + sorted(transactions['project_name_en'].dropna().unique().tolist())
            selected_project = st.selectbox("Project", projects)
    
    with filter_col6:
        if 'procedure_name_en' in transactions.columns:
            procedures = ['All'] + sorted(transactions['procedure_name_en'].dropna().unique().tolist())
            selected_procedure = st.selectbox("Transaction Type", procedures)
    
    # More filter options in expander
    with st.expander("Advanced Filters"):
        adv_col1, adv_col2, adv_col3, adv_col4 = st.columns(4)
        
        with adv_col1:
            if 'rooms_en' in transactions.columns:
                room_counts = ['All'] + sorted([str(r) for r in transactions['rooms_en'].dropna().unique().tolist()])
                selected_rooms = st.selectbox("Bedrooms", room_counts)
            
            if 'master_project_en' in transactions.columns:
                master_projects = ['All'] + sorted(transactions['master_project_en'].dropna().unique().tolist())
                selected_master_project = st.selectbox("Master Project", master_projects)
        
        with adv_col2:
            if 'has_parking' in transactions.columns:
                parking_options = ['All', 'Yes', 'No']
                selected_parking = st.selectbox("Parking Available", parking_options)
            
            # Zone filter (Waterfront, inland, desert, etc.) if available
            if 'zone_type' in transactions.columns:
                zone_types = ['All'] + sorted(transactions['zone_type'].dropna().unique().tolist())
                selected_zone = st.selectbox("Zone Type", zone_types)
        
        with adv_col3:
            if 'nearest_metro_en' in transactions.columns:
                metro_stations = ['All'] + sorted(transactions['nearest_metro_en'].dropna().unique().tolist())
                selected_metro = st.selectbox("Nearest Metro", metro_stations)
            
            if 'reg_type_en' in transactions.columns:
                reg_types = ['All'] + sorted(transactions['reg_type_en'].dropna().unique().tolist())
                selected_reg_type = st.selectbox("Registration Type", reg_types)
            
        with adv_col4:
            # Payment method filter if available
            if 'payment_method' in transactions.columns:
                payment_methods = ['All'] + sorted(transactions['payment_method'].dropna().unique().tolist())
                selected_payment = st.selectbox("Payment Method", payment_methods)
            
            # Distance filters if available
            if 'distance_to_metro' in transactions.columns:
                metro_dist_options = ['All', 'Under 1km', '1-3km', 'Over 3km']
                selected_metro_dist = st.selectbox("Distance to Metro", metro_dist_options)
    
    # Apply filters
    filtered_data = transactions.copy()
    
    if 'instance_date' in transactions.columns and len(date_range) == 2:
        filtered_data = filtered_data[(filtered_data['instance_date'].dt.date >= date_range[0]) & 
                                     (filtered_data['instance_date'].dt.date <= date_range[1])]
    
    if 'area_name_en' in transactions.columns and selected_area != 'All':
        filtered_data = filtered_data[filtered_data['area_name_en'] == selected_area]
    
    if 'property_type_en' in transactions.columns and selected_property_type != 'All':
        filtered_data = filtered_data[filtered_data['property_type_en'] == selected_property_type]
    
    if 'project_name_en' in transactions.columns and selected_project != 'All':
        filtered_data = filtered_data[filtered_data['project_name_en'] == selected_project]
    
    if 'procedure_name_en' in transactions.columns and selected_procedure != 'All':
        filtered_data = filtered_data[filtered_data['procedure_name_en'] == selected_procedure]
    
    # Apply advanced filters
    if 'property_usage_en' in transactions.columns and selected_usage != 'All':
        filtered_data = filtered_data[filtered_data['property_usage_en'] == selected_usage]
    
    if 'rooms_en' in transactions.columns and selected_rooms != 'All':
        filtered_data = filtered_data[filtered_data['rooms_en'].astype(str) == selected_rooms]
    
    if 'master_project_en' in transactions.columns and selected_master_project != 'All':
        filtered_data = filtered_data[filtered_data['master_project_en'] == selected_master_project]
    
    if 'has_parking' in transactions.columns and selected_parking != 'All':
        if selected_parking == 'Yes':
            filtered_data = filtered_data[filtered_data['has_parking'] == True]
        elif selected_parking == 'No':
            filtered_data = filtered_data[filtered_data['has_parking'] == False]
    
    if 'nearest_metro_en' in transactions.columns and selected_metro != 'All':
        filtered_data = filtered_data[filtered_data['nearest_metro_en'] == selected_metro]
    
    if 'reg_type_en' in transactions.columns and selected_reg_type != 'All':
        filtered_data = filtered_data[filtered_data['reg_type_en'] == selected_reg_type]
    
    if 'zone_type' in transactions.columns and selected_zone != 'All':
        filtered_data = filtered_data[filtered_data['zone_type'] == selected_zone]
    
    if 'payment_method' in transactions.columns and selected_payment != 'All':
        filtered_data = filtered_data[filtered_data['payment_method'] == selected_payment]
    
    # Apply distance to metro filter if available
    if 'distance_to_metro' in transactions.columns and selected_metro_dist != 'All':
        if selected_metro_dist == 'Under 1km':
            filtered_data = filtered_data[filtered_data['distance_to_metro'] < 1]
        elif selected_metro_dist == '1-3km':
            filtered_data = filtered_data[(filtered_data['distance_to_metro'] >= 1) & 
                                         (filtered_data['distance_to_metro'] <= 3)]
        elif selected_metro_dist == 'Over 3km':
            filtered_data = filtered_data[filtered_data['distance_to_metro'] > 3]
    
    # Calculate YoY comparison data
    current_period_data = filtered_data.copy()
    
    # Calculate previous period data if date range allows
    if 'instance_date' in transactions.columns and len(date_range) == 2:
        period_length = (date_range[1] - date_range[0]).days
        previous_end = date_range[0] - timedelta(days=1)
        previous_start = previous_end - timedelta(days=period_length)
        
        previous_period_data = transactions[
            (transactions['instance_date'].dt.date >= previous_start) & 
            (transactions['instance_date'].dt.date <= previous_end)
        ]
        
        # Apply same filters as current period
        if selected_area != 'All':
            previous_period_data = previous_period_data[previous_period_data['area_name_en'] == selected_area]
        if selected_property_type != 'All':
            previous_period_data = previous_period_data[previous_period_data['property_type_en'] == selected_property_type]
        # Apply other filters as needed
    else:
        previous_period_data = pd.DataFrame()  # Empty DataFrame if no date range
    
    # Key Metrics section
    st.subheader("🔑 Key Performance Metrics")
    
    # Transaction metrics row
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    
    with metric_col1:
        total_transactions = len(filtered_data)
        prev_total_transactions = len(previous_period_data) if not previous_period_data.empty else 0
        transaction_change = ((total_transactions - prev_total_transactions) / prev_total_transactions * 100) if prev_total_transactions > 0 else 0
        
        st.metric(
            "Total Transactions", 
            f"{total_transactions:,}",
            f"{transaction_change:+.1f}%" if prev_total_transactions > 0 else None,
            help="Overall number of sale deals in the selected period. Indicator of market activity. Dubai hit 180,900 property sales in 2024, up 36% from 2023."
        )
    
    with metric_col2:
        total_sales_value = filtered_data['actual_worth'].sum()
        prev_total_sales = previous_period_data['actual_worth'].sum() if not previous_period_data.empty else 0
        sales_change = ((total_sales_value - prev_total_sales) / prev_total_sales * 100) if prev_total_sales > 0 else 0
        
        st.metric(
            "Total Sales Value (AED)", 
            f"{total_sales_value:,.2f}",
            f"{sales_change:+.1f}%" if prev_total_sales > 0 else None,
            help="Aggregate value of transactions. Shows market liquidity and capital flow. 2024 market reference: AED 522.1 billion (↑27% vs 2023)"
        )
    
    with metric_col3:
        avg_deal_size = total_sales_value / total_transactions if total_transactions > 0 else 0
        prev_avg_deal = (prev_total_sales / prev_total_transactions) if prev_total_transactions > 0 else 0
        deal_size_change = ((avg_deal_size - prev_avg_deal) / prev_avg_deal * 100) if prev_avg_deal > 0 else 0
        
        st.metric(
            "Average Deal Size (AED)", 
            f"{avg_deal_size:,.2f}",
            f"{deal_size_change:+.1f}%" if prev_avg_deal > 0 else None,
            help="Average transaction value (Total Sales Value ÷ Number of Transactions). Helps benchmark market segments: affordable (<AED 1M), mid-market (1–3M), luxury (3M+)."
        )
    
    # Price metrics row
    metric_col4, metric_col5, metric_col6 = st.columns(3)
    
    with metric_col4:
        # Price per square meter
        if 'meter_sale_price' in filtered_data.columns:
            avg_price_per_sqm = filtered_data['meter_sale_price'].mean() 
            prev_avg_price_per_sqm = previous_period_data['meter_sale_price'].mean() if not previous_period_data.empty else 0
            price_per_sqm_change = ((avg_price_per_sqm - prev_avg_price_per_sqm) / prev_avg_price_per_sqm * 100) if prev_avg_price_per_sqm > 0 else 0
            
            st.metric(
                "Avg. Price per Sq. Meter (AED)",
                f"{avg_price_per_sqm:,.2f}",
                f"{price_per_sqm_change:+.1f}%" if prev_avg_price_per_sqm > 0 else None,
                help="Average price per square meter. 2024 reference: ~AED 17,222 (1,600 per sqft) for off-plan, AED 14,000 (1,300 per sqft) for ready homes."
            )
        else:
            # Median price if price per sqm not available
            median_price = filtered_data['actual_worth'].median()
            prev_median_price = previous_period_data['actual_worth'].median() if not previous_period_data.empty else 0
            median_change = ((median_price - prev_median_price) / prev_median_price * 100) if prev_median_price > 0 else 0
            
            st.metric(
                "Median Sale Price (AED)",
                f"{median_price:,.2f}",
                f"{median_change:+.1f}%" if prev_median_price > 0 else None,
                help="Median transaction price, which removes the effect of extreme values."
            )
    
    with metric_col5:
        # Determine if we can calculate off-plan vs ready split
        if 'reg_type_en' in filtered_data.columns:
            # Attempt to identify off-plan transactions
            offplan_indicator = filtered_data['reg_type_en'].str.contains('off|plan|primary', case=False, na=False)
            offplan_count = offplan_indicator.sum()
            offplan_percent = (offplan_count / total_transactions * 100) if total_transactions > 0 else 0
            
            st.metric(
                "Off-Plan Sales %",
                f"{offplan_percent:.1f}%",
                help="Percentage of off-plan sales. 2024 reference: ~68% of Dubai's sales were off-plan."
            )
        elif 'payment_method' in filtered_data.columns:
            # If payment method is available, show mortgage vs cash
            payment_counts = filtered_data['payment_method'].value_counts()
            mortgage_percent = (payment_counts.get('Mortgage', 0) / total_transactions * 100) if total_transactions > 0 else 0
            
            st.metric(
                "Mortgage Purchases %",
                f"{mortgage_percent:.1f}%",
                help="Percentage of purchases financed with mortgages. Indicates investor confidence and banking sentiment."
            )
        else:
            unique_areas = filtered_data['area_name_en'].nunique()
            st.metric(
                "Active Areas",
                f"{unique_areas}",
                help="Number of distinct areas with transactions in the selected period."
            )
    
    with metric_col6:
        # Sale velocity if available
        if 'listing_date' in filtered_data.columns and 'instance_date' in filtered_data.columns:
            filtered_data['days_to_sale'] = (filtered_data['instance_date'] - filtered_data['listing_date']).dt.days
            avg_days_to_sale = filtered_data['days_to_sale'].mean()
            
            st.metric(
                "Avg. Days to Sale",
                f"{avg_days_to_sale:.1f}",
                help="Average time from listing to closing. High velocity (low days) indicates high-demand zones."
            )
        else:
            highest_transaction = filtered_data['actual_worth'].max()
            st.metric(
                "Highest Transaction (AED)",
                f"{highest_transaction:,.2f}",
                help="The highest-value property transaction in the selected period."
            )
    
    # Market Segmentation
    st.subheader("💼 Market Segmentation")
    
    # Price range segmentation
    seg_col1, seg_col2 = st.columns(2)
    
    with seg_col1:
        # Create price segments
        price_bins = [0, 1000000, 3000000, 5000000, 10000000, float('inf')]
        price_labels = ['Affordable (<1M)', 'Mid-Market (1-3M)', 'Luxury (3-5M)', 'Ultra-Luxury (5-10M)', 'Super-Prime (10M+)']
        
        filtered_data['price_segment'] = pd.cut(
            filtered_data['actual_worth'],
            bins=price_bins,
            labels=price_labels
        )
        
        price_segment_counts = filtered_data['price_segment'].value_counts().reset_index()
        price_segment_counts.columns = ['Segment', 'Count']
        
        # Calculate percentage
        price_segment_counts['Percentage'] = price_segment_counts['Count'] / price_segment_counts['Count'].sum() * 100
        
        # Sort by price segment order
        price_segment_counts['Segment'] = pd.Categorical(
            price_segment_counts['Segment'],
            categories=price_labels,
            ordered=True
        )
        price_segment_counts = price_segment_counts.sort_values('Segment')
        
        fig = px.bar(
            price_segment_counts,
            x='Segment',
            y='Count',
            title="Transactions by Price Segment",
            text=price_segment_counts['Percentage'].apply(lambda x: f'{x:.1f}%'),
            color='Count',
            color_continuous_scale=px.colors.sequential.Viridis
        )
        
        fig.update_layout(xaxis_title="Price Segment", yaxis_title="Number of Transactions")
        st.plotly_chart(fig, use_container_width=True)
    
    with seg_col2:
        # Off-plan vs Ready Split (if available)
        if 'reg_type_en' in filtered_data.columns:
            filtered_data['market_type'] = filtered_data['reg_type_en'].apply(
                lambda x: 'Off-Plan' if pd.notna(x) and ('off' in str(x).lower() or 'plan' in str(x).lower() or 'primary' in str(x).lower()) else 'Ready'
            )
            
            market_counts = filtered_data['market_type'].value_counts().reset_index()
            market_counts.columns = ['Market Type', 'Count']
            market_counts['Percentage'] = market_counts['Count'] / market_counts['Count'].sum() * 100
            
            fig = px.pie(
                market_counts,
                values='Count',
                names='Market Type',
                title="Off-Plan vs Ready Market Split",
                hole=0.4,
                color_discrete_sequence=['#3366cc', '#dc3912']
            )
            
            # Add percentage labels
            fig.update_traces(
                textinfo='percent+label',
                textposition='outside'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        elif 'property_type_en' in filtered_data.columns:
            # Property type distribution if off-plan data not available
            property_type_counts = filtered_data['property_type_en'].value_counts().reset_index()
            property_type_counts.columns = ['Property Type', 'Count']
            property_type_counts['Percentage'] = property_type_counts['Count'] / property_type_counts['Count'].sum() * 100
            
            fig = px.pie(
                property_type_counts.head(5),  # Show top 5 property types
                values='Count',
                names='Property Type',
                title="Transaction Distribution by Property Type",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Payment method analysis if available
    if 'payment_method' in filtered_data.columns:
        st.subheader("💰 Payment Method Analysis")
        
        payment_counts = filtered_data['payment_method'].value_counts().reset_index()
        payment_counts.columns = ['Payment Method', 'Count']
        payment_counts['Percentage'] = payment_counts['Count'] / payment_counts['Count'].sum() * 100
        
        fig = px.pie(
            payment_counts,
            values='Count',
            names='Payment Method',
            title="Transactions by Payment Method",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        
        # Add percentage labels
        fig.update_traces(
            textinfo='percent+label',
            textposition='outside'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Time-based analysis
    st.subheader("📅 Temporal Analysis")
    
    time_col1, time_col2 = st.columns(2)
    
    with time_col1:
        time_metric = st.radio("View By", ["Monthly", "Quarterly", "Yearly"], horizontal=True)
        
        if time_metric == "Monthly":
            time_group = 'M'
            time_format = '%b %Y'
        elif time_metric == "Quarterly":
            time_group = 'Q'
            time_format = 'Q%q %Y'
        else:
            time_group = 'Y'
            time_format = '%Y'
    
    with time_col2:
        chart_type = st.radio("Chart Type", ["Transactions", "Value", "Average Price"], horizontal=True)
    
    # Prepare time-based data
    time_data = filtered_data.copy()
    time_period = time_data['instance_date'].dt.to_period(time_group)
    
    if chart_type == "Transactions":
        time_series = time_data.groupby(time_period).size()
        y_label = "Number of Transactions"
        title = f"{time_metric} Transaction Volume"
    elif chart_type == "Value":
        time_series = time_data.groupby(time_period)['actual_worth'].sum()
        y_label = "Total Value (AED)"
        title = f"{time_metric} Transaction Value"
    else:
        time_series = time_data.groupby(time_period)['actual_worth'].mean()
        y_label = "Average Price (AED)"
        title = f"{time_metric} Average Price"
    
    time_series = time_series.reset_index()
    time_series.columns = ['period', 'value']
    time_series['period_str'] = time_series['period'].astype(str)
    
    # Plot the time series
    fig = px.bar(
        time_series, 
        x='period_str', 
        y='value',
        title=title,
        labels={'period_str': time_metric, 'value': y_label},
        color='value',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    
    # Add a trend line
    fig.add_scatter(
        x=time_series['period_str'], 
        y=time_series['value'], 
        mode='lines',
        name='Trend',
        line=dict(color='red', width=2)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Area-wise Performance
    st.subheader("📍 Breakdown Analysis – Area-Wise")
    
    # Create top areas metrics table
    area_metrics = []
    
    for area, group in filtered_data.groupby('area_name_en'):
        metrics = {
            'Area': area,
            'No. of Deals': len(group),
            'Total Sales (AED)': group['actual_worth'].sum(),
            'Avg. Price': group['actual_worth'].mean(),
            'Price/sqft': group['meter_sale_price'].mean() * 10.764 if 'meter_sale_price' in group.columns else None  # Convert m² to ft²
        }
        
        # Calculate YoY growth if previous period data is available
        if not previous_period_data.empty:
            prev_group = previous_period_data[previous_period_data['area_name_en'] == area]
            
            if not prev_group.empty:
                prev_total_value = prev_group['actual_worth'].sum()
                if prev_total_value > 0:
                    metrics['YoY Growth %'] = ((metrics['Total Sales (AED)'] - prev_total_value) / prev_total_value * 100)
        
        area_metrics.append(metrics)
    
    # Create DataFrame from metrics
    area_metrics_df = pd.DataFrame(area_metrics)
    
    # Top performing areas (by transaction volume)
    area_vol_col1, area_vol_col2 = st.columns(2)
    
    with area_vol_col1:
        # Top areas by transaction count
        top_areas_by_volume = area_metrics_df.sort_values('No. of Deals', ascending=False).head(10)
        
        fig = px.bar(
            top_areas_by_volume,
            y='Area',
            x='No. of Deals',
            title="Top 10 Areas by Transaction Volume",
            color='No. of Deals',
            color_continuous_scale=px.colors.sequential.Viridis,
            orientation='h'
        )
        
        fig.update_layout(yaxis_title="Area", xaxis_title="Number of Transactions")
        st.plotly_chart(fig, use_container_width=True)
    
    with area_vol_col2:
        # Top areas by total value
        top_areas_by_value = area_metrics_df.sort_values('Total Sales (AED)', ascending=False).head(10)
        
        fig = px.bar(
            top_areas_by_value,
            y='Area',
            x='Total Sales (AED)',
            title="Top 10 Areas by Total Value (AED)",
            color='Total Sales (AED)',
            color_continuous_scale=px.colors.sequential.Plasma,
            orientation='h'
        )
        
        fig.update_layout(yaxis_title="Area", xaxis_title="Total Sales Value (AED)")
        st.plotly_chart(fig, use_container_width=True)
    
    # Create styled top 5 area table
    st.subheader("🔝 Top Performing Areas")
    
    # Get top 5 areas by volume
    top5_areas = area_metrics_df.nlargest(5, 'No. of Deals').copy()
    
    # Format numbers for better display
    top5_areas['Total Sales (AED)'] = top5_areas['Total Sales (AED)'].apply(
        lambda x: f"AED {x/1e9:.1f}B" if x >= 1e9 else f"AED {x/1e6:.1f}M"
    )
    top5_areas['Avg. Price'] = top5_areas['Avg. Price'].apply(
        lambda x: f"AED {x/1e6:.1f}M" if x >= 1e6 else f"AED {x/1000:.0f}K"
    )
    
    if 'Price/sqft' in top5_areas.columns:
        top5_areas['Price/sqft'] = top5_areas['Price/sqft'].apply(
            lambda x: f"AED {x:.0f}" if pd.notna(x) else "N/A"
        )
    
    if 'YoY Growth %' in top5_areas.columns:
        top5_areas['YoY Growth %'] = top5_areas['YoY Growth %'].apply(
            lambda x: f"+{x:.0f}%" if pd.notna(x) else "N/A"
        )

    
    
    # Create the styled dataframe
    st.dataframe(
        top5_areas,
        column_config={
            'Area': st.column_config.TextColumn("Area"),
            'No. of Deals': st.column_config.NumberColumn("No. of Deals", format="%d"),
            'Total Sales (AED)': st.column_config.TextColumn("Total Sales"),
            'Avg. Price': st.column_config.TextColumn("Avg. Price"),
            'Price/sqft': st.column_config.TextColumn("Price/sqft"),
            'YoY Growth %': st.column_config.TextColumn("YoY Growth")
        },
        use_container_width=True,
        hide_index=True
    )
    
    st.caption("""
    Insights:
    - Business Bay & Dubai Marina lead in value due to prime waterfront locations
    - JVC & similar areas are volume-driven, signaling investor entry zones or mid-income segments
    - Off-plan sales typically dominate in emerging areas with new project launches
    """)
    
    # Geographic Price Analysis - Add Mapbox visualization
    if 'latitude' in filtered_data.columns and 'longitude' in filtered_data.columns:
        st.subheader("🗺️ Geographic Price Analysis")
        
        # Create Mapbox visualization
        st.info("Explore property prices across Dubai. Point size indicates value, color intensity shows price per square foot.")
        
        mapbox_fig = create_mapbox_visualization(
            filtered_data,
            color_column='meter_sale_price' if 'meter_sale_price' in filtered_data.columns else 'actual_worth',
            size_column='actual_worth',
            title="Property Price Distribution Map"
        )
        
        st.plotly_chart(mapbox_fig, use_container_width=True)
    
    # ROI Calculator Tool
    st.subheader("💹 ROI Calculator")
    st.info("Estimate the potential return on investment for properties in your selected area.")
    
    calc_col1, calc_col2, calc_col3 = st.columns(3)
    
    with calc_col1:
        avg_property_price = filtered_data['actual_worth'].mean()
        property_price = st.number_input(
            "Property Purchase Price (AED)",
            min_value=0.0,
            value=avg_property_price,
            step=100000.0,
            format="%.2f"
        )
    
    with calc_col2:
        # Estimate monthly rent as 0.6% of property value (7.2% annual)
        est_monthly_rent = property_price * 0.006
        monthly_rent = st.number_input(
            "Monthly Rental Income (AED)",
            min_value=0.0,
            value=est_monthly_rent,
            step=1000.0,
            format="%.2f"
        )
        annual_rent = monthly_rent * 12
    
    with calc_col3:
        expenses_percent = st.slider(
            "Annual Expenses (% of Property Value)",
            min_value=1.0,
            max_value=30.0,
            value=10.0,
            step=0.5
        ) / 100
        
        vacancy_rate = st.slider(
            "Expected Vacancy Rate (%)",
            min_value=0.0,
            max_value=20.0,
            value=5.0,
            step=0.5
        ) / 100
    
    # Calculate ROI
    roi_percent, annual_cash_flow = calculate_roi(
        property_price,
        annual_rent,
        expenses_percent,
        vacancy_rate
    )
    
    # Display ROI results
    roi_col1, roi_col2, roi_col3 = st.columns(3)
    
    with roi_col1:
        st.metric(
            "Annual ROI (%)",
            f"{roi_percent:.2f}%",
            help="Return on Investment = (Annual Cash Flow / Property Price) × 100"
        )
    
    with roi_col2:
        st.metric(
            "Annual Cash Flow (AED)",
            f"{annual_cash_flow:,.2f}",
            help="Cash Flow = Annual Rental Income - Annual Expenses - Vacancy Loss"
        )
    
    with roi_col3:
        cap_rate = (annual_rent * (1 - vacancy_rate) / property_price) * 100
        st.metric(
            "Cap Rate (%)",
            f"{cap_rate:.2f}%",
            help="Capitalization Rate = (Annual Rental Income × (1 - Vacancy Rate)) / Property Price"
        )
    
    # Emerging Communities
    if not previous_period_data.empty:
        st.subheader("🌟 Emerging Communities")
        
        # Calculate growth rates
        emerging_area_data = []
        
        for area, group in filtered_data.groupby('area_name_en'):
            if len(group) >= 10:  # Minimum threshold to avoid statistical noise
                prev_group = previous_period_data[previous_period_data['area_name_en'] == area]
                prev_count = len(prev_group)
                
                if prev_count >= 5:  # Ensure enough data points for comparison
                    growth_rate = ((len(group) - prev_count) / prev_count) * 100
                    
                    emerging_area_data.append({
                        'Area': area,
                        'Current Transactions': len(group),
                        'Previous Transactions': prev_count,
                        'Transaction Growth %': growth_rate,
                        'Current Value (AED)': group['actual_worth'].sum(),
                        'Previous Value (AED)': prev_group['actual_worth'].sum(),
                        'Value Growth %': ((group['actual_worth'].sum() - prev_group['actual_worth'].sum()) / prev_group['actual_worth'].sum()) * 100
                    })
        
        if emerging_area_data:
            emerging_df = pd.DataFrame(emerging_area_data)
            
            # Get top 5 fastest growing areas by transaction count (min 30% growth)
            high_growth_areas = emerging_df[emerging_df['Transaction Growth %'] >= 30].nlargest(5, 'Transaction Growth %')
            
            if not high_growth_areas.empty:
                fig = px.bar(
                    high_growth_areas,
                    y='Area',
                    x='Transaction Growth %',
                    title="Fastest Growing Areas (Transaction Volume)",
                    color='Transaction Growth %',
                    orientation='h',
                    text=high_growth_areas['Transaction Growth %'].apply(lambda x: f'+{x:.0f}%')
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.info("""
                **Emerging Communities Insights**:
                
                Areas like Arjan, Liwan, Town Square, and Dubai South show rapid growth, driven by:
                - Infrastructure development and improved connectivity
                - Attractive price points for first-time buyers
                - New project launches with favorable payment plans
                - Growing community amenities and facilities
                """)
            else:
                st.info("No significant emerging communities detected in the selected period.")
        else:
            st.info("Insufficient historical data to identify emerging communities.")
    
    # Enhanced Project Sales Metrics
    st.subheader("🏗️ Project Sales Metrics")

    st.info("Comprehensive analysis of sales performance by project, including transaction volumes, pricing metrics, and developer breakdown.")

    # Create detailed project metrics
    project_detailed_metrics = []

    for project, group in filtered_data.groupby('project_name_en'):
        if len(group) >= 3:  # Only include projects with at least 3 transactions
            metrics = {
                'Project Name': project,
                'Area': group['area_name_en'].mode().iloc[0] if not group['area_name_en'].empty else "Unknown",
                'Transactions': len(group),
                'Total Value (AED)': group['actual_worth'].sum(),
                'Avg. Price (AED)': group['actual_worth'].mean(),
                'Median Price (AED)': group['actual_worth'].median(),
                'Price Range (AED)': f"{group['actual_worth'].min():,.0f} - {group['actual_worth'].max():,.0f}",
                'Price/sqft (AED)': group['meter_sale_price'].mean() * 10.764 if 'meter_sale_price' in group.columns else None,
            }
            
            # Add developer if available
            if 'developer' in group.columns:
                metrics['Developer'] = group['developer'].mode().iloc[0] if not group['developer'].empty else "Unknown"
            
            # Add most common property type
            if 'property_type_en' in group.columns:
                metrics['Property Type'] = group['property_type_en'].mode().iloc[0] if not group['property_type_en'].empty else "Unknown"
            
            # Add bedroom distribution if available
            if 'rooms_en' in group.columns:
                bed_counts = group['rooms_en'].value_counts()
                metrics['Most Common Bedrooms'] = bed_counts.index[0] if not bed_counts.empty else None
            
            # Add off-plan percentage if available
            if 'reg_type_en' in group.columns:
                offplan_indicator = group['reg_type_en'].str.contains('off|plan|primary', case=False, na=False)
                metrics['Off-plan %'] = offplan_indicator.mean() * 100
            
            # Calculate growth if previous period data is available
            if not previous_period_data.empty:
                prev_group = previous_period_data[previous_period_data['project_name_en'] == project]
                
                if not prev_group.empty and len(prev_group) >= 2:
                    prev_trans_count = len(prev_group)
                    prev_total_value = prev_group['actual_worth'].sum()
                    
                    if prev_trans_count > 0:
                        metrics['Transaction Growth %'] = ((len(group) - prev_trans_count) / prev_trans_count) * 100
                    
                    if prev_total_value > 0:
                        metrics['Value Growth %'] = ((metrics['Total Value (AED)'] - prev_total_value) / prev_total_value) * 100
            
            project_detailed_metrics.append(metrics)

    # Create and sort the dataframe
    project_detailed_df = pd.DataFrame(project_detailed_metrics)
    project_detailed_df = project_detailed_df.sort_values('Transactions', ascending=False)

    # Format values for display
    for col in ['Total Value (AED)', 'Avg. Price (AED)', 'Median Price (AED)']:
        if col in project_detailed_df.columns:
            project_detailed_df[col] = project_detailed_df[col].map(lambda x: f"{x:,.0f}")

    if 'Price/sqft (AED)' in project_detailed_df.columns:
        project_detailed_df['Price/sqft (AED)'] = project_detailed_df['Price/sqft (AED)'].map(
            lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A"
        )

    if 'Off-plan %' in project_detailed_df.columns:
        project_detailed_df['Off-plan %'] = project_detailed_df['Off-plan %'].map(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
        )

    for col in ['Transaction Growth %', 'Value Growth %']:
        if col in project_detailed_df.columns:
            project_detailed_df[col] = project_detailed_df[col].map(
                lambda x: f"{x:+.1f}%" if pd.notna(x) else "N/A"
            )

    # Display the top 15 projects by transaction volume
    top_projects_df = project_detailed_df.head(15)

    st.dataframe(
        top_projects_df,
        column_config={
            'Project Name': st.column_config.TextColumn("Project Name"),
            'Developer': st.column_config.TextColumn("Developer") if 'Developer' in top_projects_df.columns else None,
            'Area': st.column_config.TextColumn("Area"),
            'Property Type': st.column_config.TextColumn("Property Type") if 'Property Type' in top_projects_df.columns else None,
            'Transactions': st.column_config.NumberColumn("Transactions", format="%d"),
            'Total Value (AED)': st.column_config.TextColumn("Total Value"),
            'Avg. Price (AED)': st.column_config.TextColumn("Avg. Price"),
            'Median Price (AED)': st.column_config.TextColumn("Median Price"),
            'Price/sqft (AED)': st.column_config.TextColumn("Price/sqft") if 'Price/sqft (AED)' in top_projects_df.columns else None,
            'Most Common Bedrooms': st.column_config.TextColumn("Bedrooms") if 'Most Common Bedrooms' in top_projects_df.columns else None,
            'Off-plan %': st.column_config.TextColumn("Off-plan %") if 'Off-plan %' in top_projects_df.columns else None,
            'Transaction Growth %': st.column_config.TextColumn("Vol. Growth") if 'Transaction Growth %' in top_projects_df.columns else None,
            'Value Growth %': st.column_config.TextColumn("Value Growth") if 'Value Growth %' in top_projects_df.columns else None,
        },
        use_container_width=True,
        hide_index=True
    )

    # Add download button for full project metrics
    st.download_button(
        label="Download Full Project Metrics",
        data=project_detailed_df.to_csv(index=False).encode('utf-8'),
        file_name='dubai_projects_metrics.csv',
        mime='text/csv',
        key="download-project-metrics"
    )

    # Project Analysis Visualizations
    project_viz_col1, project_viz_col2 = st.columns(2)

    with project_viz_col1:
        # Calculate project distribution by size
        project_size_bins = [0, 5, 10, 20, 50, 100, float('inf')]
        project_size_labels = ['Very Small (1-5)', 'Small (6-10)', 'Medium (11-20)', 'Large (21-50)', 'X-Large (51-100)', 'Mega (100+)']
        
        project_sizes = project_detailed_df['Transactions'].copy()
        project_size_categories = pd.cut(project_sizes, bins=project_size_bins, labels=project_size_labels)
        
        size_counts = project_size_categories.value_counts().reset_index()
        size_counts.columns = ['Project Size', 'Count']
        
        # Ensure proper ordering
        size_counts['Project Size'] = pd.Categorical(
            size_counts['Project Size'],
            categories=project_size_labels,
            ordered=True
        )
        
        size_counts = size_counts.sort_values('Project Size')
        
        # Plot project size distribution
        fig = px.bar(
            size_counts,
            x='Project Size',
            y='Count',
            title="Projects by Transaction Volume Category",
            text='Count',
            color='Count',
            color_continuous_scale=px.colors.sequential.Viridis
        )
        
        st.plotly_chart(fig, use_container_width=True)

    with project_viz_col2:
        # Top developers by transaction count (if available)
        if 'Developer' in project_detailed_df.columns:
            # Extract numeric values from formatted strings for calculations
            project_detailed_df['Numeric_Total_Value'] = project_detailed_df['Total Value (AED)'].str.replace('AED', '').str.replace(',', '').astype(float)
            
            # Group by developer and calculate metrics
            dev_metrics = []
            
            for developer, group in project_detailed_df.groupby('Developer'):
                if not pd.isna(developer) and developer != "Unknown":
                    dev_metrics.append({
                        'Developer': developer,
                        'Projects': len(group),
                        'Total Transactions': group['Transactions'].sum(),
                        'Total Value': group['Numeric_Total_Value'].sum()
                    })
            
            # Create developer metrics dataframe
            dev_df = pd.DataFrame(dev_metrics)
            
            if not dev_df.empty:
                # Get top 10 developers by transaction count
                top_devs = dev_df.nlargest(10, 'Total Transactions')
                
                # Plot developer performance
                fig = px.bar(
                    top_devs,
                    y='Developer',
                    x='Total Transactions',
                    title="Top 10 Developers by Transaction Volume",
                    color='Total Value',
                    color_continuous_scale=px.colors.sequential.Plasma,
                    text='Projects',
                    orientation='h'
                )
                
                fig.update_traces(texttemplate='%{text} projects', textposition='inside')
                fig.update_layout(yaxis_title="Developer", xaxis_title="Number of Transactions")
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                # If no developer data, show project price distribution
                price_data = filtered_data.groupby('project_name_en')['actual_worth'].mean().reset_index()
                price_data.columns = ['Project', 'Average Price']
                price_data = price_data.sort_values('Average Price', ascending=False).head(10)
                
                fig = px.bar(
                    price_data,
                    y='Project',
                    x='Average Price',
                    title="Top 10 Projects by Average Price",
                    color='Average Price',
                    orientation='h'
                )
                
                st.plotly_chart(fig, use_container_width=True)

        # If we have developer data, add more developer analysis
        if 'Developer' in project_detailed_df.columns and 'developer' in filtered_data.columns:
            st.subheader("👷 Developer Performance Analysis")
            
            # Get transaction counts by developer
            dev_trans = filtered_data.groupby('developer').size().reset_index(name='Transactions')
            dev_trans = dev_trans.sort_values('Transactions', ascending=False).head(5)
            
            # Get average prices by developer
            dev_prices = filtered_data.groupby('developer')['actual_worth'].mean().reset_index(name='Avg_Price')
            
            # Merge transaction counts and prices
            dev_metrics = pd.merge(dev_trans, dev_prices, on='developer')
            
            # Calculate total value
            dev_values = filtered_data.groupby('developer')['actual_worth'].sum().reset_index(name='Total_Value')
            dev_metrics = pd.merge(dev_metrics, dev_values, on='developer')
            
            # Format the developer metrics for display
            dev_metrics['formatted_price'] = dev_metrics['Avg_Price'].apply(
                lambda x: f"AED {x/1e6:.2f}M" if x >= 1e6 else f"AED {x/1000:.0f}K"
            )
            
            dev_metrics['formatted_value'] = dev_metrics['Total_Value'].apply(
                lambda x: f"AED {x/1e9:.2f}B" if x >= 1e9 else f"AED {x/1e6:.2f}M"
            )
            
            # Create a scatter plot of developer performance
            fig = px.scatter(
                dev_metrics,
                x='Transactions',
                y='Avg_Price',
                size='Total_Value',
                color='Total_Value',
                hover_name='developer',
                text='developer',
                title="Developer Performance Matrix",
                labels={
                    'Transactions': 'Number of Transactions',
                    'Avg_Price': 'Average Price (AED)',
                    'Total_Value': 'Total Sales Value (AED)'
                },
                color_continuous_scale=px.colors.sequential.Viridis
            )
            
            fig.update_traces(
                textposition='top center',
                marker=dict(sizemode='area', sizeref=2.*max(dev_metrics['Total_Value'])/(40.**2), sizemin=4)
            )
            
            fig.update_layout(
                height=500,
                xaxis_title="Transaction Volume (Market Share)",
                yaxis_title="Average Price (Premium Positioning)"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.caption("""
            **Developer Performance Matrix Interpretation**:
            - Top-right quadrant: Premium developers with high market share
            - Top-left quadrant: Luxury/boutique developers with lower volume
            - Bottom-right quadrant: Mass-market developers with high volume
            - Bottom-left quadrant: Emerging developers or niche segments
            """)
    
    # Raw data table with download option
    st.subheader("📋 Transaction Data")
    
    # Show data sample with pagination
    st.dataframe(filtered_data, use_container_width=True)
    
    # Add download button for filtered data
    st.download_button(
        label="Download Filtered Data",
        data=filtered_data.to_csv(index=False).encode('utf-8'),
        file_name='dubai_property_transactions_filtered.csv',
        mime='text/csv',
    )
    
    # Dataset information
    st.caption(f"Dataset includes {len(transactions)} transactions from {transactions['instance_date'].min().date()} to {transactions['instance_date'].max().date()}")
    
    # Disclaimer
    st.caption("Market insights and benchmarks are based on industry reports and may not reflect the exact values in the dataset.")

    # Area-wise Sales Metrics - Detailed Table
    st.subheader("📊 Area-wise Sales Metrics")
    
    # Add explanation
    st.info("Comprehensive breakdown of sales performance by area, sorted by transaction volume.")

    # Create expanded metrics table with broader metrics
    area_expanded_metrics = []

    for area, group in filtered_data.groupby('area_name_en'):
        if len(group) >= 3:  # Include areas with at least 3 transactions
            metrics = {
                'Area': area,
                'Transactions': len(group),
                'Total Value (AED)': group['actual_worth'].sum(),
                'Average Price (AED)': group['actual_worth'].mean(),
                'Median Price (AED)': group['actual_worth'].median(),
                'Min Price (AED)': group['actual_worth'].min(),
                'Max Price (AED)': group['actual_worth'].max(),
                'Price/sqft (AED)': group['meter_sale_price'].mean() * 10.764 if 'meter_sale_price' in group.columns else None,
            }
            
            # Add bed types distribution if available
            if 'rooms_en' in group.columns:
                # Count the number of different bedroom types
                bed_counts = group['rooms_en'].value_counts()
                most_common_bed = bed_counts.index[0] if not bed_counts.empty else None
                metrics['Most Common Bedrooms'] = most_common_bed
            
            # Add off-plan percentage if available
            if 'reg_type_en' in group.columns:
                offplan_indicator = group['reg_type_en'].str.contains('off|plan|primary', case=False, na=False)
                metrics['Off-plan %'] = offplan_indicator.mean() * 100
            
            area_expanded_metrics.append(metrics)

    # Create and sort the dataframe
    area_metrics_expanded_df = pd.DataFrame(area_expanded_metrics)
    area_metrics_expanded_df = area_metrics_expanded_df.sort_values('Transactions', ascending=False)

    # Format metrics for display
    for col in ['Total Value (AED)', 'Average Price (AED)', 'Median Price (AED)', 'Min Price (AED)', 'Max Price (AED)']:
        if col in area_metrics_expanded_df.columns:
            area_metrics_expanded_df[col] = area_metrics_expanded_df[col].map(lambda x: f"{x:,.0f}")

    if 'Price/sqft (AED)' in area_metrics_expanded_df.columns:
        area_metrics_expanded_df['Price/sqft (AED)'] = area_metrics_expanded_df['Price/sqft (AED)'].map(
            lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A"
        )

    if 'Off-plan %' in area_metrics_expanded_df.columns:
        area_metrics_expanded_df['Off-plan %'] = area_metrics_expanded_df['Off-plan %'].map(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
        )

    # Create a color gradient formatter for the transactions column
    st.dataframe(
        area_metrics_expanded_df,
        column_config={
            'Area': st.column_config.TextColumn("Area"),
            'Transactions': st.column_config.NumberColumn(
                "Transactions",
                format="%d",
                help="Number of transactions in the selected period"
            ),
            'Total Value (AED)': st.column_config.TextColumn(
                "Total Value",
                help="Total sales value in AED"
            ),
            'Average Price (AED)': st.column_config.TextColumn(
                "Average Price",
                help="Mean transaction price"
            ),
            'Median Price (AED)': st.column_config.TextColumn(
                "Median Price",
                help="Median transaction price (less affected by outliers)"
            ),
            'Min Price (AED)': st.column_config.TextColumn(
                "Min Price",
                help="Lowest transaction price"
            ),
            'Max Price (AED)': st.column_config.TextColumn(
                "Max Price", 
                help="Highest transaction price"
            ),
            'Price/sqft (AED)': st.column_config.TextColumn(
                "Price/sqft",
                help="Average price per square foot"
            ),
            'Most Common Bedrooms': st.column_config.TextColumn(
                "Common Beds",
                help="Most common bedroom configuration"
            ) if 'Most Common Bedrooms' in area_metrics_expanded_df.columns else None,
            'Off-plan %': st.column_config.TextColumn(
                "Off-plan %",
                help="Percentage of off-plan sales"
            ) if 'Off-plan %' in area_metrics_expanded_df.columns else None
        },
        use_container_width=True,
        hide_index=True
    )

    # Add download button for the area metrics
    st.download_button(
        label="Download Area Metrics",
        data=area_metrics_expanded_df.to_csv(index=False).encode('utf-8'),
        file_name='area_sales_metrics.csv',
        mime='text/csv',
        key="download-area-metrics"
    )

    # Property Type Sales Metrics
    st.subheader("🏢 Property Type Sales Metrics")

    st.info("Analysis of sales performance by property type, showing price ranges and transaction volumes.")

    # Create property type metrics
    prop_type_metrics = []

    for prop_type, group in filtered_data.groupby('property_type_en'):
        if len(group) >= 3:  # Include property types with at least 3 transactions
            metrics = {
                'Property Type': prop_type,
                'Transactions': len(group),
                'Total Value (AED)': group['actual_worth'].sum(),
                'Average Price (AED)': group['actual_worth'].mean(),
                'Median Price (AED)': group['actual_worth'].median(),
                'Price Range (AED)': f"{group['actual_worth'].min():,.0f} - {group['actual_worth'].max():,.0f}",
                'Price/sqft (AED)': group['meter_sale_price'].mean() * 10.764 if 'meter_sale_price' in group.columns else None,
            }
            
            # Calculate YoY growth if previous period data is available
            if not previous_period_data.empty:
                prev_group = previous_period_data[previous_period_data['property_type_en'] == prop_type]
                
                if not prev_group.empty and len(prev_group) >= 3:
                    prev_total_value = prev_group['actual_worth'].sum()
                    prev_count = len(prev_group)
                    
                    if prev_total_value > 0 and prev_count > 0:
                        metrics['Vol. Change %'] = ((len(group) - prev_count) / prev_count) * 100
                        metrics['Value Change %'] = ((metrics['Total Value (AED)'] - prev_total_value) / prev_total_value) * 100
            
            prop_type_metrics.append(metrics)

    # Create and sort the dataframe
    prop_type_df = pd.DataFrame(prop_type_metrics)
    prop_type_df = prop_type_df.sort_values('Transactions', ascending=False)

    # Format metrics for display
    for col in ['Total Value (AED)', 'Average Price (AED)', 'Median Price (AED)']:
        if col in prop_type_df.columns:
            prop_type_df[col] = prop_type_df[col].map(lambda x: f"{x:,.0f}")

    if 'Price/sqft (AED)' in prop_type_df.columns:
        prop_type_df['Price/sqft (AED)'] = prop_type_df['Price/sqft (AED)'].map(
            lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A"
        )

    for col in ['Vol. Change %', 'Value Change %']:
        if col in prop_type_df.columns:
            prop_type_df[col] = prop_type_df[col].map(
                lambda x: f"{x:+.1f}%" if pd.notna(x) else "N/A"
            )

    # Property type metrics table
    st.dataframe(
        prop_type_df,
        column_config={
            'Property Type': st.column_config.TextColumn("Property Type"),
            'Transactions': st.column_config.NumberColumn(
                "Transactions",
                format="%d",
                help="Number of transactions in the selected period"
            ),
            'Total Value (AED)': st.column_config.TextColumn(
                "Total Value",
                help="Total sales value in AED"
            ),
            'Average Price (AED)': st.column_config.TextColumn(
                "Average Price",
                help="Mean transaction price"
            ),
            'Median Price (AED)': st.column_config.TextColumn(
                "Median Price",
                help="Median transaction price (less affected by outliers)"
            ),
            'Price Range (AED)': st.column_config.TextColumn(
                "Price Range",
                help="Min to Max price range"
            ),
            'Price/sqft (AED)': st.column_config.TextColumn(
                "Price/sqft",
                help="Average price per square foot"
            ),
            'Vol. Change %': st.column_config.TextColumn(
                "Vol. Change",
                help="Year-over-Year change in transaction volume"
            ) if 'Vol. Change %' in prop_type_df.columns else None,
            'Value Change %': st.column_config.TextColumn(
                "Value Change",
                help="Year-over-Year change in total value"
            ) if 'Value Change %' in prop_type_df.columns else None
        },
        use_container_width=True,
        hide_index=True
    )

    # Add visualization for property type comparison
    prop_type_col1, prop_type_col2 = st.columns(2)

    with prop_type_col1:
        # Convert formatted values back to numeric for visualization
        viz_data = filtered_data.groupby('property_type_en').agg(
            Transactions=('actual_worth', 'count'),
            Total_Value=('actual_worth', 'sum'),
            Avg_Price=('actual_worth', 'mean')
        ).reset_index().sort_values('Transactions', ascending=False).head(8)
        
        fig = px.bar(
            viz_data,
            x='property_type_en',
            y='Transactions',
            title="Top Property Types by Transaction Count",
            labels={'property_type_en': 'Property Type', 'Transactions': 'Number of Transactions'},
            color='Total_Value',
            color_continuous_scale=px.colors.sequential.Viridis,
            text_auto=True
        )
        
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with prop_type_col2:
        fig = px.scatter(
            viz_data,
            x='Transactions',
            y='Avg_Price',
            size='Total_Value',
            color='property_type_en',
            title="Property Type Price vs. Popularity",
            labels={
                'Transactions': 'Number of Transactions (Popularity)',
                'Avg_Price': 'Average Price (AED)',
                'property_type_en': 'Property Type'
            },
            hover_data=['property_type_en', 'Total_Value']
        )
        
        st.plotly_chart(fig, use_container_width=True)

    # Enhanced Price Segments
    st.subheader("💲 Enhanced Price Segment Analysis")

    st.info("Detailed analysis of market segments by price range, showing distribution and characteristics of each segment.")

    # Create more detailed price segments
    price_bins = [0, 500000, 1000000, 1500000, 2000000, 3000000, 5000000, 10000000, float('inf')]
    price_labels = [
        'Entry (<500K)', 
        'Affordable (500K-1M)', 
        'Lower Mid (1M-1.5M)', 
        'Mid-Market (1.5M-2M)', 
        'Upper Mid (2M-3M)', 
        'Luxury (3M-5M)', 
        'Ultra-Luxury (5M-10M)', 
        'Super-Prime (10M+)'
    ]

    # Apply price segmentation
    filtered_data['detailed_price_segment'] = pd.cut(
        filtered_data['actual_worth'],
        bins=price_bins,
        labels=price_labels
    )

    # Calculate metrics by price segment
    segment_metrics = []

    for segment, group in filtered_data.groupby('detailed_price_segment'):
        metrics = {
            'Price Segment': segment,
            'Transactions': len(group),
            'Total Value (AED)': group['actual_worth'].sum(),
            'Market Share %': (len(group) / len(filtered_data)) * 100,
            'Value Share %': (group['actual_worth'].sum() / filtered_data['actual_worth'].sum()) * 100,
            'Avg. Price (AED)': group['actual_worth'].mean(),
            'Price/sqft (AED)': group['meter_sale_price'].mean() * 10.764 if 'meter_sale_price' in group.columns else None,
        }
        
        # Add most common property type
        if 'property_type_en' in group.columns:
            prop_type_counts = group['property_type_en'].value_counts()
            if not prop_type_counts.empty:
                metrics['Top Property Type'] = prop_type_counts.index[0]
                metrics['Top Property %'] = (prop_type_counts.iloc[0] / len(group)) * 100
        
        # Add most common area
        if 'area_name_en' in group.columns:
            area_counts = group['area_name_en'].value_counts()
            if not area_counts.empty:
                metrics['Top Area'] = area_counts.index[0]
                metrics['Top Area %'] = (area_counts.iloc[0] / len(group)) * 100
        
        segment_metrics.append(metrics)

    # Create and sort the dataframe
    segment_df = pd.DataFrame(segment_metrics)

    # Sort by price segment order
    segment_df['Price Segment'] = pd.Categorical(
        segment_df['Price Segment'],
        categories=price_labels,
        ordered=True
    )
    segment_df = segment_df.sort_values('Price Segment')

    # Format metrics for display
    segment_df['Total Value (AED)'] = segment_df['Total Value (AED)'].map(lambda x: f"{x:,.0f}")
    segment_df['Avg. Price (AED)'] = segment_df['Avg. Price (AED)'].map(lambda x: f"{x:,.0f}")
    segment_df['Market Share %'] = segment_df['Market Share %'].map(lambda x: f"{x:.1f}%")
    segment_df['Value Share %'] = segment_df['Value Share %'].map(lambda x: f"{x:.1f}%")

    if 'Price/sqft (AED)' in segment_df.columns:
        segment_df['Price/sqft (AED)'] = segment_df['Price/sqft (AED)'].map(
            lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A"
        )

    if 'Top Property %' in segment_df.columns:
        segment_df['Top Property %'] = segment_df['Top Property %'].map(lambda x: f"{x:.1f}%")

    if 'Top Area %' in segment_df.columns:
        segment_df['Top Area %'] = segment_df['Top Area %'].map(lambda x: f"{x:.1f}%")

    # Create enhanced price segment table
    st.dataframe(
        segment_df,
        column_config={
            'Price Segment': st.column_config.TextColumn("Price Segment"),
            'Transactions': st.column_config.NumberColumn(
                "Transactions",
                format="%d"
            ),
            'Total Value (AED)': st.column_config.TextColumn("Total Value"),
            'Market Share %': st.column_config.TextColumn("Market Share"),
            'Value Share %': st.column_config.TextColumn("Value Share"),
            'Avg. Price (AED)': st.column_config.TextColumn("Avg. Price"),
            'Price/sqft (AED)': st.column_config.TextColumn("Price/sqft"),
            'Top Property Type': st.column_config.TextColumn("Top Property Type"),
            'Top Property %': st.column_config.TextColumn("Type %"),
            'Top Area': st.column_config.TextColumn("Top Area"),
            'Top Area %': st.column_config.TextColumn("Area %")
        },
        use_container_width=True,
        hide_index=True
    )

    # Add visualization for price segment distribution
    segment_col1, segment_col2 = st.columns(2)

    with segment_col1:
        # Prepare data for transaction count visualization
        segment_counts = filtered_data['detailed_price_segment'].value_counts().reset_index()
        segment_counts.columns = ['Price Segment', 'Transactions']
        
        # Ensure proper ordering
        segment_counts['Price Segment'] = pd.Categorical(
            segment_counts['Price Segment'],
            categories=price_labels,
            ordered=True
        )
        segment_counts = segment_counts.sort_values('Price Segment')
        
        fig = px.bar(
            segment_counts,
            x='Price Segment',
            y='Transactions',
            title="Transactions by Price Segment",
            color='Transactions',
            color_continuous_scale=px.colors.sequential.Viridis,
            text_auto=True
        )
        
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with segment_col2:
        # Prepare data for value distribution visualization
        segment_value = filtered_data.groupby('detailed_price_segment')['actual_worth'].sum().reset_index()
        segment_value.columns = ['Price Segment', 'Total Value']
        
        # Ensure proper ordering
        segment_value['Price Segment'] = pd.Categorical(
            segment_value['Price Segment'],
            categories=price_labels,
            ordered=True
        )
        segment_value = segment_value.sort_values('Price Segment')
        
        fig = px.pie(
            segment_value,
            values='Total Value',
            names='Price Segment',
            title="Total Value by Price Segment",
            color_discrete_sequence=px.colors.sequential.Viridis,
            hole=0.4
        )
        
        fig.update_traces(
            textinfo='percent+label',
            textposition='outside'
        )
        
        st.plotly_chart(fig, use_container_width=True) 