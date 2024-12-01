import requests
import json
import time
import pandas as pd
import alertlabAPI as al
import urllib.parse as urlparse

LOGIN_API = 'https://www.alertlabsdashboard.com/oauth/login?client_id=AlertLabsLogin&state=login&redirect_uri=https://www.alertlabsdashboard.com&response_type=code'
TOKEN_API = 'https://www.alertlabsdashboard.com/oauth/AlertLabsLogin/tokenExchange'



'''
Inputs: None
Outputs: String
Description: Uses alertlabs login details to return an authorization header for their non-public API
'''
# Handle token exchange token to get new access token
def generate_new_authorization_header():
    response = requests.post(LOGIN_API, json={
        "user": "ethan.kim@water-controls.com",
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



'''
Inputs: String, String, String
Outputs: Dictionary
Description:
'''
def get_details(location_id, authorization_header, query):
    location_ids_json = json.dumps(location_id)
    if query == "property_details":
        url = f"https://www.alertlabsdashboard.com/api/v2/locations/{location_id}/details"
        data_key = 'location'
    elif query == "water_rates":
        url = f"https://www.alertlabsdashboard.com/api/v3/locations/{location_id}/waterRates"
        data_key = "rates"
    elif query == "parent_name":
        url = f"https://www.alertlabsdashboard.com/api/v2/locations/{location_id}"
        data_key = "friendly name"
    headers = {
        "authorization": authorization_header,
    }
    params = {
        "locationIDs": location_ids_json,
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()


'''
Inputs: String, String, 
Outputs: Dictionary
Description:
'''
def get_property_details(location_id, authorization_header):
    location_ids_json = json.dumps(location_id)
    property_details_url = f"https://www.alertlabsdashboard.com/api/v2/locations/{location_id}/details"
    headers = {
        "authorization": authorization_header,
    }
    # Pass the locationIDs as a JSON string in the params
    params = {
        "locationIDs": location_ids_json,
    }
    response = requests.get(property_details_url, headers=headers, params=params)
    return response.json()


'''
Inputs: String, String
Outputs: Dictionary
Description: Returns a dictionary about watercosts
'''
def get_water_costs(location_id, authorization_header):
    location_ids_json = json.dumps(location_id)
    property_details_url = f"https://www.alertlabsdashboard.com/api/v3/locations/{location_id}/waterRates"
    headers = {
        "authorization": authorization_header,
    }
    # Pass the locationIDs as a JSON string in the params
    params = {
        "locationIDs": location_ids_json,
    }
    response = requests.get(property_details_url, headers=headers, params=params)
    return response.json()


'''
Inputs: None
Outputs: Dataframe
Description: Using the non-public API this fucntion will use the dataframe from the alertlabs-api.py main() function to lookup up all non-public info based on location ID 
'''
def get_tombstone_data(df, authorization_header):
    #start = time.time()
    column_ids = ['_id', 'postalCode', 'commercialPropertyType', 'numberSuites', 
              'unoccupiedSuites', 'smartMeter', 'numOccupants', 'age', 'size', 'numberFloors']
    tombstone_list = []
    location_list = df["_id"]
    for location in location_list:
        details = get_property_details(location, authorization_header)
        tombstone_list.append(details['location'])
    cleaned_data = [
        {k: (v if v is not None else '') for k, v in d.items()}
        for d in tombstone_list if isinstance(d, dict)
    ]
    df = pd.DataFrame(cleaned_data)
    df_reduced = df[column_ids]
    return df_reduced



def get_parents_ids(df, authorization_header):
    parent_names = []
    parent_id_df = df[["_id", "parentIDs"]].copy()
    for parent_id_list in parent_id_df["parentIDs"]:
        if len(parent_id_list) == 0:
            parent_names.append("Other")
        elif len(parent_id_list) == 1:
            response = get_only_parent_id(parent_id_list[0], authorization_header)
            if response != "Error":
                parent_names.append(response)
            elif response == "Error":
                parent_names.append("Other")
        elif len(parent_id_list) > 1:
            flag = False
            for parent_id in parent_id_list:
                response = get_only_parent_id(parent_id, authorization_header)
                if response != "Error":
                    parent_names.append(response)
                    flag = True
                    break
            if flag == False:
                parent_names.append("Other")
        
    parent_id_df.loc[:, "parentNames"] = parent_names
    return parent_id_df



def main():
    # Only for testing 
    start = time.time()
    # This should be replace but for now it will substitute the initial API call used to get location data
    df = al.main()
    # Create a new dataframe and initialize the column with the same id values as the original
    parent_id_dataframe = pd.DataFrame(df["_id"], columns=["_id"])
    # Authorization header should be replaced with actual fucntion
    authorization_header = generate_new_authorization_header()
    # Create list of parent ID names
    parent_id_dataframe["parentID"] = df["_id"].apply(lambda location_id: get_only_parent_id(location_id, authorization_header))
    # Stop timer
    stop = time.time()
    # Get elapsed time
    time_elapsed = stop - start
    # print 
    print(f"Time elapsed: {time_elapsed}")
    # Return the pandas dataframe
    return parent_id_dataframe



def get_only_parent_id(parent_id, authorization_header):
    location_ids_json = json.dumps(parent_id)
    url = f"https://www.alertlabsdashboard.com/api/v2/locations/{parent_id}"
    headers = {
        "authorization": authorization_header,
    }
    params = {
        "locationIDs": location_ids_json,
    }
    response = requests.get(url, headers=headers, params=params)
    if "friendlyName" in response.json().keys():
        return response.json()["friendlyName"]
    else:
        return "Error"
