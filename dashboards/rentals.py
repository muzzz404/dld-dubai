import streamlit as st
import pandas as pd
import plotly.express as px

def show_rentals_dashboard(rentals):
    st.header("🏢 Rental Market Performance Dashboard")
    st.markdown("""This dashboard provides comprehensive analytics of Dubai's rental market, 
                highlighting tenant patterns, property preferences, and price trends across different areas.""")
    
    # Market insights container
    with st.expander("📈 Rental Market Insights", expanded=True):
        st.info("""
        **2024-2025 Rental Market Context:**
        - Dubai's rental market has seen steady growth with average rents increasing by ~20% in 2024
        - High-demand areas include Dubai Marina, Downtown, JVC, and Business Bay
        - Studio and 1-bedroom units account for ~60% of all rental contracts
        - Average annual rent reached AED 95,000 in Q1 2025
        - Residential units dominate with ~85% of rental contracts
        """)
    
    # Key Metrics section
    st.subheader("🔑 Key Rental Metrics")
    
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    
    with metric_col1:
        total_contracts = len(rentals)
        st.metric(
            "Total Rental Contracts", 
            f"{total_contracts:,}",
            help="Total number of rental contracts registered in Dubai"
        )
    
    with metric_col2:
        total_annual_amount = rentals['annual_amount'].sum()
        st.metric(
            "Total Annual Rental Value (AED)", 
            f"{total_annual_amount:,.2f}",
            help="Aggregate annual rental value across all contracts"
        )
    
    with metric_col3:
        avg_annual_rent = rentals['annual_amount'].mean()
        st.metric(
            "Average Annual Rent (AED)", 
            f"{avg_annual_rent:,.2f}",
            help="Mean annual rental price across all properties"
        )
    
    # Additional metrics
    metric_col4, metric_col5, metric_col6 = st.columns(3)
    
    with metric_col4:
        median_rent = rentals['annual_amount'].median()
        st.metric(
            "Median Annual Rent (AED)",
            f"{median_rent:,.2f}",
            help="Median annual rental price, which removes the effect of extreme values"
        )
    
    with metric_col5:
        highest_rent = rentals['annual_amount'].max()
        st.metric(
            "Highest Annual Rent (AED)",
            f"{highest_rent:,.2f}",
            help="The highest annual rental price in the dataset"
        )
    
    with metric_col6:
        unique_areas = rentals['area_name_en'].nunique()
        st.metric(
            "Active Rental Areas",
            f"{unique_areas}",
            help="Number of distinct areas with rental contracts"
        )
    
    # Interactive Filters for the rental dashboard
    st.subheader("📊 Rental Filters")
    
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        areas = ['All'] + sorted(rentals['area_name_en'].dropna().unique().tolist())
        selected_area = st.selectbox("Area", areas, key="rental_area_filter")
    
    with filter_col2:
        property_types = ['All'] + sorted(rentals['ejari_property_sub_type_en'].dropna().unique().tolist())
        selected_property_type = st.selectbox("Property Type", property_types, key="rental_type_filter")
    
    # Apply filters
    filtered_rentals = rentals.copy()
    
    if selected_area != 'All':
        filtered_rentals = filtered_rentals[filtered_rentals['area_name_en'] == selected_area]
    
    if selected_property_type != 'All':
        filtered_rentals = filtered_rentals[filtered_rentals['ejari_property_sub_type_en'] == selected_property_type]
    
    # Area Analysis
    st.subheader("📍 Rental Area Analysis")
    
    area_col1, area_col2 = st.columns(2)
    
    with area_col1:
        # Top rental areas by contract count
        area_counts = filtered_rentals['area_name_en'].value_counts().head(10).reset_index()
        area_counts.columns = ['Area', 'Number of Contracts']
        
        fig = px.bar(
            area_counts, 
            x='Number of Contracts',
            y='Area',
            title="Top 10 Areas by Rental Contract Count",
            color='Number of Contracts',
            color_continuous_scale=px.colors.sequential.Viridis,
            orientation='h'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with area_col2:
        # Average rent by area
        avg_rent_by_area = filtered_rentals.groupby('area_name_en')['annual_amount'].mean().reset_index()
        avg_rent_by_area.columns = ['Area', 'Average Annual Rent']
        avg_rent_by_area = avg_rent_by_area.sort_values('Average Annual Rent', ascending=False).head(10)
        
        fig = px.bar(
            avg_rent_by_area, 
            x='Average Annual Rent',
            y='Area',
            title="Top 10 Areas by Average Annual Rent",
            color='Average Annual Rent',
            color_continuous_scale=px.colors.sequential.Plasma,
            orientation='h'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Property Type Analysis
    st.subheader("🏠 Property Type Analysis")
    
    prop_col1, prop_col2 = st.columns(2)
    
    with prop_col1:
        # Distribution of property types
        property_type_counts = filtered_rentals['ejari_property_sub_type_en'].value_counts().reset_index()
        property_type_counts.columns = ['Property Type', 'Count']
        
        fig = px.pie(
            property_type_counts.head(10), 
            values='Count', 
            names='Property Type',
            title="Distribution of Rental Property Types",
            color_discrete_sequence=px.colors.qualitative.Set3,
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with prop_col2:
        # Average rent by property type
        avg_rent_by_type = filtered_rentals.groupby('ejari_property_sub_type_en')['annual_amount'].mean().reset_index()
        avg_rent_by_type.columns = ['Property Type', 'Average Annual Rent']
        avg_rent_by_type = avg_rent_by_type.sort_values('Average Annual Rent', ascending=False).head(10)
        
        fig = px.bar(
            avg_rent_by_type, 
            x='Average Annual Rent',
            y='Property Type',
            title="Average Annual Rent by Property Type",
            color='Average Annual Rent',
            color_continuous_scale=px.colors.sequential.Plasma,
            orientation='h'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Rent Distribution Analysis
    st.subheader("💰 Rent Distribution Analysis")
    
    # Histogram of annual rents
    fig = px.histogram(
        filtered_rentals,
        x="annual_amount",
        nbins=50,
        title="Distribution of Annual Rental Amounts",
        labels={"annual_amount": "Annual Rent (AED)"},
        color_discrete_sequence=['#3366cc']
    )
    fig.update_layout(bargap=0.1)
    st.plotly_chart(fig, use_container_width=True)
    
    # Rental Value Segments
    rent_segments = pd.cut(
        filtered_rentals['annual_amount'], 
        bins=[0, 50000, 100000, 150000, 200000, 300000, 500000, float('inf')],
        labels=['Up to 50K', '50K-100K', '100K-150K', '150K-200K', '200K-300K', '300K-500K', '500K+']
    ).value_counts().reset_index()
    rent_segments.columns = ['Rent Segment', 'Count']
    
    fig = px.bar(
        rent_segments,
        x='Rent Segment',
        y='Count',
        title="Rental Contracts by Price Segment",
        color='Count',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Area-wise Rental Metrics Table
    st.subheader("📊 Area-wise Rental Metrics")
    
    # Group by area and calculate metrics
    if not filtered_rentals.empty:
        area_metrics = []
        
        for area, group in filtered_rentals.groupby('area_name_en'):
            metrics = {
                'Area': area,
                'Contract Count': len(group),
                'Average Rent': group['annual_amount'].mean(),
                'Median Rent': group['annual_amount'].median(),
                'Highest Rent': group['annual_amount'].max(),
                'Lowest Rent': group['annual_amount'].min(),
                'Total Rental Value': group['annual_amount'].sum()
            }
            area_metrics.append(metrics)
        
        # Create DataFrame from metrics
        area_metrics_df = pd.DataFrame(area_metrics)
        
        # Sort by contract count by default
        area_metrics_df = area_metrics_df.sort_values('Contract Count', ascending=False)
        
        # Define column configurations for better sorting and formatting
        area_column_config = {
            'Area': st.column_config.TextColumn(
                "Area",
                width="medium"
            ),
            'Contract Count': st.column_config.NumberColumn(
                "Contract Count",
                format="%d",
                width="small"
            ),
            'Average Rent': st.column_config.NumberColumn(
                "Average Rent",
                format="AED %.2f",
                width="medium"
            ),
            'Median Rent': st.column_config.NumberColumn(
                "Median Rent",
                format="AED %.2f",
                width="medium"
            ),
            'Highest Rent': st.column_config.NumberColumn(
                "Highest Rent",
                format="AED %.2f",
                width="medium"
            ),
            'Lowest Rent': st.column_config.NumberColumn(
                "Lowest Rent",
                format="AED %.2f",
                width="medium"
            ),
            'Total Rental Value': st.column_config.NumberColumn(
                "Total Rental Value",
                format="AED %.2f",
                width="medium"
            )
        }
        
        # Display the table with proper column configuration for sorting
        st.dataframe(
            area_metrics_df,
            column_config=area_column_config,
            use_container_width=True,
            hide_index=True
        )
        
        # Add download button for the table
        csv = area_metrics_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download Area Rental Metrics",
            csv,
            "area_rental_metrics.csv",
            "text/csv",
            key="download-area-rental-metrics"
        )
    
    # Property Type Metrics Table
    st.subheader("🏢 Property Type Rental Metrics")
    
    # Group by property type and calculate metrics
    if not filtered_rentals.empty:
        property_metrics = []
        
        for prop_type, group in filtered_rentals.groupby('ejari_property_sub_type_en'):
            metrics = {
                'Property Type': prop_type,
                'Contract Count': len(group),
                'Average Rent': group['annual_amount'].mean(),
                'Median Rent': group['annual_amount'].median(),
                'Highest Rent': group['annual_amount'].max(),
                'Lowest Rent': group['annual_amount'].min(),
                'Total Rental Value': group['annual_amount'].sum()
            }
            property_metrics.append(metrics)
        
        # Create DataFrame from metrics
        property_metrics_df = pd.DataFrame(property_metrics)
        
        # Sort by contract count by default
        property_metrics_df = property_metrics_df.sort_values('Contract Count', ascending=False)
        
        # Define column configurations for better sorting and formatting
        property_column_config = {
            'Property Type': st.column_config.TextColumn(
                "Property Type",
                width="medium"
            ),
            'Contract Count': st.column_config.NumberColumn(
                "Contract Count",
                format="%d",
                width="small"
            ),
            'Average Rent': st.column_config.NumberColumn(
                "Average Rent",
                format="AED %.2f",
                width="medium"
            ),
            'Median Rent': st.column_config.NumberColumn(
                "Median Rent",
                format="AED %.2f",
                width="medium"
            ),
            'Highest Rent': st.column_config.NumberColumn(
                "Highest Rent",
                format="AED %.2f",
                width="medium"
            ),
            'Lowest Rent': st.column_config.NumberColumn(
                "Lowest Rent",
                format="AED %.2f",
                width="medium"
            ),
            'Total Rental Value': st.column_config.NumberColumn(
                "Total Rental Value",
                format="AED %.2f",
                width="medium"
            )
        }
        
        # Display the table with proper column configuration
        st.dataframe(
            property_metrics_df,
            column_config=property_column_config,
            use_container_width=True,
            hide_index=True
        )
        
        # Add download button for the table
        csv = property_metrics_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download Property Type Rental Metrics",
            csv,
            "property_type_rental_metrics.csv",
            "text/csv",
            key="download-property-rental-metrics"
        )
    
    # Rental Market Insights
    st.subheader("💡 Rental Market Insights")
    
    insights_col1, insights_col2, insights_col3 = st.columns(3)
    
    with insights_col1:
        st.info("""
        **Rising Rental Yields**
        
        Dubai's rental yields average 6-8%, outperforming many global markets. 
        Apartments typically deliver higher yields than villas, with studios and 
        1-bedrooms offering the best returns for investors.
        """)
    
    with insights_col2:
        st.info("""
        **Seasonal Demand Patterns**
        
        Rental activity typically peaks in Q3 and Q4, driven by new resident 
        arrivals and educational calendar cycles. This creates opportunities 
        for timing lease renewals and new investments.
        """)
    
    with insights_col3:
        st.info("""
        **Long-term vs. Short-term**
        
        Short-term rentals command 30-40% premium over long-term leases in 
        tourist-favored areas, though they require more management and have 
        higher vacancy risks. Downtown, Marina, and Palm Jumeirah lead this segment.
        """)
    
    # Raw rental data table
    st.subheader("📋 Rental Contract Data")
    
    # Show raw data with pagination
    st.dataframe(filtered_rentals, use_container_width=True)
    
    # Add download button for filtered data
    st.download_button(
        label="Download Filtered Rental Data",
        data=filtered_rentals.to_csv(index=False).encode('utf-8'),
        file_name='dubai_rental_contracts_filtered.csv',
        mime='text/csv',
    )
    
    # Dataset information
    st.caption(f"Rental dataset includes {len(rentals)} contracts across {rentals['area_name_en'].nunique()} areas in Dubai") 