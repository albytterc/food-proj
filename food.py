import requests
import json
import os

API_KEY = os.environ.get('YELP_API_KEY')

BASE_URL = 'https://api.yelp.com/v3'


HEADER = {'Authorization': f"Bearer {API_KEY}"}

endpoint = "/businesses/search"

search_keys = "term=vegan&location=emory&limit=3"

request = requests.get(f'{BASE_URL}{endpoint}?{search_keys}', headers=HEADER)
response = request.json()

places = response['businesses']

for i in range(len(places)):
    print(places[i]['name'], end=", ")
    print(str(places[i]['rating']) + " stars")
    print(places[i]['display_phone'])
    address_arr = places[i]['location']['display_address']
    print(address_arr[0] + ", " + address_arr[1])
    print(places[i]['categories'][0]['title'])
    print()

# print(json.dumps(request.json(), indent=2))
