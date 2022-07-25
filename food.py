import requests
import json
import os
import pandas as pd
import sqlalchemy as db


API_KEY = os.environ.get('YELP_API_KEY')
BASE_URL = 'https://api.yelp.com/v3'
HEADER = {'Authorization': f"Bearer {API_KEY}"}
database_name = 'yelp_info'
engine = db.create_engine('mysql://root:codio@localhost/'+database_name+'?char\
    set=utf8', encoding='utf-8')
business_search_endpoint = "/businesses/search"
prefs_dict = {}
biz_categories = []


def get_response(endpoint, search_keys=""):
    """Performs a GET request to API and returns JSON response.
    
    Keyword arguments:
    endpoint -- the API's endpoint as a string, e.g. "/businesses/search"
    search_keys -- a dictionary of the different request parameters, default is with no parameters

    returns the JSON response for the given endpoint and parameters
    """
    request = requests.get(f'{BASE_URL}{endpoint}', params=search_keys, headers=HEADER)
    response = request.json()
    return response


def json_to_df(json_response):
    """Converts the API's JSON response to a Pandas dataframe.
    
    Keyword arguments:
    json_response -- the JSON response returned by the API request

    returns a normalized Pandas dataframe, removing any unsupported types like lists or dictionaries 
    """
    for key, value in list(json_response.items()):
        if isinstance(value, list) or isinstance(value, dict):
            del json_response[key]
    normalized_frame = pd.json_normalize(json_response)
    return normalized_frame


def df_to_sql(dataframe, title):
    """Converts Pandas dataframe into a MySQL database table

    Keyword arguments:
    dataframe -- the Pandas dataframe gotten from the json_to_df function
    title -- the name of the database table

    returns the num of rows in the table affected by the .to_sql() method
    """
    database = dataframe.to_sql(title, con=engine, if_exists='replace', index=False)
    return database


# Receives a list as a param
def validate_prefs(pref_type, prefs):
    # check prefs against yelp search
    # not valid if no results
    valid_flag = False
    for i, pref in enumerate(prefs):
        data = {pref_type: pref, "limit": 2}
        if "location" in prefs_dict:
            data["location"] = prefs_dict["location"][i]
        else:
            data["location"] = pref

        try:
            pref_response = get_response(business_search_endpoint, data)

            business_df = json_to_df(pref_response)
            business_df.to_html('business.html')

            df_to_sql(business_df, "business")
            query_result = engine.execute("select * from business;").fetchall()

            print(json.dumps(pref_response, indent=2))
            if pref_response['businesses'] and pref_response['total'] > 0:
                if pref_type == "term":
                    global biz_categories
                    biz_categories += get_biz_categories(
                        pref_response['businesses'][0]['categories']
                    )
                valid_flag = True
        except KeyError:
            continue

    return valid_flag


# Takes a string param pref_type that tells the function what kind of
# preference it is, i.e. for businesses or locations etc. Prompt is a string
# that will passed to the user to ask them for their preferences
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


# TODO: implement a helper method to go thru the businesses in prefs_dict and
# collect all their categories.
# TODO: Use this category list and pass to the request with each location
def get_biz_categories(raw_categories):
    categories = []
    for category_obj in raw_categories:
        category = category_obj['alias']
        if category not in biz_categories and category not in categories:
            categories.append(category)

    return categories


# Returns an array of the names of the recommended places
# Based on the preferences passed, now in prefs_dict.
def get_recs():
    recs = []
    # match recs to prefs based on categories
    # get a set of the unique categories of the given businesses
    # pass all the categories and get recs for each location
    for loc in prefs_dict["location"]:
        params = {
            "categories": biz_categories,
            "location": loc,
            "sort_by": "rating",
            "limit": 1
        }
        response = get_response(business_search_endpoint, params)
        recs.append(response["businesses"][0])

    return recs


def print_info(biz):
    print(biz['name'], end=", ")
    print(str(biz['rating']) + " stars")
    print(biz['display_phone'])
    address_arr = biz['location']['display_address']
    print(*address_arr, sep=", ")
    categories = []
    for category_obj in biz['categories']:
        categories.append(category_obj['title'])

    print(*categories, sep=", ")
    print()


def main():
    get_prefs("location", "Where would you like to receive recommendations?")
    get_prefs("term", "What are some businesses you like?")
    print("Here are some recommendations based on what you've put in:")
    for rec_obj in get_recs():
        print_info(rec_obj)


if __name__ == '__main__':
    main()
