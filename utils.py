import pandas as pd

# Format currency values
def format_currency(value):
    return f"AED {value:,.2f}"

# Calculate percentage change
def calculate_percent_change(current, previous):
    if previous == 0:
        return float('inf')
    return ((current - previous) / previous) * 100

# Calculate statistics for a numeric column
def calculate_statistics(df, column):
    if df.empty:
        return {
            'mean': 0,
            'median': 0,
            'min': 0,
            'max': 0,
            'count': 0
        }
    
    return {
        'mean': df[column].mean(),
        'median': df[column].median(),
        'min': df[column].min(),
        'max': df[column].max(),
        'count': len(df)
    }

# Convert date columns to datetime
def ensure_datetime(df, date_column):
    if date_column in df.columns:
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
    return df

# Create time period groups for analysis
def create_time_periods(df, date_column, period='M'):
    """
    Create time period groups for time-based analysis
    period options: 'M' (month), 'Q' (quarter), 'Y' (year)
    """
    if date_column not in df.columns:
        return df
    
    df = ensure_datetime(df, date_column)
    df['time_period'] = df[date_column].dt.to_period(period)
    return df

# Handle non-numeric values in data frames
def safe_numeric_conversion(df, column):
    if column in df.columns:
        return pd.to_numeric(df[column], errors='coerce')
    return pd.Series([float('nan')] * len(df))

# Create bins for value ranges
def create_value_bins(df, column, bins, labels=None):
    if column not in df.columns:
        return df
    
    numeric_column = safe_numeric_conversion(df, column)
    df[f'{column}_bin'] = pd.cut(numeric_column, bins=bins, labels=labels)
    return df 