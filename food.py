import requests
import json
import os
import pandas as pd
# import sqlalchemy as db


API_KEY = os.environ.get('YELP_API_KEY')
BASE_URL = 'https://api.yelp.com/v3'
HEADER = {'Authorization': f"Bearer {API_KEY}"}
# engine = db.create_engine('sqlite:///yelp_info.db')
database_name = 'yelp_info'
# engine = db.create_engine('mysql://root:codio@localhost/'+database_name+'?charset=utf8', encoding='utf-8')
business_search_endpoint = "/businesses/search"
prefs_dict = {}


def get_response(endpoint, search_keys=""):
    request = requests.get(f'{BASE_URL}{endpoint}', params=search_keys, headers=HEADER)
    response = request.json()
    return response


def json_to_df(json_response):
    for key, value in list(json_response.items()):
        if isinstance(value, list) or isinstance(value, dict):
            del json_response[key]
    normalized_frame = pd.json_normalize(json_response)
    return normalized_frame


def df_to_sql(dataframe, title):
    database = dataframe.to_sql(title, con=engine, if_exists='replace', index=False)
    return database


def print_info(places):
    for i in range(len(places)):
        print(places[i]['name'], end=", ")
        print(str(places[i]['rating']) + " stars")
        print(places[i]['display_phone'])
        address_arr = places[i]['location']['display_address']
        print(address_arr[0] + ", " + address_arr[1])
        print(places[i]['categories'][0]['title'])
        print()


# Receives a list as a param
def validate_prefs(pref_type, prefs):
    # check prefs against yelp search
    # not valid if no results
    for pref in prefs:
        data = {pref_type: pref, "limit": 2}
        if "location" in prefs_dict:
            data["location"] = prefs_dict["location"][0]
        pref_response = get_response(business_search_endpoint, data)
        try:
            print(json.dumps(pref_response, indent=2))
            if pref_response['businesses']:
                return True
        except:
            continue

    return False
        

# Takes a string param pref_type that tells the function what kind of preference it is, i.e. for businesses or locations etc. Prompt is a string that will passed to the user to ask them for their preferences
def get_prefs(pref_type, prompt):
    pref_list = []
    valid_prefs = False
    while not valid_prefs:
        prefs = input(prompt + "\n").strip()
        pref_list = prefs.split("; ")
        valid_prefs = validate_prefs(pref_type, pref_list)

    if pref_type not in prefs_dict:
        prefs_dict[pref_type] = pref_list

    return pref_list

# TODO: implement a helper method to go thru the businesses in prefs_dict and collect all their categories.
# TODO: Use this category list and pass to the request with each location
# Returns an array of the names of the recommended places
# Based on the preferences passed, now in prefs_dict. 
def get_recs():
    recs = []
    # match recs to prefs based on categories
    # get a set of the unique categories of the given businesses
    # pass all the categories and get recs for each location
    for loc in prefs_dict["location"]:
        params = {
            "categories": category_list, 
            "location": loc, 
            "sort_by": "rating",
            "limit": 1
        }
        response = get_response(business_search_endpoint, params)
        recs.append(response["businesses"][0]["name"])

    return recs


def main():
    get_prefs("location", "Where would you like to receive recommendations?")
    get_prefs("term", "What are some businesses you like?")
    print("Here are some recommendations based on what you've put in:")
    for rec in get_recs():
        print(rec)


if __name__ == '__main__':
    main()


'''
search_keys = {'term': 'vegan', 'location': 'emory', 'limit': '3'}
search_response = get_response(business_search_endpoint, search_keys)

business_id_endpoint = "/businesses/"
business_id = search_response['businesses'][0]['id']
business_id_response = get_response(f'{business_id_endpoint}{business_id}')

reviews_endpoint = f"/businesses/{business_id}/reviews"
reviews_response = get_response(reviews_endpoint)

business_df = json_to_df(business_id_response)
business_df.to_html('no-category.html')

df_to_sql(business_df, "business")
query_result = engine.execute("select * from business;").fetchall()
'''

