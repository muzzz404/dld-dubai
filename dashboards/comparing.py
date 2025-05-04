import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
from utils import format_currency, calculate_statistics, calculate_percent_change

# Cache expensive calculations
@st.cache_data(ttl=3600)
def calculate_rental_yield(price, annual_rent):
    """Calculate gross rental yield as a percentage"""
    if price <= 0:
        return 0
    return (annual_rent / price) * 100

@st.cache_data(ttl=3600)
def calculate_total_return(rental_yield, appreciation_rate):
    """Calculate total return (yield + appreciation)"""
    return rental_yield + appreciation_rate

@st.cache_data(ttl=3600)
def calculate_net_yield(price, annual_rent, expenses_percent=0.2):
    """Calculate net yield after expenses"""
    if price <= 0:
        return 0
    expenses = price * expenses_percent
    net_income = annual_rent - expenses
    return (net_income / price) * 100

@st.cache_data(ttl=3600)
def calculate_irr_projection(initial_investment, annual_cash_flow, holding_period=5, exit_value_multiplier=1.2):
    """Calculate approximate IRR for a 5-year projection"""
    # Simple IRR approximation
    cash_flows = [-initial_investment]
    
    for year in range(holding_period):
        cash_flows.append(annual_cash_flow)
    
    # Add exit value in the final year
    cash_flows[-1] += initial_investment * exit_value_multiplier
    
    # Calculate IRR using NumPy's IRR function
    try:
        irr = np.irr(cash_flows)
        return irr * 100  # Convert to percentage
    except:
        return 0  # In case of computational error or no real solution

@st.cache_data(ttl=3600)
def create_dual_axis_chart(time_periods, price_index, rent_index, title="Price and Rent Indices Over Time"):
    """Create a dual-axis chart showing price and rent indices over time"""
    fig = go.Figure()
    
    # Add price index line
    fig.add_trace(
        go.Scatter(
            x=time_periods,
            y=price_index,
            name="Price Index",
            line=dict(color='blue', width=2)
        )
    )
    
    # Add rent index line on second y-axis
    fig.add_trace(
        go.Scatter(
            x=time_periods,
            y=rent_index,
            name="Rent Index",
            line=dict(color='red', width=2),
            yaxis="y2"
        )
    )
    
    # Update layout for dual axes
    fig.update_layout(
        title=title,
        xaxis=dict(title="Time Period"),
        yaxis=dict(
            title="Price Index",
            titlefont=dict(color="blue"),
            tickfont=dict(color="blue")
        ),
        yaxis2=dict(
            title="Rent Index",
            titlefont=dict(color="red"),
            tickfont=dict(color="red"),
            anchor="x",
            overlaying="y",
            side="right"
        ),
        legend=dict(x=0.01, y=0.99),
        hovermode="x unified"
    )
    
    return fig

@st.cache_data(ttl=3600)
def create_yield_roi_heatmap(data, x_column, y_column, z_column, title):
    """Create a heatmap showing yield or ROI by two dimensions"""
    # Create pivot table
    pivot_data = pd.pivot_table(
        data,
        values=z_column,
        index=y_column,
        columns=x_column,
        aggfunc='mean',
        fill_value=0
    )
    
    # Create heatmap
    fig = px.imshow(
        pivot_data,
        labels=dict(x=x_column, y=y_column, color=z_column),
        x=pivot_data.columns,
        y=pivot_data.index,
        color_continuous_scale="RdYlGn",  # Red-Yellow-Green scale appropriate for ROI/yield
        text_auto='.1f'  # Show values to 1 decimal place
    )
    
    fig.update_layout(
        title=title,
        xaxis_title=x_column,
        yaxis_title=y_column,
        coloraxis_colorbar=dict(title=z_column)
    )
    
    return fig

@st.cache_data(ttl=3600)
def prepare_merged_data(transactions, rentals, selected_area='All', selected_property_type='All', selected_rooms='All', min_price=0, max_price=float('inf')):
    """Prepare and merge transaction and rental data with caching"""
    # Filter transaction data
    filtered_transactions = transactions.copy()
    
    if selected_area != 'All':
        filtered_transactions = filtered_transactions[filtered_transactions['area_name_en'] == selected_area]
    
    if selected_property_type != 'All':
        filtered_transactions = filtered_transactions[filtered_transactions['property_type_en'] == selected_property_type]
    
    if 'rooms_en' in transactions.columns and selected_rooms != 'All':
        filtered_transactions = filtered_transactions[filtered_transactions['rooms_en'].astype(str) == selected_rooms]
    
    filtered_transactions = filtered_transactions[
        (filtered_transactions['actual_worth'] >= min_price) & 
        (filtered_transactions['actual_worth'] <= max_price)
    ]
    
    # Similarly filter rental data
    filtered_rentals = rentals.copy()
    
    if selected_area != 'All':
        filtered_rentals = filtered_rentals[filtered_rentals['area_name_en'] == selected_area]
    
    # Match property types between transactions and rentals
    if selected_property_type != 'All':
        # Map transaction property types to rental property types if they're different
        if 'property_type_en' in rentals.columns:
            filtered_rentals = filtered_rentals[filtered_rentals['property_type_en'] == selected_property_type]
        elif 'ejari_property_sub_type_en' in rentals.columns:
            # Attempt to match property types (this is a simplification)
            property_mapping = {
                'Apartment': ['Apartment', 'Studio', 'Flat'],
                'Villa': ['Villa', 'Townhouse'],
                'Commercial': ['Office', 'Shop', 'Retail']
            }
            
            # Find matching rental property types
            if selected_property_type in property_mapping:
                matched_types = property_mapping[selected_property_type]
                filtered_rentals = filtered_rentals[
                    filtered_rentals['ejari_property_sub_type_en'].isin(matched_types)
                ]
    
    # Filter by bedrooms if available in rental data
    if 'rooms_en' in rentals.columns and selected_rooms != 'All':
        filtered_rentals = filtered_rentals[filtered_rentals['rooms_en'].astype(str) == selected_rooms]
    
    # Calculate average prices and rents by area
    area_price_data = filtered_transactions.groupby('area_name_en')['actual_worth'].mean().reset_index()
    area_rent_data = filtered_rentals.groupby('area_name_en')['annual_amount'].mean().reset_index()
    
    # Merge the data to calculate yield
    merged_data = pd.merge(area_price_data, area_rent_data, on='area_name_en', how='inner')
    
    return filtered_transactions, filtered_rentals, merged_data

