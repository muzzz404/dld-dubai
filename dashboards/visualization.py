import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import streamlit as st

def plot_time_series(data, date_column, value_column, title, time_group='M'):
    """
    Create a time series plot with trend line
    
    Parameters:
    - data: DataFrame containing the data
    - date_column: Column containing dates
    - value_column: Column containing values to plot
    - title: Plot title
    - time_group: Time grouping ('D' for daily, 'W' for weekly, 'M' for monthly, etc.)
    """
    # Ensure datetime type
    data[date_column] = pd.to_datetime(data[date_column])
    
    # Group by time period
    time_period = data[date_column].dt.to_period(time_group)
    time_series = data.groupby(time_period)[value_column].agg(['mean', 'sum', 'count']).reset_index()
    
    # Convert period to string for plotting
    time_series['period_str'] = time_series[date_column].astype(str)
    
    # Create figure
    fig = px.bar(
        time_series, 
        x='period_str', 
        y='sum',  # Default to sum
        title=title,
        labels={'period_str': 'Time Period', 'sum': value_column},
        color='sum',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    
    # Add trend line
    fig.add_scatter(
        x=time_series['period_str'], 
        y=time_series['sum'], 
        mode='lines',
        name='Trend',
        line=dict(color='red', width=2)
    )
    
    return fig

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

def plot_metric_table(data, dimension_col, metrics, title="Metrics Table"):
    """
    Create a plotly table visualization for displaying metrics
    
    Parameters:
    - data: DataFrame containing the data
    - dimension_col: Column to use as the row dimension
    - metrics: List of metrics columns to display
    - title: Table title
    """
    # Prepare data for table
    table_data = data.sort_values(metrics[0], ascending=False).head(10)
    
    # Create table
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=[dimension_col] + metrics,
            fill_color='#075e54',
            align='left',
            font=dict(color='white', size=12)
        ),
        cells=dict(
            values=[table_data[dimension_col]] + [table_data[m] for m in metrics],
            fill_color='#f2f2f2',
            align='left'
        )
    )])
    
    fig.update_layout(title=title)
    return fig

def create_comparison_chart(data, comparison_col, value_col, title):
    """
    Create a comparison chart (bar chart with two categories)
    
    Parameters:
    - data: DataFrame containing the data
    - comparison_col: Column used for comparison (e.g., property type)
    - value_col: Column containing the values to compare
    - title: Chart title
    """
    # Group and calculate
    grouped = data.groupby(comparison_col)[value_col].agg(['mean', 'median', 'count']).reset_index()
    
    # Create figure with dual axes
    fig = px.bar(
        grouped,
        x=comparison_col,
        y='mean',
        color=comparison_col,
        title=title,
        text=grouped['count'].apply(lambda x: f"n={x}"),
        labels={
            comparison_col: comparison_col,
            'mean': f'Average {value_col}',
            'count': 'Count'
        }
    )
    
    # Add count as a secondary axis
    fig.add_trace(
        go.Scatter(
            x=grouped[comparison_col],
            y=grouped['count'],
            mode='markers',
            marker=dict(size=12, color='red'),
            name='Transaction Count',
            yaxis='y2'
        )
    )
    
    # Update layout for dual y-axes
    fig.update_layout(
        yaxis2=dict(
            title='Transaction Count',
            overlaying='y',
            side='right'
        )
    )
    
    return fig

def create_scatter_matrix(data, dimensions, color_by=None):
    """
    Create a scatter matrix for multi-dimensional analysis
    
    Parameters:
    - data: DataFrame containing the data
    - dimensions: List of columns to use as dimensions
    - color_by: Column to use for coloring points
    """
    fig = px.scatter_matrix(
        data,
        dimensions=dimensions,
        color=color_by,
        title="Multi-dimensional Analysis"
    )
    
    fig.update_layout(
        width=900,
        height=900
    )
    
    return fig 