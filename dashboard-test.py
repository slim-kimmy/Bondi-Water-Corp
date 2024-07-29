import ast
import time
import pytz
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import altair as alt
import alertlabAPI as al
import streamlit_toggle as tog


###########################################
def get_60_day_monday_average(sensor_list):
    if len(sensor_list) > 0:
        # Get today's date and convert to unix time
        today = datetime.now()
        today_unix = int(time.mktime(today.timetuple()))
        # Get 60 days ago date and convert to unix time
        sixty_days_ago = today - timedelta(days=60)
        sixty_days_ago_unix = int(time.mktime(sixty_days_ago.timetuple()))
        # Query for all the sensors at the location
        sixty_day_dataframes = al.get_list_timeseries(sensor_list, start_date=sixty_days_ago_unix, end_date=today_unix, rate="h", series="water")
        # Sum the dataframes
        cumulative_sixty_day_consumption = al.sum_columns(sixty_day_dataframes, ['series'])
        # Convert the datetime strings into Datetime objects and adjust for UTC to EDT
        cumulative_sixty_day_consumption['Datetime'] = pd.to_datetime(cumulative_sixty_day_consumption['Datetime'])
        # Filter the data for Datetime values that are Mondays at 3AM EDT
        filtered_data = cumulative_sixty_day_consumption[(cumulative_sixty_day_consumption['Datetime'].dt.dayofweek == 0) & (cumulative_sixty_day_consumption['Datetime'].dt.hour == 3)]
        # Calculate the mean and median of the series column for the filtered data
        mean_series = filtered_data['series'].mean()
        median_series = filtered_data['series'].median()
        return mean_series, median_series, cumulative_sixty_day_consumption
    
def get_this_weeks_average():
    pass

def make_timeseries_chart(queried_sensors, start_date, end_date, rate, series):
    if len(queried_sensors) != 0:
        time_series_data = al.get_list_timeseries(queried_sensors, start_date=start_date_unix, end_date=end_date_unix, rate=rate, series=series)
        # Sum the displayed dataframes
        cumulative_timeseries_data = al.sum_columns(time_series_data, ['series'])
        # Generate the chart
        st.bar_chart(cumulative_timeseries_data, x="Datetime", y="series", x_label="Date", y_label="Water Consumption", height=800)
        st.write(cumulative_timeseries_data)

def get_location_dataframes(location_id):
    pass
###########################################

    
# Settings
st.set_page_config(
    page_title="Bondi Water Corp",
    page_icon=":potable_water:",
    layout="wide",
    initial_sidebar_state="expanded")
alt.themes.enable("dark")
# Read in existing CSV, these will be swapped every refresh
if 'df' not in st.session_state:
    initial_load_dataframe = al.main()
    # Creating unique ID's from a concatenation of address and name values
    initial_load_dataframe["unique"] = initial_load_dataframe["address"] + " " + initial_load_dataframe["name"]
    # Stashing in session
    st.session_state.df = initial_load_dataframe
df = st.session_state.df



with st.sidebar:
    # Dashboard title
    st.markdown("""
    <style>
    .big-font {
        font-size:40px !important;
        color: #122B46; 
    }
    .kpi-font {
        font-size:35px !important;
        color: #ed0919; 
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<p class="big-font">Water Consumption Dashboard</p>', unsafe_allow_html=True)

    # Address Filter Dropdown
    address_list = list(df.unique.unique())[::-1]
    selected_address = st.selectbox('Select Property:', address_list)
    df_selected_address = df[df.unique == selected_address]
    st.write(df_selected_address)
    # Calendar widget 
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")
    start_date_unix = str(datetime.strptime(str(start_date), "%Y-%m-%d").timestamp())
    end_date_unix = str(datetime.strptime(str(end_date), "%Y-%m-%d").timestamp())

    # Rate selection
    rate_switch = tog.st_toggle_switch(label="Hour / Minute")
    rate = "h"
    if rate_switch == True:
        rate="m"
    # Series selection
    series_switch = tog.st_toggle_switch(label="Water / Temperature")
    series = "water"
    if series_switch == True:
        series="temp"
    # List of sensors as buttons
    buttons = []
    sensor_list = df_selected_address["sensors"].iloc[0]
    for i in sensor_list:
        buttons.append(tog.st_toggle_switch(label=i,
                                            key=i))
    for button in buttons:
        if button:
            pass
    # Time series data list
    queried_sensors = []
    for sensor_id, button in zip(sensor_list, buttons):
        if button == True:
            queried_sensors.append(sensor_id)        
    # Initiate Query and get list of dataframes from selected sensors
    submitted = st.button("Query")


# Displays
    # KPI's
mean, median, df2 = get_60_day_monday_average(sensor_list)


st.markdown(
    """
<style>
[data-testid="stMetricValue"] {
    font-size: 100px;
}
div[data-testid="stMarkdownContainer"] > p {
    font-size: 35px;
}


</style>
""",
    unsafe_allow_html=True,
)


kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(
    label="Average Litres",
    value=round(mean)
)
kpi2.metric(
    label="Median Litres",
    value=round(median)
)
kpi3.metric(
    label="Past Weeks Avg",
    value = 999)


    # Timeseries chart
if submitted == True:
    # Function to make timeseries chart  
    make_timeseries_chart(queried_sensors, start_date_unix, end_date_unix, rate, series)




