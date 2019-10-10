import json
import time
import datetime as dt
from pprint import pprint
from typing import List

import googlemaps
import pandas as pd

from local import api_key


HOME = ''
WORK = ''

TRAFFIC_MODELS = ['optimistic', 'best_guess', 'pessimistic']
TEST = True

'''
TODO:
    - might be a way to reduce api calls?
'''


def get_single_data_point(
    gmaps: googlemaps.Client,
    start: str,
    end: str,
    departure_time: dt.datetime,
    traffic_model: str,
) -> int:
    '''
    params:
        gmaps: google maps client object
        start, end: addresses for home and work (strings)
        departure_time: datetime object
        traffic_model: one of 'optimistic', 'best_guess', 'pessimistic'
    return 
        duration_in_traffic (int) in seconds
    Note: will be called ~1000 times; Google maps API daily free request limit is 2500
    '''
    result =  gmaps.distance_matrix(start, end, 
        mode='driving', departure_time=departure_time, traffic_model=traffic_model)
    # return preditced travel time in seconds
    try:
        return result['rows'][0]['elements'][0]['duration_in_traffic']['value']
    except:
        return -1


def generate_datetimes(direction: str) -> dt.datetime:
    '''
    params: 
        direction: either 'going' or 'returning'
    returns:
        List of datetime objects: 6 hour range for every weekday starting at either 6am (direction='going')
        or 2pm (direction='returning'), every 10 minutes
    '''
    if direction == 'going':
        start_hour = 6
    elif direction == 'returning':
        start_hour = 14

    today = dt.datetime.now().replace(hour=start_hour, minute=0, second=0, microsecond=0)
    tomorrow = today + dt.timedelta(1)

    if TEST:
        # smaller time range for testing, only 6 hours over one day
        return [
            tomorrow + dt.timedelta(seconds=hour * 60 * 60)
            for hour in range(0, 6)
        ]
    else:
        return [
            tomorrow + dt.timedelta(day=day, hour=hour, minute=minute)
            for day in range(0, 5)
            for hour in range(0, 6)
            for minute in range(0, 60, 10)
        ]
        # return [datetime(2017, 10, 2 + day, start_hour + hour, 0 + minute, 0, 0) 
        #                 for day in range(0, 5)
        #                 for hour in range(0, 6)
        #                 for minute in range(0, 60, 10)]


def generate_df(gmaps: googlemaps.Client, start: str, end: str, datetimes: List[dt.datetime]):
    '''
    params:
        gmaps: google maps client object
        start, end: addresses for home and work (strings)
        datetimes: list of datetime objects
    returns:
        DataFrame with traffic models for columns, datetimes for rows, and travel times for values
    '''
    optimistic = [get_single_data_point(gmaps, start, end, time, 'optimistic') 
                    for time in datetimes]
    best_guess = [get_single_data_point(gmaps, start, end, time, 'best_guess') 
                    for time in datetimes]
    pessimistic = [get_single_data_point(gmaps, start, end, time, 'pessimistic') 
                    for time in datetimes]

    return pd.DataFrame(data={'optimistic': optimistic, 
                                'best_guess': best_guess,
                                'pessimistic': pessimistic},
                        index=datetimes,
                        columns=TRAFFIC_MODELS)


def get_morning_data(gmaps):
    '''
    Queries google maps api for morning commute, creates DataFrame and saves as pickle file

    params:
        gmaps: google maps client object
    '''
    start, end = HOME, WORK
    datetimes = generate_datetimes('going')
    going_df = generate_df(gmaps, start, end, datetimes)
    going_df.to_pickle('./data/going_df.p')


def get_afternoon_data(gmaps):
    '''
    Queries google maps api for afternoon commute, creates DataFrame and saves as pickle file

    params:
        gmaps: google maps client object
    '''
    start, end = WORK, HOME
    datetimes = generate_datetimes('returning')
    returning_df = generate_df(gmaps, start, end, datetimes)
    returning_df.to_pickle('./data/returning_df.p')


if __name__ == '__main__':
    gmaps = googlemaps.Client(key=api_key)
    get_morning_data(gmaps)
    get_afternoon_data(gmaps)
