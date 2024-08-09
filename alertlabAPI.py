import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse as urlparse


def read_credentials(file_path="credentials.txt"):
    username = None
    password = None    
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if line.startswith('username:'):
                username = line.split('username:')[1].strip()
            elif line.startswith('password:'):
                password = line.split('password:')[1].strip()
    return username, password



def get_token(username, password):
    url = 'https://www.alertlabsdashboard.com/api/v3/login'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'user': username,
        'password': password
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 202: 
        print("Request was accepted.")
        response_json = response.json()
        print(response_json)
        # Extract the token from the response
        token = response_json.get("token")
        print("Access Token:", token)
    else:
        print(f"Failed to retrieve token. Status code: {response.status_code}")
    return token



def check_credential(file_path="token.txt"):
    # Read the content of the file
    with open(file_path, 'r') as file:
        content = file.read().strip()
    
    # Extract the token and date from the content
    token_part, date_part = content.split('date: ')
    token = token_part.split('token: ')[1].strip()
    date_str = date_part.strip()
    file_date = datetime.strptime(date_str, "%m/%d/%Y")
    # Calculate the difference between today's date and the file date
    today = datetime.now()
    date_difference = today - file_date
    # If the date is more than 29 days ago, get a new token and update the file
    if date_difference.days > 29:
        username, password = read_credentials()
        new_token = get_token(username, password)  # Assuming get_token() is defined elsewhere
        new_date_str = today.strftime("%m/%d/%Y")
        new_content = f"token: {new_token}\ndate: {new_date_str}"
        token = new_token
        # Write the new content to the file
        with open(file_path, 'w') as file:
            file.write(new_content)
    return token



def locations(token='$2b$08$7kPxAMomf57uw1hQWXY7je3h5pAGSilfGe.MRj4o7drjgY9Vj6BJ2'):
        # Get all locations test
    test_url = 'https://www.alertlabsdashboard.com/api/v3/dataModel/read/allLocations'
    test_headers = {
    'token': token
    }
    response = requests.get(test_url, headers=test_headers)
    response_json = response.json()
    return response_json["dataModel"]



def get_ongoing(location_id, token='$2b$08$7kPxAMomf57uw1hQWXY7je3h5pAGSilfGe.MRj4o7drjgY9Vj6BJ2'):
            # Get all locations test
    test_url = f'https://www.alertlabsdashboard.com/api/v3/dataModel/read/allSensorEventsAtLocation?locationID={location_id}'
    test_headers = {
    'token': token
    }
    response = requests.get(test_url, headers=test_headers)
    response_json = response.json()
    return response_json["dataModel"]



#Test 313747173737333821002b00
def get_timeseries(sensor_id="323747143531313928002000", start_date="1720119038", end_date="1720205438", rate="h", series="water"):
    test_url = f'https://www.alertlabsdashboard.com/api/v3/timeSeries/sensor/{sensor_id}?start={start_date}&end={end_date}&rate={rate}&series={series}'
    test_headers = {
    'token': '$2b$08$7kPxAMomf57uw1hQWXY7je3h5pAGSilfGe.MRj4o7drjgY9Vj6BJ2'
    }
    response = requests.get(test_url, headers=test_headers)
    response_json = response.json()
    values = response_json['value']
    # Create a DataFrame
    df = pd.DataFrame(values, columns=['time', 'series'])
    df['Datetime'] = pd.to_datetime(df['time'], unit='s') - timedelta(hours=4)
    return df



def get_list_timeseries(sensor_list, start_date="1720119038", end_date="1720205438", rate="h", series="water"):
    time_series_list = []
    for sensor in sensor_list:
        time_series_data = get_timeseries(sensor_id=sensor,
                                             start_date=start_date,
                                             end_date=end_date,
                                             rate=rate
                                            )
        if time_series_data.empty != True:
            time_series_list.append(time_series_data)
    return time_series_list



def get_properties_with_sensors(properties, token):
    for place in properties:
        location_id = place["_id"]
        sensors = get_ongoing(location_id, token)
        list_of_sensors = sensors[0]['sensors']
        # Use list comprehension to filter sensors
        sensors_at_location = [sensor["_id"] for sensor in list_of_sensors if sensor['type'] in {"FlowieO", "WaterMeter"}]
        sensor_names_at_location = [sensor["name"] for sensor in list_of_sensors if sensor['type'] in {"FlowieO", "WaterMeter"}]
        place["sensors"] = sensors_at_location
        place["sensor names"] = sensor_names_at_location
    return properties



LOGIN_API = 'https://www.alertlabsdashboard.com/oauth/login?client_id=AlertLabsLogin&state=login&redirect_uri=https://www.alertlabsdashboard.com&response_type=code'
TOKEN_API = 'https://www.alertlabsdashboard.com/oauth/AlertLabsLogin/tokenExchange'
COMPARISON_API = 'https://www.alertlabsdashboard.com/api/v2/aggregates/comparison'



# Handle token exchange token to get new access token
def generate_new_authorization_header():
    response = requests.post(LOGIN_API, json={
        "user": "ethank007@hotmail.com",
        "password": "Kimmy2002"
    })
    login_response = json.loads(response.text)
    if login_response['success'] == False:
        return
    parsed = urlparse.urlparse(login_response['redirectURI'])
    response = requests.post(TOKEN_API, data={
            "code": urlparse.parse_qs(parsed.query)['code'],
            "client_secret": "Siwe98EMfnL973Nner",
            "grant_type": "authorization_code",
            "client_id": "AlertLabsLogin"
        }, headers={
            "Content-Type": "application/x-www-form-urlencoded"
        })
    secret = json.loads(response.text)
    return secret['access_token']



# Return false if error, return json if successful
def getComparisonData(locationIDs):
    locationIDs = json.dumps({
        "locationIDs": locationIDs
    })
    response = requests.get(COMPARISON_API, params=locationIDs, headers={
        "authorization": generateNewAuthorizationHeader()
    })
    if response.status_code != 200:
        return False
    return json.loads(response.text)



def sum_columns(dataframes, column_names):
    if len(dataframes) > 1:
        # Initialize a dataframe with the structure of the first dataframe in the list
        summed_df = dataframes[0].copy()
        # Iterate through the list of dataframes, starting from the second dataframe
        for df in dataframes[1:]:
            for col in column_names:
                # Sum the specified columns
                summed_df[col] += df[col]
        return summed_df
    elif len(dataframes) == 1:
        return dataframes[0]
    


def main():
    token = check_credential()
    properties = locations(token)
    properties_with_sensors = get_properties_with_sensors(properties, token)
    df_locations = pd.DataFrame.from_dict(properties_with_sensors)
    return df_locations



"""
To do list:
1. Create a function that will update the list of sensors
2. Create a dataframe that has a row each for every location ID and a then a column for a list of sensors
3. Create function to query for the average volume by date
"""
