import googlemaps
from datetime import datetime
from local import api_key
import json
import time
import pandas as pd
from pprint import pprint


HOME = '400 S Andresen Rd, Vancouver, WA 98661, USA'
WORK = '2505 SE 11th Ave, Portland, OR 97202, USA'
TRAFFIC_MODELS = ['optimistic', 'best_guess', 'pessimistic']


# params:
#   gmaps: google maps client object
#   start, end: addresses for home and work (strings)
#   departure_time: datetime object
#   traffic_model: one of 'optimistic', 'best_guess', 'pessimistic'
# return 
#   duration_in_traffic (int) in seconds
# Note: will be called ~1000 times; Google maps API daily free request limit is 2500
def get_single_data_point(gmaps, start, end, departure_time, traffic_model):
    result =  gmaps.distance_matrix(start, end, 
        mode='driving', departure_time=departure_time, traffic_model=traffic_model)
    # return preditced travel time in seconds
    try:
        return result['rows'][0]['elements'][0]['duration_in_traffic']['value']
    except:
        return -1


# params: 
#   direction: either 'going' or 'returning'
# returns:
#   List of datetime objects: 6 hour range for every weekday starting at either 6am (direction='going')
#   or 2pm (direction='returning'), every 10 minutes
def generate_datetimes(direction):
    if direction == 'going':
        start_hour = 6
    elif direction == 'returning':
        start_hour = 14

    return [datetime(2017, 10, 2 + day, start_hour + hour, 0 + minute, 0, 0) 
                    for day in range(0, 5)
                    for hour in range(0, 6)
                    for minute in range(0, 60, 10)]

    # smaller list for testing, only range of 6 hours during one day
    # return [datetime(2017, 10, 2, start_hour + hour, 0, 0, 0) 
    #             for hour in range(0, 6)]


# params:
#   gmaps: google maps client object
#   start, end: addresses for home and work (strings)
#   datetimes: list of datetime objects
# returns:
#   DataFrame with traffic models for columns, datetimes for rows, and travel times for values
def generate_df(gmaps, start, end, datetimes):
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


# params:
#   gmaps: google maps client object
# Queries google maps api for morning commute, creates DataFrame and saves as pickle file
def get_morning_data(gmaps):
    start, end = HOME, WORK
    datetimes = generate_datetimes('going')
    going_df = generate_df(gmaps, start, end, datetimes)
    going_df.to_pickle('going_df.p')


# params:
#   gmaps: google maps client object
# Queries google maps api for afternoon commute, creates DataFrame and saves as pickle file
def get_afternoon_data(gmaps):
    start, end = WORK, HOME
    datetimes = generate_datetimes('returning')
    returning_df = generate_df(gmaps, start, end, datetimes)
    returning_df.to_pickle('returning_df.p')


if __name__ == '__main__':
    gmaps = googlemaps.Client(key=api_key.KEY)
    get_morning_data(gmaps)
    get_afternoon_data(gmaps)