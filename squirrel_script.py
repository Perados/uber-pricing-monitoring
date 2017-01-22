#!/usr/bin/env python

import csv
import datetime
import os

from geopy.geocoders import GoogleV3
from uber_rides.session import Session, OAuth2Credential
from uber_rides.client import UberRidesClient

# fill the following global variables with your values
ACCESS_TOKEN = 'your_access_token'
CLIENT_ID = 'your_client_id'
CLIENT_SECRET = 'your_client_secret'
PRODUCT_NAME = 'uberX'  # change this according to your city

# define your addresses and give them a short name
START_PLACE = ('short_name_1', 'start_address')
END_PLACE = ('short_name_2', 'end_address')

GEOLOCATOR = GoogleV3(timeout=5)  # we will use Google maps API

# use the addresses to get the gps coordinates
START_GEOCODE = GEOLOCATOR.geocode(START_PLACE[1])
END_GEOCODE = GEOLOCATOR.geocode(END_PLACE[1])

# define the ouput file and its headers
OUTPUT_FILE_PATH = 'squirrel_monitoring.csv'
CSV_HEADERS = [
    'date',
    'start_place',
    'start_latitude',
    'end_longitude',
    'end_place',
    'end_latitude',
    'end_longitude',
    'distance_estimation',
    'duration_estimation',
    'price',
]


def authenticate():
    credentials = {
        'access_token': ACCESS_TOKEN,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'expires_in_seconds': 9999999999,
        'grant_type': 'authorization_code',
        'scopes': None
    }
    oauth2_credential = OAuth2Credential(**credentials)
    session = Session(oauth2credential=oauth2_credential)
    client = UberRidesClient(session)
    return client


def get_product_id(client, product_name):
    response = client.get_products(
        START_GEOCODE.latitude,
        START_GEOCODE.longitude,
    )
    products = response.json.get('products')

    for product in products:
        if product['display_name'] == product_name:
            product_id = product['product_id']
            return product_id


def write_to_csv(client, product_id):
    file_exists = os.path.isfile(OUTPUT_FILE_PATH)

    with open(OUTPUT_FILE_PATH, 'a') as f:
        writer = csv.writer(f)

        if not file_exists:  # this allows you to write the headers only once
            writer.writerow(CSV_HEADERS)

        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        # extract
        estimated_ride = client.estimate_ride(
            product_id=product_id,
            start_latitude=START_GEOCODE.latitude,
            start_longitude=START_GEOCODE.longitude,
            end_latitude=END_GEOCODE.latitude,
            end_longitude=END_GEOCODE.longitude,
        ).json

        # transform
        row = [
            now,
            START_PLACE[0],
            START_GEOCODE.latitude,
            START_GEOCODE.longitude,
            END_PLACE[0],
            END_GEOCODE.latitude,
            END_GEOCODE.longitude,
            estimated_ride['trip']['distance_estimate'],
            estimated_ride['trip']['duration_estimate'],
            estimated_ride['fare']['value'],
        ]

        # load
        writer.writerow(row)


def main():
    print('Starting script...')
    client = authenticate()
    product_id = get_product_id(client, PRODUCT_NAME)
    write_to_csv(client, product_id)
    print('Successfully wrote line into csv file...')


if __name__ == '__main__':
    main()