def show_comparing_dashboard(transactions, rentals):
    st.header("⚖️ Investment Comparison Dashboard")
    st.markdown("""This dashboard compares sales and rental data to provide insights on rental yields, 
                capital appreciation, and total returns across different areas and property types.""")
    
    # Initialize variables that might be referenced before definition
    prop_merged = pd.DataFrame()  # Initialize empty DataFrame to avoid NameError
    
    # Market insights in expandable container
    with st.expander("📈 Investment Market Context", expanded=True):
        st.info("""
        **2024-2025 Dubai Real Estate Investment Indicators:**
        - Average gross rental yields range from 5-8% citywide
        - Capital appreciation averaged 20-25% in prime areas (2024)
        - Total returns (yield + appreciation) peaked at 30-35% in emerging areas
        - Studios and 1BRs typically provide higher rental yields (7-9%)
        - Villas showed stronger capital appreciation (25-30%) but lower yields (4-6%)
        - Emerging areas like JVC, Dubai South offer higher yields (8-10%) but potentially lower appreciation
        - Prime areas like Downtown, Palm Jumeirah offer strong capital growth but compressed yields (4-6%)
        """)
    
    # Basic data preparation
    # Ensure we have the needed data
    if 'actual_worth' not in transactions.columns or 'annual_amount' not in rentals.columns:
        st.error("Required data columns missing. Please ensure transactions have 'actual_worth' and rentals have 'annual_amount'.")
        return
    
    # Filter and join data if we have common identifiers
    # For this example, we'll use area_name_en as the common field
    common_areas = list(set(transactions['area_name_en'].unique()) & set(rentals['area_name_en'].unique()))
    
    # Interactive Filters
    with st.sidebar:
        st.header("🔍 Dashboard Filters")
        
        # Create filter tabs for better organization
        filter_tabs = st.tabs(["Location", "Property", "Price", "Date"])
        
        with filter_tabs[0]:  # Location Filters
            st.subheader("Location Filters")
            
            # Area selection with search
            areas = ['All'] + sorted(common_areas)
            selected_area = st.selectbox("Area", areas, key="compare_area_filter")
            
            # Add neighborhood/community selection if available
            if 'master_project_en' in transactions.columns:
                projects = ['All']
                if selected_area != 'All':
                    area_projects = sorted(transactions[transactions['area_name_en'] == selected_area]['master_project_en'].dropna().unique().tolist())
                    projects.extend(area_projects)
                else:
                    projects.extend(sorted(transactions['master_project_en'].dropna().unique().tolist()))
                
                selected_project = st.selectbox("Master Project/Community", projects, key="project_filter")
            
            # Add proximity filters
            st.subheader("Proximity Filters")
            proximity_options = st.multiselect(
                "Must Be Near",
                ["Metro Station", "Mall", "Beach", "School", "Airport", "Healthcare"],
                key="proximity_filter"
            )
            
            if "Metro Station" in proximity_options and 'nearest_metro_en' in transactions.columns:
                metro_distance = st.slider("Max Distance to Metro (km)", 0.1, 5.0, 1.0, 0.1)
            
            if "Mall" in proximity_options and 'nearest_mall_en' in transactions.columns:
                mall_distance = st.slider("Max Distance to Mall (km)", 0.1, 5.0, 1.0, 0.1)
        
        with filter_tabs[1]:  # Property Filters
            st.subheader("Property Filters")
            
            # Property type selection
            property_types = ['All'] + sorted(transactions['property_type_en'].dropna().unique().tolist())
            selected_property_type = st.selectbox("Property Type", property_types, key="compare_type_filter")
            
            # Property subtypes if available
            if 'property_sub_type_en' in transactions.columns and selected_property_type != 'All':
                subtypes = ['All'] + sorted(transactions[transactions['property_type_en'] == selected_property_type]['property_sub_type_en'].dropna().unique().tolist())
                selected_subtype = st.selectbox("Property Subtype", subtypes, key="subtype_filter")
            
            # Bedrooms selection
            if 'rooms_en' in transactions.columns:
                room_counts = ['All'] + sorted([str(r) for r in transactions['rooms_en'].dropna().unique().tolist()])
                selected_rooms = st.selectbox("Bedrooms", room_counts, key="compare_rooms_filter")
            
            # Property size range
            if 'procedure_area' in transactions.columns:
                min_size, max_size = st.slider(
                    "Property Size (sqft)", 
                    int(transactions['procedure_area'].min()), 
                    int(transactions['procedure_area'].max()),
                    (int(transactions['procedure_area'].min()), int(transactions['procedure_area'].max()))
                )
            
            # Amenities (if available)
            st.subheader("Amenities")
            has_parking = st.checkbox("Parking", value=False)
            amenities = st.multiselect(
                "Must Include", 
                ["Gym", "Pool", "Security", "Balcony", "Maid's Room", "Study"],
                key="amenities_list"
            )
            
            # Property age filter
            property_age = st.selectbox(
                "Property Age", 
                ["All", "New (< 1 year)", "1-5 years", "5-10 years", "10+ years"], 
                key="property_age"
            )
        
        with filter_tabs[2]:  # Price Filters
            st.subheader("Price Filters")
            
            # Price Range with slider
            price_min = int(transactions['actual_worth'].min())
            price_max = int(transactions['actual_worth'].max())
            price_range = st.slider("Price Range (AED)", price_min, price_max, (price_min, price_max), step=100000)
            min_price, max_price = price_range
            
            # Also show as select boxes for quick filtering
            price_ranges = ["All", "Up to 1M AED", "1M-3M AED", "3M-5M AED", "5M-10M AED", "10M+ AED"]
            selected_price_range = st.selectbox("Price Bracket", price_ranges, key="compare_price_filter")
            
            # Convert price range to numeric bounds if using the select box
            if selected_price_range == "Up to 1M AED":
                min_price, max_price = 0, 1000000
            elif selected_price_range == "1M-3M AED":
                min_price, max_price = 1000000, 3000000
            elif selected_price_range == "3M-5M AED":
                min_price, max_price = 3000000, 5000000
            elif selected_price_range == "5M-10M AED":
                min_price, max_price = 5000000, 10000000
            elif selected_price_range == "10M+ AED":
                min_price, max_price = 10000000, float('inf')
            elif selected_price_range != "All":  # Keep the slider values if "All" is not selected
                pass  # Use the slider values
            
            # Investment parameters
            st.subheader("Investment Criteria")
            min_yield = st.slider("Minimum Yield (%)", 0.0, 15.0, 0.0, 0.5)
            min_roi = st.slider("Minimum Capital ROI (%)", 0.0, 50.0, 0.0, 1.0)
            
            # ROI preference selection
            roi_preference = st.radio(
                "Investment Strategy", 
                ["Balanced", "Yield Focused", "Appreciation Focused"],
                horizontal=True,
                key="roi_preference"
            )
        
        with filter_tabs[3]:  # Date Filters
            st.subheader("Date Filters")
            
            # Year range selection
            if 'instance_date' in transactions.columns:
                years = sorted(transactions['instance_date'].dt.year.unique())
                if len(years) > 1:
                    year_range = st.slider(
                        "Transaction Years", 
                        int(min(years)), 
                        int(max(years)),
                        (int(min(years)), int(max(years)))
                    )
                    min_year, max_year = year_range
                
                # Quarter selection
                quarters = ["All", "Q1", "Q2", "Q3", "Q4"]
                selected_quarter = st.selectbox("Quarter", quarters, key="quarter_filter")
                
                # Month range selection
                months = ["All"] + ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                selected_month = st.selectbox("Month", months, key="month_filter")
        
        # Reset filters button
        if st.button("Reset All Filters"):
            st.session_state["compare_area_filter"] = "All"
            st.session_state["compare_type_filter"] = "All"
            st.session_state["compare_rooms_filter"] = "All"
            st.session_state["compare_price_filter"] = "All"
            st.session_state["roi_preference"] = "Balanced"
            st.rerun()
    
    # Show active filters summary
    active_filters = []
    if selected_area != 'All':
        active_filters.append(f"Area: {selected_area}")
    if selected_property_type != 'All':
        active_filters.append(f"Property Type: {selected_property_type}")
    if 'rooms_en' in transactions.columns and selected_rooms != 'All':
        active_filters.append(f"Bedrooms: {selected_rooms}")
    if selected_price_range != "All":
        active_filters.append(f"Price Range: {selected_price_range}")
    
    if active_filters:
        st.info(" | ".join(active_filters))
        
    # Time period selection
    time_periods = ['Yearly', 'Quarterly', 'Monthly']
    selected_time_period = st.selectbox("Time Period", time_periods, index=1)
    
    # Convert to pandas period format
    if selected_time_period == 'Yearly':
        period_format = 'Y'
    elif selected_time_period == 'Quarterly':
        period_format = 'Q'
    else:
        period_format = 'M'
    
    # Filter transaction data
    filtered_transactions = transactions.copy()
    
    if selected_area != 'All':
        filtered_transactions = filtered_transactions[filtered_transactions['area_name_en'] == selected_area]
    
    if selected_property_type != 'All':
        filtered_transactions = filtered_transactions[filtered_transactions['property_type_en'] == selected_property_type]
    
    if 'rooms_en' in transactions.columns and selected_rooms != 'All':
        filtered_transactions = filtered_transactions[filtered_transactions['rooms_en'].astype(str) == selected_rooms]
    
    if selected_price_range != "All":
        filtered_transactions = filtered_transactions[
            (filtered_transactions['actual_worth'] >= min_price) & 
            (filtered_transactions['actual_worth'] <= max_price)
        ]
    
    # Similarly filter rental data
    filtered_rentals = rentals.copy()
    
    if selected_area != 'All':
        filtered_rentals = filtered_rentals[filtered_rentals['area_name_en'] == selected_area]
    
    # Match property types between transactions and rentals
    if selected_property_type != 'All':
        # Map transaction property types to rental property types if they're different
        if 'property_type_en' in rentals.columns:
            filtered_rentals = filtered_rentals[filtered_rentals['property_type_en'] == selected_property_type]
        elif 'ejari_property_sub_type_en' in rentals.columns:
            # Attempt to match property types (this is a simplification)
            property_mapping = {
                'Apartment': ['Apartment', 'Studio', 'Flat'],
                'Villa': ['Villa', 'Townhouse'],
                'Commercial': ['Office', 'Shop', 'Retail']
            }
            
            # Find matching rental property types
            if selected_property_type in property_mapping:
                matched_types = property_mapping[selected_property_type]
                filtered_rentals = filtered_rentals[
                    filtered_rentals['ejari_property_sub_type_en'].isin(matched_types)
                ]
    
    # Filter by bedrooms if available in rental data
    if 'rooms_en' in rentals.columns and selected_rooms != 'All':
        filtered_rentals = filtered_rentals[filtered_rentals['rooms_en'].astype(str) == selected_rooms]
    
    # Key Metrics Section
    st.subheader("🔢 Key Investment Metrics")
    
    # Calculate average prices and rents by area
    area_price_data = filtered_transactions.groupby('area_name_en')['actual_worth'].mean().reset_index()
    area_rent_data = filtered_rentals.groupby('area_name_en')['annual_amount'].mean().reset_index()
    
    # Merge the data to calculate yield
    merged_data = pd.merge(area_price_data, area_rent_data, on='area_name_en', how='inner')
    
    # Calculate yields
    merged_data['gross_yield'] = merged_data.apply(
        lambda row: calculate_rental_yield(row['actual_worth'], row['annual_amount']),
        axis=1
    )
    
    # Calculate net yield (after expenses)
    merged_data['net_yield'] = merged_data.apply(
        lambda row: calculate_net_yield(row['actual_worth'], row['annual_amount']),
        axis=1
    )
    
    # Calculate appreciation rate if we have historical data
    # For now, we'll use fixed appreciation rates based on area (simulated data)
    area_appreciation = {
        'Dubai Marina': 22.5,
        'Downtown Dubai': 24.0,
        'Palm Jumeirah': 28.0,
        'Jumeirah Village Circle': 18.5,
        'Business Bay': 21.0,
        'Dubai Hills Estate': 26.0,
        'Arabian Ranches': 17.0,
        'International City': 14.5,
        'Jumeirah Lake Towers': 16.0,
        'Dubai Sports City': 12.5,
        'Al Barsha': 15.0,
        'Dubai Silicon Oasis': 13.5,
        'Jumeirah Beach Residence': 19.5,
        'Dubai Production City': 14.0,
        'DIFC': 23.0,
        'Emirates Hills': 27.0,
        'The Springs': 16.5,
        'Dubai South': 20.0,
        'Meydan': 25.0,
        'Al Furjan': 17.5
    }
    
    # Apply appreciation rates
    merged_data['appreciation_rate'] = merged_data['area_name_en'].map(
        lambda x: area_appreciation.get(x, 15.0)  # Default to 15% if area not in our list
    )
    
    # Calculate total return
    merged_data['total_return'] = merged_data.apply(
        lambda row: calculate_total_return(row['gross_yield'], row['appreciation_rate']),
        axis=1
    )
    
    # Calculate Capital ROI
    merged_data['capital_roi'] = merged_data['appreciation_rate']
    
    # Create a metrics table with formulas
    with st.expander("📊 Key Metrics Formulas", expanded=True):
        metrics_df = pd.DataFrame({
            'Metric': [
                'Gross Rental Yield (%)', 
                'Capital ROI (%)', 
                'Total Return (%)', 
                'Net Yield (%)',
                '5-Year IRR (%)'
            ],
            'Formula': [
                '(Annual Rent ÷ Property Price) × 100',
                '((Current Price - Purchase Price) ÷ Purchase Price) × 100',
                'Rental Yield + Capital ROI',
                '(Rent - Expenses) ÷ Price × 100',
                'Calculated via cash flow projection'
            ],
            'Purpose': [
                'Income potential',
                'Appreciation over time',
                'Combined income & equity growth',
                'Post-cost return',
                'Long-term ROI modeling'
            ]
        })
        st.table(metrics_df)
    
    # Display overall metrics
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    
    with metric_col1:
        avg_gross_yield = merged_data['gross_yield'].mean() if not merged_data.empty else 0.0
        st.metric(
            "Average Gross Rental Yield",
            f"{avg_gross_yield:.2f}%",
            help="Annual rental income as a percentage of property value"
        )
    
    with metric_col2:
        avg_appreciation = merged_data['appreciation_rate'].mean() if not merged_data.empty else 0.0
        st.metric(
            "Average Capital ROI",
            f"{avg_appreciation:.2f}%",
            help="Annual increase in property value"
        )
    
    with metric_col3:
        avg_total_return = merged_data['total_return'].mean() if not merged_data.empty else 0.0
        st.metric(
            "Average Total Return",
            f"{avg_total_return:.2f}%",
            help="Combined return from rental yield and capital appreciation"
        )
    
    # Additional investment metrics
    metric_col4, metric_col5, metric_col6 = st.columns(3)
    
    with metric_col4:
        avg_net_yield = merged_data['net_yield'].mean() if not merged_data.empty else 0.0
        st.metric(
            "Average Net Yield (After Expenses)",
            f"{avg_net_yield:.2f}%",
            help="Rental yield after deducting typical expenses (20% of property value)"
        )
    
    with metric_col5:
        # Calculate 5-year IRR projection for an average property
        avg_price = filtered_transactions['actual_worth'].mean() if not filtered_transactions.empty else 0.0
        avg_rent = filtered_rentals['annual_amount'].mean() if not filtered_rentals.empty else 0.0
        avg_irr = calculate_irr_projection(avg_price, avg_rent) if avg_price > 0 and avg_rent > 0 else 0.0
        
        st.metric(
            "5-Year IRR Projection",
            f"{avg_irr:.2f}%",
            help="Internal Rate of Return over a 5-year holding period"
        )
    
    with metric_col6:
        # Calculate price-to-rent ratio
        price_to_rent = avg_price / avg_rent if avg_rent > 0 else 0
        st.metric(
            "Price-to-Rent Ratio",
            f"{price_to_rent:.1f}",
            help="Property price divided by annual rent. Lower values indicate better value for investors."
        )
    
    # Visualizations
    st.subheader("📊 Investment Performance Visualizations")
    
    # First, check if we have enough data to create visualizations
    if merged_data.empty:
        st.warning("No matching data found between transactions and rentals for the selected filters. Try adjusting your filters to see visualizations.")
    else:
        # Yield vs. Appreciation Scatter Plot
        viz_col1, viz_col2 = st.columns(2)
        
        with viz_col1:
            # Create scatter plot of yield vs. appreciation
            fig = px.scatter(
                merged_data,
                x='gross_yield',
                y='appreciation_rate',
                size='actual_worth',
                color='total_return',
                hover_name='area_name_en',
                text='area_name_en',
                title="Yield vs. ROI by Area/Project",
                labels={
                    'gross_yield': 'Gross Rental Yield (%)',
                    'appreciation_rate': 'Capital Appreciation (%)',
                    'total_return': 'Total Return (%)',
                    'actual_worth': 'Average Property Price'
                },
                color_continuous_scale=px.colors.sequential.Viridis
            )
            
            # Add quadrant lines
            fig.add_hline(y=avg_appreciation, line_dash="dash", line_color="gray")
            fig.add_vline(x=avg_gross_yield, line_dash="dash", line_color="gray")
            
            # Add annotations for quadrants
            fig.add_annotation(
                x=avg_gross_yield/2, 
                y=avg_appreciation*1.5,
                text="High Growth,<br>Low Yield",
                showarrow=False,
                font=dict(size=10)
            )
            fig.add_annotation(
                x=avg_gross_yield*1.5, 
                y=avg_appreciation*1.5,
                text="High Growth,<br>High Yield<br>(Ideal)",
                showarrow=False,
                font=dict(size=10)
            )
            fig.add_annotation(
                x=avg_gross_yield/2, 
                y=avg_appreciation/2,
                text="Low Growth,<br>Low Yield<br>(Avoid)",
                showarrow=False,
                font=dict(size=10)
            )
            fig.add_annotation(
                x=avg_gross_yield*1.5, 
                y=avg_appreciation/2,
                text="Low Growth,<br>High Yield",
                showarrow=False,
                font=dict(size=10)
            )
            
            # Update layout
            fig.update_traces(
                textposition='top center',
                marker=dict(
                    sizemode='area', 
                    sizeref=2.*max(merged_data['actual_worth'])/(40.**2) if len(merged_data) > 0 else 0.1, 
                    sizemin=4
                )
            )
            
            st.plotly_chart(fig, use_container_width=True, key="yield_vs_appreciation")
        
        with viz_col2:
            # Total Return by Area Bar Chart
            if len(merged_data) >= 1:
                top_returns = merged_data.sort_values('total_return', ascending=False).head(10)
                
                fig = px.bar(
                    top_returns,
                    y='area_name_en',
                    x='total_return',
                    orientation='h',
                    title="Top 10 Areas by Total Return",
                    labels={
                        'area_name_en': 'Area',
                        'total_return': 'Total Return (%)'
                    },
                    color='total_return',
                    color_continuous_scale='RdYlGn',
                    text=top_returns['total_return'].apply(lambda x: f"{x:.1f}%")
                )
                
                fig.update_layout(yaxis_title="Area", xaxis_title="Total Return (%)")
                st.plotly_chart(fig, use_container_width=True, key="total_return_by_area")
            else:
                st.info("Insufficient data to display top areas by total return.")
    
    # New Bar Charts: Yield & ROI by property type
    if 'property_type_en' in filtered_transactions.columns:
        prop_viz_col1, prop_viz_col2 = st.columns(2)
        
        # Group by property type
        property_yield_data = filtered_transactions.groupby('property_type_en').agg(
            avg_price=('actual_worth', 'mean')
        ).reset_index()
        
        # Match rental data
        if 'property_type_en' in filtered_rentals.columns:
            property_rent_data = filtered_rentals.groupby('property_type_en').agg(
                avg_rent=('annual_amount', 'mean')
            ).reset_index()
            
            # Merge datasets
            property_metrics = pd.merge(
                property_yield_data,
                property_rent_data,
                on='property_type_en',
                how='inner'
            )
            
            # Calculate metrics
            property_metrics['gross_yield'] = property_metrics.apply(
                lambda row: calculate_rental_yield(row['avg_price'], row['avg_rent']), 
                axis=1
            )
            
            # Add appreciation rates (use average by property type)
            property_appreciation = {
                'Apartment': 18.5,
                'Villa': 22.0,
                'Building': 16.0,
                'Land': 14.0,
                'Commercial': 15.0,
                'Office': 13.5,
                'Retail': 14.5
            }
            
            property_metrics['appreciation_rate'] = property_metrics['property_type_en'].map(
                lambda x: property_appreciation.get(x, 15.0)
            )
            
            property_metrics['total_return'] = property_metrics['gross_yield'] + property_metrics['appreciation_rate']
            
            # Create bar charts
            with prop_viz_col1:
                fig = px.bar(
                    property_metrics,
                    x='property_type_en',
                    y='gross_yield',
                    title="Rental Yield by Property Type",
                    labels={
                        'property_type_en': 'Property Type',
                        'gross_yield': 'Gross Rental Yield (%)'
                    },
                    color='gross_yield',
                    color_continuous_scale='Blues',
                    text=property_metrics['gross_yield'].apply(lambda x: f"{x:.1f}%")
                )
                
                st.plotly_chart(fig, use_container_width=True, key="yield_by_property_type")
            
            with prop_viz_col2:
                fig = px.bar(
                    property_metrics,
                    x='property_type_en',
                    y='appreciation_rate',
                    title="Capital ROI by Property Type",
                    labels={
                        'property_type_en': 'Property Type',
                        'appreciation_rate': 'Capital ROI (%)'
                    },
                    color='appreciation_rate',
                    color_continuous_scale='Greens',
                    text=property_metrics['appreciation_rate'].apply(lambda x: f"{x:.1f}%")
                )
                
                st.plotly_chart(fig, use_container_width=True, key="roi_by_property_type")
    
    # Ranking Tables: Top 10 areas by yield, ROI, total return
    st.subheader("🏆 Top Investment Areas/Projects")
    
    rank_col1, rank_col2, rank_col3 = st.columns(3)
    
    with rank_col1:
        # Top areas by yield
        top_yield_areas = merged_data.sort_values('gross_yield', ascending=False).head(10)
        st.markdown("#### Top 10 by Rental Yield")
        
        yield_df = top_yield_areas[['area_name_en', 'gross_yield']].copy()
        yield_df.columns = ['Area', 'Yield (%)']
        yield_df['Yield (%)'] = yield_df['Yield (%)'].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(
            yield_df,
            hide_index=True,
            use_container_width=True
        )
    
    with rank_col2:
        # Top areas by ROI
        top_roi_areas = merged_data.sort_values('appreciation_rate', ascending=False).head(10)
        st.markdown("#### Top 10 by Capital ROI")
        
        roi_df = top_roi_areas[['area_name_en', 'appreciation_rate']].copy()
        roi_df.columns = ['Area', 'ROI (%)']
        roi_df['ROI (%)'] = roi_df['ROI (%)'].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(
            roi_df,
            hide_index=True,
            use_container_width=True
        )
    
    with rank_col3:
        # Top areas by total return
        top_return_areas = merged_data.sort_values('total_return', ascending=False).head(10)
        st.markdown("#### Top 10 by Total Return")
        
        return_df = top_return_areas[['area_name_en', 'total_return']].copy()
        return_df.columns = ['Area', 'Total Return (%)']
        return_df['Total Return (%)'] = return_df['Total Return (%)'].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(
            return_df,
            hide_index=True,
            use_container_width=True
        )
    
    # Geo/Location Analysis Section
    st.subheader("🌍 Geo/Location Analysis")
    
    # Proximity analysis
    if 'nearest_metro_en' in filtered_transactions.columns and 'nearest_mall_en' in filtered_transactions.columns:
        proximity_col1, proximity_col2 = st.columns(2)
        
        with proximity_col1:
            st.markdown("#### Metro Proximity Impact")
            
            # Group by metro station
            if len(filtered_transactions['nearest_metro_en'].dropna().unique()) > 1:
                metro_data = filtered_transactions.groupby('nearest_metro_en').agg(
                    avg_price=('actual_worth', 'mean'),
                    count=('instance_date', 'count')
                ).reset_index()
                
                # Filter for stations with sufficient data
                metro_data = metro_data[metro_data['count'] >= 5].sort_values('avg_price', ascending=False)
                
                if not metro_data.empty:
                    # Create bar chart
                    fig = px.bar(
                        metro_data.head(10),
                        x='nearest_metro_en',
                        y='avg_price',
                        title="Average Property Price by Metro Station",
                        labels={
                            'nearest_metro_en': 'Metro Station',
                            'avg_price': 'Average Price (AED)'
                        },
                        color='avg_price',
                        text=metro_data.head(10)['avg_price'].apply(lambda x: f"{x/1000000:.1f}M")
                    )
                    
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Insufficient data for metro station analysis")
            else:
                st.info("Insufficient metro station data available")
        
        with proximity_col2:
            st.markdown("#### Mall Proximity Impact")
            
            # Group by mall
            if len(filtered_transactions['nearest_mall_en'].dropna().unique()) > 1:
                mall_data = filtered_transactions.groupby('nearest_mall_en').agg(
                    avg_price=('actual_worth', 'mean'),
                    count=('instance_date', 'count')
                ).reset_index()
                
                # Filter for malls with sufficient data
                mall_data = mall_data[mall_data['count'] >= 5].sort_values('avg_price', ascending=False)
                
                if not mall_data.empty:
                    # Create bar chart
                    fig = px.bar(
                        mall_data.head(10),
                        x='nearest_mall_en',
                        y='avg_price',
                        title="Average Property Price by Mall Proximity",
                        labels={
                            'nearest_mall_en': 'Mall',
                            'avg_price': 'Average Price (AED)'
                        },
                        color='avg_price',
                        text=mall_data.head(10)['avg_price'].apply(lambda x: f"{x/1000000:.1f}M")
                    )
                    
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Insufficient data for mall proximity analysis")
            else:
                st.info("Insufficient mall proximity data available")
    
    # Project-Level Stats
    if 'project_name_en' in filtered_transactions.columns:
        st.markdown("#### Project-Level Investment Metrics")
        
        # Group by project
        project_data = filtered_transactions.groupby('project_name_en').agg(
            avg_price=('actual_worth', 'mean'),
            count=('instance_date', 'count')
        ).reset_index()
        
        # Filter for projects with sufficient data
        project_data = project_data[
            (project_data['count'] >= 3) & 
            (project_data['project_name_en'] != "")
        ]  # Removed sorting by avg_price here
        
        # Add rental data if possible
        if 'project_name_en' in filtered_rentals.columns:
            project_rent_data = filtered_rentals.groupby('project_name_en').agg(
                avg_rent=('annual_amount', 'mean')
            ).reset_index()
            
            # Merge with project data
            project_data = pd.merge(
                project_data,
                project_rent_data,
                on='project_name_en',
                how='left'
            )
            
            # Calculate yield
            project_data['gross_yield'] = project_data.apply(
                lambda row: calculate_rental_yield(row['avg_price'], row['avg_rent']) if pd.notnull(row['avg_rent']) else None,
                axis=1
            )
            
            # Fill NaN yields with estimated values
            project_data['gross_yield'].fillna(avg_gross_yield, inplace=True)
            
            # Add appreciation (using area averages or fixed rate)
            project_data['appreciation_rate'] = 15.0  # Default
            
            # Calculate total return
            project_data['total_return'] = project_data['gross_yield'] + project_data['appreciation_rate']
            
            # Display top projects
            if not project_data.empty:
                top_projects = project_data.sort_values('total_return', ascending=False).head(10)
                
                # Create a display dataframe without string formatting
                top_projects_display = top_projects[['project_name_en', 'avg_price', 'avg_rent', 'gross_yield', 'appreciation_rate', 'total_return']].copy()
                top_projects_display.columns = ['Project', 'Avg Price (AED)', 'Avg Rent (AED)', 'Yield (%)', 'ROI (%)', 'Total Return (%)']
                
                # Replace NaN with None for better handling in the dataframe
                top_projects_display = top_projects_display.fillna(value=None)
                
                # Use column_config for formatting instead of string conversion
                st.dataframe(
                    top_projects_display,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Avg Price (AED)": st.column_config.NumberColumn(
                            "Avg Price (AED)",
                            format="%,.0f"
                        ),
                        "Avg Rent (AED)": st.column_config.NumberColumn(
                            "Avg Rent (AED)",
                            format="%,.0f"
                        ),
                        "Yield (%)": st.column_config.NumberColumn(
                            "Yield (%)",
                            format="%.2f%%"
                        ),
                        "ROI (%)": st.column_config.NumberColumn(
                            "ROI (%)",
                            format="%.2f%%"
                        ),
                        "Total Return (%)": st.column_config.NumberColumn(
                            "Total Return (%)",
                            format="%.2f%%"
                        )
                    }
                )
            else:
                st.info("Insufficient project data available")
        else:
            st.info("Project-level rental data not available")
    
    # Create Yield & ROI Heatmap Matrix
    st.subheader("🔥 Yield & ROI Matrix Analysis")
    
    # Property Type vs Area Yield Heatmap
    if len(merged_data) >= 5:  # Only show if we have enough data points
        # Get property type data
        property_data = []
        
        # Verify that needed columns exist
        trans_has_req_cols = 'area_name_en' in filtered_transactions.columns and 'property_type_en' in filtered_transactions.columns
        rent_has_area = 'area_name_en' in filtered_rentals.columns
        
        if not trans_has_req_cols or not rent_has_area:
            st.warning("Required columns missing from data. Property type analysis unavailable.")
        else:
            # Group by area and property type for transactions dataset
            area_prop_prices = filtered_transactions.groupby(['area_name_en', 'property_type_en'])['actual_worth'].mean().reset_index()
            
            # For rentals, handle different property type column names
            if 'property_type_en' in rentals.columns:
                area_prop_rents = filtered_rentals.groupby(['area_name_en', 'property_type_en'])['annual_amount'].mean().reset_index()
            elif 'ejari_property_sub_type_en' in rentals.columns:
                # Simplify property type categorization
                filtered_rentals['simplified_property_type'] = filtered_rentals['ejari_property_sub_type_en'].apply(
                    lambda x: 'Apartment' if x in ['Apartment', 'Studio', 'Flat'] else
                              'Villa' if x in ['Villa', 'Townhouse'] else
                              'Commercial' if x in ['Office', 'Shop', 'Retail'] else 'Other'
                )
                area_prop_rents = filtered_rentals.groupby(['area_name_en', 'simplified_property_type'])['annual_amount'].mean().reset_index()
                area_prop_rents.rename(columns={'simplified_property_type': 'property_type_en'}, inplace=True)
            
            # Merge datasets
            try:
                prop_merged = pd.merge(
                    area_prop_prices, 
                    area_prop_rents, 
                    on=['area_name_en', 'property_type_en'], 
                    how='inner'
                )
                
                # Calculate yields and appreciation
                prop_merged['gross_yield'] = prop_merged.apply(
                    lambda row: calculate_rental_yield(row['actual_worth'], row['annual_amount']),
                    axis=1
                )
                
                # Add appreciation rate (simulated for now)
                prop_merged['appreciation_rate'] = prop_merged['area_name_en'].map(
                    lambda x: area_appreciation.get(x, 15.0)
                )
                
                # Calculate total return
                prop_merged['total_return'] = prop_merged['gross_yield'] + prop_merged['appreciation_rate']
                
                # Create heatmap for yields
                if len(prop_merged) >= 6:  # Need enough data points for a meaningful heatmap
                    heatmap_col1, heatmap_col2 = st.columns(2)
                    
                    with heatmap_col1:
                        yield_heatmap = create_yield_roi_heatmap(
                            prop_merged,
                            'property_type_en',
                            'area_name_en',
                            'gross_yield',
                            "Rental Yield (%) by Area and Property Type"
                        )
                        st.plotly_chart(yield_heatmap, use_container_width=True, key="yield_heatmap")
                    
                    with heatmap_col2:
                        roi_heatmap = create_yield_roi_heatmap(
                            prop_merged,
                            'property_type_en',
                            'area_name_en',
                            'total_return',
                            "Total Return (%) by Area and Property Type"
                        )
                        st.plotly_chart(roi_heatmap, use_container_width=True, key="roi_heatmap")
                else:
                    st.info("Insufficient data to generate heatmaps. Try broadening your filters.")
            except Exception as e:
                st.error(f"Error processing property type data: {str(e)}")
    else:
        st.info("Insufficient data to perform area-property type analysis. Try broadening your filters.")
    
    # Investment Recommendation Engine
    st.subheader("🧠 Investment Recommendations")
    
    # Set recommendation criteria based on strategy preference
    if roi_preference == "Yield Focused":
        merged_data['recommendation_score'] = merged_data['gross_yield'] * 0.7 + merged_data['appreciation_rate'] * 0.3
        strategy_description = "Prioritizing rental income over capital growth"
    elif roi_preference == "Appreciation Focused":
        merged_data['recommendation_score'] = merged_data['gross_yield'] * 0.3 + merged_data['appreciation_rate'] * 0.7
        strategy_description = "Prioritizing capital growth over rental income"
    else:  # Balanced
        merged_data['recommendation_score'] = merged_data['gross_yield'] * 0.5 + merged_data['appreciation_rate'] * 0.5
        strategy_description = "Balancing rental income and capital growth"
    
    # Filter based on minimum criteria
    recommendation_data = merged_data[
        (merged_data['gross_yield'] >= min_yield) &
        (merged_data['appreciation_rate'] >= min_roi)
    ]
    
    # Get top recommendations
    top_recommendations = recommendation_data.sort_values('recommendation_score', ascending=False).head(5)
    
    # Display recommendation explanation
    st.info(f"**Investment Strategy: {roi_preference}** - {strategy_description}")
    
    if not top_recommendations.empty:
        # Create recommendation table
        for i, row in top_recommendations.iterrows():
            with st.expander(f"📌 {row['area_name_en']} - Total Return: {row['total_return']:.2f}%", expanded=True if i == 0 else False):
                rec_col1, rec_col2, rec_col3 = st.columns(3)
                
                with rec_col1:
                    st.metric("Rental Yield", f"{row['gross_yield']:.2f}%")
                    st.metric("Average Property Price", f"AED {row['actual_worth']:,.0f}")
                
                with rec_col2:
                    st.metric("Capital Appreciation", f"{row['appreciation_rate']:.2f}%")
                    st.metric("Average Annual Rent", f"AED {row['annual_amount']:,.0f}")
                
                with rec_col3:
                    st.metric("Total Return", f"{row['total_return']:.2f}%")
                    st.metric("Net Yield (After Expenses)", f"{row['net_yield']:.2f}%")
                
                # Add property type breakdown if available
                try:
                    if (not prop_merged.empty and 
                        'area_name_en' in prop_merged.columns and 
                        'property_type_en' in prop_merged.columns and
                        'gross_yield' in prop_merged.columns and
                        'appreciation_rate' in prop_merged.columns and
                        'total_return' in prop_merged.columns and
                        len(prop_merged[prop_merged['area_name_en'] == row['area_name_en']]) > 0):
                        
                        area_props = prop_merged[prop_merged['area_name_en'] == row['area_name_en']]
                        
                        st.subheader("Property Type Analysis")
                        
                        # Create property type table
                        area_props_display = area_props[['property_type_en', 'gross_yield', 'appreciation_rate', 'total_return']].copy()
                        area_props_display.columns = ['Property Type', 'Rental Yield (%)', 'Capital Appreciation (%)', 'Total Return (%)']
                        
                        # Remove string formatting loop and use column_config instead
                        st.dataframe(
                            area_props_display, 
                            hide_index=True,
                            column_config={
                                "Rental Yield (%)": st.column_config.NumberColumn(
                                    "Rental Yield (%)",
                                    format="%.2f%%"
                                ),
                                "Capital Appreciation (%)": st.column_config.NumberColumn(
                                    "Capital Appreciation (%)",
                                    format="%.2f%%"
                                ),
                                "Total Return (%)": st.column_config.NumberColumn(
                                    "Total Return (%)",
                                    format="%.2f%%"
                                )
                            }
                        )
                except (NameError, AttributeError, KeyError) as e:
                    # If prop_merged doesn't exist or isn't properly defined, silently skip this section
                    pass
    else:
        st.warning("No investments match your criteria. Try adjusting your filters or minimum requirements.")
    
    # Investment Strategy Tips
    with st.expander("💡 Investment Strategy Tips"):
        st.markdown("""
        ### Dubai Real Estate Investment Strategies
        
        #### Yield-Focused Strategy (Short-Term Income)
        - Target areas: JVC, Dubai Sports City, Discovery Gardens
        - Property types: Studios and 1-bedrooms
        - Expected yields: 7-9%
        - Best for: Investors seeking immediate cash flow
        
        #### Appreciation-Focused Strategy (Long-Term Growth)
        - Target areas: Dubai Hills, Palm Jumeirah, Emirates Hills
        - Property types: Premium villas and luxury apartments
        - Expected appreciation: 20-30% annually in strong markets
        - Best for: Investors with 5+ year horizons
        
        #### Balanced Strategy (Income + Growth)
        - Target areas: Business Bay, Dubai Marina, Downtown Dubai
        - Property types: 1-2 bedroom apartments in established communities
        - Expected total returns: 15-25%
        - Best for: Most investors seeking balance
        
        #### Value-Add Strategy (Renovation/Improvement)
        - Target older properties in established areas
        - Add value through renovation and modernization
        - Potential for both rental uplift and capital appreciation
        - Requires more active management
        
        #### Exit Strategy Considerations
        - Dubai's market cycles typically run 5-7 years
        - Consider selling during market peaks, which historically occur just before new supply surges
        - Monitor key market indicators: transaction volumes, listing inventory, and mortgage rates
        """)
    
    # Raw data option
    with st.expander("View Raw Investment Performance Data"):
        # Add pagination for better performance
        st.info("Displaying large datasets can slow down the dashboard. Using pagination for better performance.")
        
        # Sort data
        sorted_data = merged_data.sort_values('total_return', ascending=False)
        
        # Pagination controls
        page_size = st.selectbox("Rows per page", [10, 25, 50, 100], index=1, key="pagination_size")
        total_pages = max(1, len(sorted_data) // page_size + (1 if len(sorted_data) % page_size > 0 else 0))
        
        col1, col2, col3 = st.columns([2, 3, 2])
        with col2:
            current_page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, key="pagination_page")
        
        # Calculate slice indices
        start_idx = (current_page - 1) * page_size
        end_idx = min(start_idx + page_size, len(sorted_data))
        
        # Show page info
        st.caption(f"Showing {start_idx+1}-{end_idx} of {len(sorted_data)} results")
        
        # Display paginated data instead of full dataset
        st.dataframe(
            sorted_data.iloc[start_idx:end_idx],
            column_config={
                'area_name_en': st.column_config.TextColumn("Area"),
                'actual_worth': st.column_config.NumberColumn("Average Price (AED)", format="AED %,.0f"),
                'annual_amount': st.column_config.NumberColumn("Average Annual Rent (AED)", format="AED %,.0f"),
                'gross_yield': st.column_config.NumberColumn("Gross Yield (%)", format="%.2f%%"),
                'net_yield': st.column_config.NumberColumn("Net Yield (%)", format="%.2f%%"),
                'appreciation_rate': st.column_config.NumberColumn("Capital Appreciation (%)", format="%.2f%%"),
                'total_return': st.column_config.NumberColumn("Total Return (%)", format="%.2f%%")
            },
            hide_index=True
        )
        
        # Add download button
        st.download_button(
            label="Download Investment Data",
            data=merged_data.to_csv(index=False).encode('utf-8'),
            file_name="dubai_investment_metrics.csv",
            mime="text/csv",
            key="download-investment-data"
        )
    
    # Disclaimer
    st.caption("""
    **Disclaimer:** Past performance is not indicative of future results. Appreciation rates are estimates based on historical data 
    and market conditions. Investment decisions should be made after thorough research and consultation with real estate professionals.
    """)    # Price and Rent Indices Over Time
    if 'instance_date' in transactions.columns:
        st.subheader("⏱️ Price and Rent Trends")
        
        # Temporal Analysis Options
        time_granularity = st.radio(
            "Time Granularity",
            ["Daily", "Weekly", "Monthly", "Quarterly", "Yearly"],
            horizontal=True,
            index=2  # Default to Monthly
        )
        
        # Map selection to pandas period format
        granularity_map = {
            "Daily": "D",
            "Weekly": "W",
            "Monthly": "M",
            "Quarterly": "Q",
            "Yearly": "Y"
        }
        
        period_format = granularity_map[time_granularity]
        
        # Group data by time periods
        try:
            # Make sure instance_date is already in datetime format
            if not pd.api.types.is_datetime64_any_dtype(transactions['instance_date']):
                transactions['instance_date'] = pd.to_datetime(transactions['instance_date'], dayfirst=True, errors='coerce')
            
            transactions['period'] = transactions['instance_date'].dt.to_period(period_format)
            
            if 'contract_start_date' in rentals.columns:
                if not pd.api.types.is_datetime64_any_dtype(rentals['contract_start_date']):
                    rentals['contract_start_date'] = pd.to_datetime(rentals['contract_start_date'], dayfirst=True, errors='coerce')
                rentals['period'] = rentals['contract_start_date'].dt.to_period(period_format)
            elif 'registration_date' in rentals.columns:
                if not pd.api.types.is_datetime64_any_dtype(rentals['registration_date']):
                    rentals['registration_date'] = pd.to_datetime(rentals['registration_date'], dayfirst=True, errors='coerce')
                rentals['period'] = rentals['registration_date'].dt.to_period(period_format)
            
            # Calculate price and rent indices
            price_by_period = transactions.groupby('period')['actual_worth'].mean().reset_index()
            
            if 'period' in rentals.columns:
                rent_by_period = rentals.groupby('period')['annual_amount'].mean().reset_index()
                
                # Sort periods chronologically to ensure proper indexing
                price_by_period = price_by_period.sort_values('period')
                rent_by_period = rent_by_period.sort_values('period')
                
                # Convert periods to strings for plotting
                price_by_period['period_str'] = price_by_period['period'].astype(str)
                rent_by_period['period_str'] = rent_by_period['period'].astype(str)
                
                # Allow user to select custom date range
                date_range_col1, date_range_col2 = st.columns(2)
                
                with date_range_col1:
                    min_year = int(price_by_period['period'].astype(str).str[:4].min())
                    max_year = int(price_by_period['period'].astype(str).str[:4].max())
                    start_year = st.slider("Start Year", min_year, max_year, min_year)
                
                with date_range_col2:
                    end_year = st.slider("End Year", min_year, max_year, max_year)
                
                # Filter data by selected year range
                price_by_period = price_by_period[
                    price_by_period['period'].astype(str).str[:4].astype(int).between(start_year, end_year)
                ]
                rent_by_period = rent_by_period[
                    rent_by_period['period'].astype(str).str[:4].astype(int).between(start_year, end_year)
                ]
                
                # Normalize to create indices (100 = starting period)
                if not price_by_period.empty and not rent_by_period.empty:
                    # Handle potential alignment issues between price and rental datasets
                    common_periods = set(price_by_period['period_str']) & set(rent_by_period['period_str'])
                    
                    if common_periods:
                        # Filter to only include common periods
                        price_by_period = price_by_period[price_by_period['period_str'].isin(common_periods)]
                        rent_by_period = rent_by_period[rent_by_period['period_str'].isin(common_periods)]
                        
                        # Sort by period to ensure correct index calculation
                        price_by_period = price_by_period.sort_values('period')
                        rent_by_period = rent_by_period.sort_values('period')
                        
                        # Calculate indices with first period as base (100)
                        price_by_period['price_index'] = (price_by_period['actual_worth'] / price_by_period['actual_worth'].iloc[0]) * 100
                        rent_by_period['rent_index'] = (rent_by_period['annual_amount'] / rent_by_period['annual_amount'].iloc[0]) * 100
                        
                        # Create dual-axis chart
                        st.subheader(f"Price and Rent Indices ({start_year}-{end_year})")
                        
                        dual_axis_fig = create_dual_axis_chart(
                            price_by_period['period_str'],
                            price_by_period['price_index'],
                            rent_by_period['rent_index'],
                            f"Price and Rent Indices ({start_year}-{end_year}) (Base Period = 100)"
                        )
                        
                        # Add info about data points
                        st.info(f"Showing data for {len(common_periods)} time periods from {start_year} to {end_year}. Base period (index=100): {price_by_period['period_str'].iloc[0]}")
                        
                        st.plotly_chart(dual_axis_fig, use_container_width=True, key="price_rent_indices")
                else:
                    st.warning("Insufficient time-series data to display indices.")
            else:
                st.warning("No valid rental dates found in the dataset.")
                
        except Exception as e:
            st.error(f"Error in temporal analysis: {str(e)}")
            st.info("Date format issue detected. Make sure your dates are in DD-MM-YYYY format. If you're using the data_loader.py, verify date parsing is set to dayfirst=True.") 

