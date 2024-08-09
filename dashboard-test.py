import ast
import time
import pytz
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import altair as alt
import apitesting as at
import alertlabAPI as al
import plotly.express as px
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
        # Filter the data for Datetime values that are Mondays between 1AM and 5AM EDT
        filtered_data = cumulative_sixty_day_consumption[#(cumulative_sixty_day_consumption['Datetime'].dt.dayofweek == 0) &
                                                         (cumulative_sixty_day_consumption['Datetime'].dt.hour >= 1) &
                                                         (cumulative_sixty_day_consumption['Datetime'].dt.hour <= 5)]
        # Calculate the mean and median of the series column for the filtered data
        mean_series = filtered_data['series'].mean()
        median_series = filtered_data['series'].median()
        return mean_series, median_series, cumulative_sixty_day_consumption

    
def get_this_weeks_average(sensor_list):
    if len(sensor_list) > 0:
        # Get today's date and convert to unix time
        today = datetime.now()
        today_unix = int(time.mktime(today.timetuple()))
        # Get 7 days ago date and convert to unix time
        seven_days_ago = today - timedelta(days=7)
        seven_days_ago_unix = int(time.mktime(seven_days_ago.timetuple()))
        # Query for all the sensors at the location
        seven_day_dataframes = al.get_list_timeseries(sensor_list, start_date=seven_days_ago_unix, end_date=today_unix, rate="h", series="water")
        # Sum the dataframes
        cumulative_seven_day_consumption = al.sum_columns(seven_day_dataframes, ['series'])
        # Convert the datetime strings into Datetime objects and adjust for UTC to EDT
        cumulative_seven_day_consumption['Datetime'] = pd.to_datetime(cumulative_seven_day_consumption['Datetime'])
        # Calculate the mean of the series column for the past week
        mean_series = cumulative_seven_day_consumption['series'].mean()
        return mean_series, cumulative_seven_day_consumption

    
def make_timeseries_chart(queried_sensors, start_date, end_date, rate, series):
    if len(queried_sensors) != 0:
        time_series_data = al.get_list_timeseries(queried_sensors, start_date=start_date_unix, end_date=end_date_unix, rate=rate, series=series)
        # Sum the displayed dataframes
        cumulative_timeseries_data = al.sum_columns(time_series_data, ['series'])
        # Casting data type for time as string
        #cumulative_timeseries_data["series"] = cumulative_timeseries_data["Datetime"].astype(str)
        cumulative_timeseries_data['series'] = cumulative_timeseries_data['series'].apply(lambda x: round(x))
        # Generate the chart
        st.bar_chart(cumulative_timeseries_data, x="Datetime", y="series", x_label="Datetime", y_label="Water Consumption", height=800)
        st.write(cumulative_timeseries_data)

def make_timeseries_chart(queried_sensors, start_date, end_date, rate, series):
    if len(queried_sensors) != 0:
        time_series_data = al.get_list_timeseries(queried_sensors, start_date=start_date_unix, end_date=end_date_unix, rate=rate, series=series)
        # Sum the displayed dataframes
        cumulative_timeseries_data = al.sum_columns(time_series_data, ['series'])
        # Casting data type for time as string
        #cumulative_timeseries_data["series"] = cumulative_timeseries_data["Datetime"].astype(str)
        cumulative_timeseries_data['series'] = cumulative_timeseries_data['series'].apply(lambda x: round(x))
        cumulative_timeseries_data['change'] = cumulative_timeseries_data['series'].pct_change().mul(100).round(2)
        # Create an outier free column
        cumulative_timeseries_data['normalized'] = cumulative_timeseries_data['series']
        Q1 = cumulative_timeseries_data['normalized'].quantile(0.25)
        Q3 = cumulative_timeseries_data['normalized'].quantile(0.75)
        IQR = Q3 - Q1
        # Define the bounds for outliers
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        median_value = cumulative_timeseries_data['normalized'].median()
        # Replace outliers with the median
        cumulative_timeseries_data['normalized'] = cumulative_timeseries_data['normalized'].apply(
            lambda x: median_value if x < lower_bound or x > upper_bound else x
        )
        # Generate the chart
        fig = px.bar(cumulative_timeseries_data, x="Datetime", y="series", height=500)
        fig2 = px.scatter(cumulative_timeseries_data, x="Datetime", y="normalized", height=800, trendline="ols", trendline_scope="overall", trendline_color_override="#d52b1e")
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig, theme="streamlit")
        st.plotly_chart(fig2, theme="streamlit")
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



