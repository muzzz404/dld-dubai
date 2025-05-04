import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

def show_market_comparison(filtered_data, previous_period_data):
    """Display market comparison section showing current vs previous period metrics"""
    
    if previous_period_data.empty:
        st.info("No previous period data available for comparison. Select a date range to enable period-over-period analysis.")
        return
    
    st.subheader("📊 Market Performance Comparison")
    
    # Calculate key metrics for both periods
    current_metrics = {
        'Transaction Count': len(filtered_data),
        'Total Value': filtered_data['actual_worth'].sum(),
        'Average Price': filtered_data['actual_worth'].mean(),
        'Median Price': filtered_data['actual_worth'].median(),
        'Areas': filtered_data['area_name_en'].nunique()
    }
    
    previous_metrics = {
        'Transaction Count': len(previous_period_data),
        'Total Value': previous_period_data['actual_worth'].sum(),
        'Average Price': previous_period_data['actual_worth'].mean(),
        'Median Price': previous_period_data['actual_worth'].median(),
        'Areas': previous_period_data['area_name_en'].nunique()
    }
    
    # Calculate percentage changes
    changes = {}
    for key in current_metrics:
        if previous_metrics[key] > 0:
            changes[key] = (current_metrics[key] - previous_metrics[key]) / previous_metrics[key] * 100
        else:
            changes[key] = 0
    
    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Transaction Growth",
            f"{changes['Transaction Count']:+.1f}%",
            help=f"Current: {current_metrics['Transaction Count']:,} vs Previous: {previous_metrics['Transaction Count']:,}"
        )
    
    with col2:
        st.metric(
            "Value Growth",
            f"{changes['Total Value']:+.1f}%",
            help=f"Current: AED {current_metrics['Total Value']:,.2f} vs Previous: AED {previous_metrics['Total Value']:,.2f}"
        )
    
    with col3:
        st.metric(
            "Avg. Price Change",
            f"{changes['Average Price']:+.1f}%",
            help=f"Current: AED {current_metrics['Average Price']:,.2f} vs Previous: AED {previous_metrics['Average Price']:,.2f}"
        )
    
    with col4:
        st.metric(
            "Median Price Change",
            f"{changes['Median Price']:+.1f}%",
            help=f"Current: AED {current_metrics['Median Price']:,.2f} vs Previous: AED {previous_metrics['Median Price']:,.2f}"
        )
    
    # Show comparison bar chart
    comparison_data = []
    for metric in ['Transaction Count', 'Total Value', 'Average Price', 'Median Price']:
        comparison_data.append({
            'Metric': metric,
            'Current Period': current_metrics[metric],
            'Previous Period': previous_metrics[metric],
            'Change %': changes[metric]
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # Use different charts for different metrics due to scale differences
    st.subheader("Transaction Count Comparison")
    fig = px.bar(
        comparison_df[comparison_df['Metric'] == 'Transaction Count'],
        x='Metric',
        y=['Current Period', 'Previous Period'],
        barmode='group',
        color_discrete_sequence=['#3366cc', '#dc3912'],
        labels={'value': 'Count', 'variable': 'Period'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Value Metrics Comparison")
    value_metrics = comparison_df[comparison_df['Metric'].isin(['Total Value', 'Average Price', 'Median Price'])]
    
    fig = px.bar(
        value_metrics,
        x='Metric',
        y=['Current Period', 'Previous Period'],
        barmode='group',
        color_discrete_sequence=['#3366cc', '#dc3912'],
        labels={'value': 'AED', 'variable': 'Period'}
    )
    st.plotly_chart(fig, use_container_width=True)

def predict_market_trends(historical_data):
    """Simple market trend prediction based on historical data"""
    
    if 'instance_date' not in historical_data.columns or historical_data.empty:
        st.info("Not enough historical data for trend prediction.")
        return
    
    st.subheader("📈 Market Trend Projection")
    
    # Prepare monthly data
    historical_data['year_month'] = historical_data['instance_date'].dt.to_period('M')
    monthly_data = historical_data.groupby('year_month').agg({
        'actual_worth': ['count', 'mean', 'sum']
    }).reset_index()
    
    monthly_data.columns = ['period', 'transaction_count', 'average_price', 'total_value']
    monthly_data['period'] = monthly_data['period'].astype(str)
    
    # Show last 12 months and projection for next 3 months
    recent_data = monthly_data.tail(12)
    
    # Simple linear projection for next 3 months
    last_counts = recent_data['transaction_count'].values
    last_prices = recent_data['average_price'].values
    last_values = recent_data['total_value'].values
    
    # Get last period for date calculation
    last_period = pd.Period(recent_data['period'].iloc[-1])
    
    # Simple linear regression to predict next periods
    next_periods = []
    for i in range(1, 4):
        next_period = last_period + i
        
        # Predict values using simple linear trend (last 6 periods average change)
        count_changes = np.diff(last_counts[-6:])
        price_changes = np.diff(last_prices[-6:])
        value_changes = np.diff(last_values[-6:])
        
        next_count = max(0, last_counts[-1] + np.mean(count_changes))
        next_price = max(0, last_prices[-1] + np.mean(price_changes))
        next_value = max(0, last_values[-1] + np.mean(value_changes))
        
        next_periods.append({
            'period': str(next_period),
            'transaction_count': next_count,
            'average_price': next_price,
            'total_value': next_value,
            'is_projection': True
        })
    
    # Convert recent data to include projection flag
    recent_data_with_flag = recent_data.copy()
    recent_data_with_flag['is_projection'] = False
    
    # Combine historical and projected data
    combined_data = pd.concat([
        recent_data_with_flag,
        pd.DataFrame(next_periods)
    ]).reset_index(drop=True)
    
    # Create charts with projections
    projection_col1, projection_col2 = st.columns(2)
    
    with projection_col1:
        fig = px.line(
            combined_data,
            x='period',
            y='transaction_count',
            title='Transaction Count Projection',
            markers=True,
            color='is_projection',
            color_discrete_map={False: '#3366cc', True: '#dc3912'},
            labels={'transaction_count': 'Transaction Count', 'period': 'Month', 'is_projection': 'Projection'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with projection_col2:
        fig = px.line(
            combined_data,
            x='period',
            y='average_price',
            title='Average Price Projection',
            markers=True,
            color='is_projection',
            color_discrete_map={False: '#3366cc', True: '#dc3912'},
            labels={'average_price': 'Average Price (AED)', 'period': 'Month', 'is_projection': 'Projection'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.caption("Note: Projections are based on simple linear trend analysis and should not be used as the sole basis for investment decisions.")

def market_segmentation_analysis(filtered_data):
    """Perform market segmentation analysis"""
    
    st.subheader("🔍 Market Segmentation Analysis")
    
    # Define segments based on price and property type
    if 'actual_worth' in filtered_data.columns and 'property_type_en' in filtered_data.columns:
        # Define price segments
        filtered_data['price_segment'] = pd.cut(
            filtered_data['actual_worth'],
            bins=[0, 1000000, 3000000, 5000000, 10000000, float('inf')],
            labels=['Affordable', 'Mid-Market', 'Luxury', 'Ultra-Luxury', 'Super-Prime']
        )
        
        # Create segment analysis
        segment_col1, segment_col2 = st.columns(2)
        
        with segment_col1:
            # Price segment by property type
            segment_counts = filtered_data.groupby(['price_segment', 'property_type_en']).size().reset_index(name='count')
            pivot_segment = segment_counts.pivot_table(
                index='price_segment',
                columns='property_type_en',
                values='count',
                fill_value=0
            )
            
            fig = px.imshow(
                pivot_segment,
                labels=dict(x='Property Type', y='Price Segment', color='Transaction Count'),
                color_continuous_scale='Viridis'
            )
            fig.update_layout(title='Transaction Count by Price Segment and Property Type')
            st.plotly_chart(fig, use_container_width=True)
        
        with segment_col2:
            # Average price by property type
            avg_prices = filtered_data.groupby('property_type_en')['actual_worth'].mean().reset_index()
            avg_prices = avg_prices.sort_values('actual_worth', ascending=False)
            
            fig = px.bar(
                avg_prices,
                x='actual_worth',
                y='property_type_en',
                orientation='h',
                title='Average Price by Property Type',
                labels={'actual_worth': 'Average Price (AED)', 'property_type_en': 'Property Type'},
                color='actual_worth',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Show segment distribution
        segment_dist = filtered_data['price_segment'].value_counts().reset_index()
        segment_dist.columns = ['Segment', 'Count']
        segment_dist['Percentage'] = segment_dist['Count'] / segment_dist['Count'].sum() * 100
        
        # Sort by the order of price segments
        segment_order = ['Affordable', 'Mid-Market', 'Luxury', 'Ultra-Luxury', 'Super-Prime']
        segment_dist['Segment'] = pd.Categorical(segment_dist['Segment'], categories=segment_order, ordered=True)
        segment_dist = segment_dist.sort_values('Segment')
        
        fig = px.pie(
            segment_dist,
            values='Count',
            names='Segment',
            title='Transaction Distribution by Price Segment',
            hover_data=['Percentage'],
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Required data for market segmentation analysis is not available.") 