import streamlit as st
import pandas as pd
from pathlib import Path
from huggingface_hub import hf_hub_download


st.set_page_config(
    page_title='Rental Yield Calculator',
    page_icon='logo.png',
    layout='wide',
    menu_items=None
)
@st.cache_data()
def load_sales_data():
    """Download and load Sales data from Hugging Face."""
    filename = "Sales.csv"
    repo_id = "lemoninabag/Sales"
    
    hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        repo_type="dataset",
        local_dir="./data",  
        token=st.secrets["hf_key"]  
    )
    
    file_path = Path('./data') / filename
    real_estate_df = pd.read_csv(file_path)
    
    real_estate_df['instance_date'] = pd.to_datetime(real_estate_df['instance_date'])
    real_estate_df['master_project_en'] = real_estate_df['master_project_en'].str.strip()
    real_estate_df['property_sub_type_en'] = real_estate_df['property_sub_type_en'].str.strip()
    
    return real_estate_df

@st.cache_data()
def load_rental_data():
    """Download and load Rentals data from Hugging Face."""
    filename = "Rentals.csv"
    repo_id = "lemoninabag/Rentals"
    
    hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        repo_type="dataset",
        local_dir="./data",  
        token=st.secrets["hf_key"]  
    )
    
    file_path = Path('./data') / filename
    rental_df = pd.read_csv(file_path)
    
    rental_df['contract_start_date'] = pd.to_datetime(rental_df['contract_start_date'])
    rental_df['master_project_en'] = rental_df['master_project_en'].str.strip()
    rental_df['ejari_property_type_en'] = rental_df['ejari_property_type_en'].str.strip()
    rental_df['ejari_property_sub_type_id'] = rental_df['ejari_property_sub_type_id'].str.strip()
    
    return rental_df

sales_data = load_sales_data()
rental_data = load_rental_data()

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 0.75rem;  }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Rental Yield Calculator")

time_periods = [1, 3, 6, 12, 24, 36, 60]
months_back = st.select_slider(
    'Time Period',
    options=time_periods,
    value=12,  
    format_func=lambda x: f"{x} month{'s' if x > 1 else ''}" if x < 12 else f"{x // 12} year{'s' if x // 12 > 1 else ''}"
)

col1, col2 = st.columns([1, 2])

with col1:
    area_options = sorted(sales_data['master_project_en'].dropna().unique())
    default_index = area_options.index('Business Bay')
    selected_area = st.selectbox("Select Area / Project:", area_options, index=default_index)

    property_type_options = sales_data['property_sub_type_en'].unique()
    selected_property_type = st.selectbox("Property Type:", property_type_options).strip() 
    
    rooms_options = sorted(sales_data['rooms_en'].unique())
    selected_rooms = st.selectbox("Rooms:", rooms_options, index=0).strip()  