# Set up initial authorization header
if "authorization_header" not in st.session_state:
    authorization_header = at.generate_new_authorization_header()
    st.session_state.authorization_header = authorization_header
authorization_header = st.session_state.authorization_header



# Read in existing CSV, these will be swapped every refresh
if 'df' not in st.session_state:
    # Load client list data
    initial_load_dataframe = al.main()
    # Load tombstone data from client list
    initial_load_tombstone_dataframe = at.get_tombstone_data(initial_load_dataframe, authorization_header)
    initial_parent_id_dataframe = at.get_parents_ids(initial_load_dataframe, authorization_header)
    #######
    # Creating unique ID's from a concatenation of address and name values
    initial_load_dataframe["unique"] = initial_load_dataframe["address"] + " " + initial_load_dataframe["name"]
    # Merge the parent ID dataframe with the initial load dataframe
    parent_dataframe = pd.merge(initial_load_dataframe, initial_parent_id_dataframe, on='_id')
    # Merge the next dataframe with the other
    tombstone_parent_dataframe = pd.merge(parent_dataframe, initial_load_tombstone_dataframe, on='_id')
    # Stashing in session
    st.session_state.df = tombstone_parent_dataframe
df = st.session_state.df


with st.sidebar:
    # Dashboard title
    st.markdown("""
    <style>
    .big-font {
        font-size:30px !important;
        color: #122B46; 
    }
    .kpi-font {
        font-size:25px !important;
        color: #ed0919; 
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="big-font">Water Consumption Dashboard</p>', unsafe_allow_html=True)
    # Parent Organization filter
    parent_list = sorted(list(df.parentNames.unique())[::-1])
    selected_address = st.selectbox('Select Organization:', parent_list)
    df_selected_parent = df[df.parentNames == selected_address]
    # Address Filter Dropdown
    address_list = list(df_selected_parent.name.unique())[::-1]
    selected_address = st.selectbox('Select Property:', address_list)
    df_selected_address = df[df.name == selected_address]
    # Calendar widget 
    default_date_last_week = datetime.today() - timedelta(days=7)
    start_date = st.date_input("Start Date", default_date_last_week)
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
    sensor_names = df_selected_address["sensor names"].iloc[0]
    for i in sensor_list:
        buttons.append(tog.st_toggle_switch(label=sensor_names[sensor_list.index(i)],
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
mean, median, cumulative_sixty_day_consumption = get_60_day_monday_average(sensor_list)
seven_day_mean, cumulative_seven_day_consumption  = get_this_weeks_average(sensor_list)
st.markdown(
    """
<style>
[data-testid="stMetricValue"] {
    font-size: 80px;
}
div[data-testid="stMarkdownContainer"] > p {
    font-size: 25px;
}


</style>
""",
    unsafe_allow_html=True,
)

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(
    label="60 Day 1-5AM (Avg)",
    value=round(mean)
)
kpi2.metric(
    label="60 Day 1-5AM (Med)",
    value=round(median)
)
kpi3.metric(
    label="Past Weeks Avg (l/h)",
    value = round(seven_day_mean)
)

    # Timeseries chart
if submitted == True:
    # Function to make timeseries chart  
    make_timeseries_chart(queried_sensors, start_date_unix, end_date_unix, rate, series)
    