with col2:
    current_date = pd.Timestamp.today()
    min_date = current_date - pd.DateOffset(months=months_back)

    filtered_sales_data = sales_data[
        (sales_data['master_project_en'] == selected_area) &
        (sales_data['property_sub_type_en'] == selected_property_type) &
        (sales_data['rooms_en'] == selected_rooms) &
        (sales_data['instance_date'] >= min_date)
    ]

    filtered_rental_data = rental_data[
        (rental_data['master_project_en'] == selected_area) &
        (rental_data['ejari_property_type_en'] == selected_property_type) &
        (rental_data['ejari_property_sub_type_id'] == selected_rooms) &
        (rental_data['contract_start_date'] >= min_date)
    ]

    if filtered_sales_data.empty or filtered_rental_data.empty:
        st.error("No sales or rental data available for the selected area, property type, or room type within the selected time period.")
    else:
        num_sales_records = len(filtered_sales_data)
        if num_sales_records > 0:
            avg_sale_price = filtered_sales_data['actual_worth'].mean()
            filtered_sales_data['instance_date'] = filtered_sales_data['instance_date'].dt.to_timestamp()
            filtered_sales_data = filtered_sales_data.groupby(filtered_sales_data['instance_date'].dt.to_period("M")).mean().reset_index()
            
        else:
            avg_sale_price = 0

        num_rental_records = len(filtered_rental_data)
        if num_rental_records > 0:
            avg_rent_price = filtered_rental_data['annual_amount'].mean()
        else:
            avg_rent_price = 0

        if avg_rent_price > 0 and avg_sale_price > 0:
            gross_rental_yield = (avg_rent_price / avg_sale_price) * 100
        else:
            gross_rental_yield = 0

        metric_col1, metric_col2, metric_col3 = st.columns(3)

        with metric_col1:
            st.markdown(
                f"""
                <div style="background-color:#101726;padding:14px;border-radius:10px;text-align:center">
                    <h3 style="color:#C8CAD0;font-size:25px;">Gross Rental Yield</h3>
                    <p style="color:#C8CAD0;font-size:24px;">{gross_rental_yield:.2f}%</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        with metric_col2:
            st.markdown(
                f"""
                <div style="background-color:#C8CAD0;padding:5px;border-radius:10px;text-align:center">
                    <h3 style="color:#101726;">Avg. Sale Price</h3>
                    <p style="color:#101726;font-size:24px;">AED {avg_sale_price:,.2f}</p>
                    <p style="color:#101726;font-size:15px;">...based on {num_sales_records} sales.</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        with metric_col3:
            st.markdown(
                f"""
                <div style="background-color:#C8CAD0;padding:5px;border-radius:10px;text-align:center">
                    <h3 style="color:#101726;">Avg. Rent Price</h3>
                    <p style="color:#101726;font-size:24px;">AED {avg_rent_price:,.2f}</p>
                    <p style="color:#101726;font-size:15px;">...based on {num_rental_records} rental contracts.</p>
                </div>
                """,
                unsafe_allow_html=True
            )

st.subheader("Compare Rental Yields Across Multiple Areas")
st.write("Graph will be updated to add the same filters like property type/rooms")

selected_comparison_areas = st.multiselect("Select Area(s)/Project(s):", area_options, default=["Business Bay"])

comparison_data = pd.DataFrame()

for comparison_area in selected_comparison_areas:
    comp_sales_data = sales_data[
        (sales_data['master_project_en'] == comparison_area) &
        (sales_data['property_sub_type_en'] == selected_property_type) &
        (sales_data['rooms_en'] == selected_rooms) &
        (sales_data['instance_date'] >= min_date)
    ]

    comp_rental_data = rental_data[
        (rental_data['master_project_en'] == comparison_area) &
        (rental_data['ejari_property_type_en'] == selected_property_type) &
        (rental_data['ejari_property_sub_type_id'] == selected_rooms) &
        (rental_data['contract_start_date'] >= min_date)
    ]

    if not comp_sales_data.empty:
        comp_sales_data = comp_sales_data.groupby(comp_sales_data['instance_date'].dt.to_period("M")).mean().reset_index()
        comp_sales_data['instance_date'] = comp_sales_data['instance_date'].dt.to_timestamp()
        comp_avg_sale_price = comp_sales_data['actual_worth'].mean()
    else:
        comp_avg_sale_price = 0

    if not comp_rental_data.empty:
        comp_avg_rent_price = comp_rental_data['annual_amount'].mean()
    else:
        comp_avg_rent_price = 0

    if comp_avg_rent_price > 0 and comp_avg_sale_price > 0:
        comp_gross_rental_yield = (comp_avg_rent_price / comp_avg_sale_price) * 100
    else:
        comp_gross_rental_yield = 0

    if not comp_sales_data.empty:
        comp_sales_data['Gross Rental Yield'] = (comp_avg_rent_price / comp_sales_data['actual_worth']) * 100
        comp_sales_data['Area'] = comparison_area  # Add a column for area
        comparison_data = pd.concat([comparison_data, comp_sales_data[['instance_date', 'Gross Rental Yield', 'Area']]])

if not comparison_data.empty:
    comparison_chart_data = comparison_data.pivot(index='instance_date', columns='Area', values='Gross Rental Yield')
    st.line_chart(comparison_chart_data, use_container_width=True)

st.write("Notes:")
st.write("Latest sales data: 30 Sept. 2024,")
st.write("Latest rental data: 04 Oct. 2024")
