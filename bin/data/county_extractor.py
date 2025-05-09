
from util.logger import error, warning
import values as v

import json
import logging
from time import sleep

from urllib.parse import quote
import requests

jRes = 'result' # fields in json from census api
jAddr = 'addressMatches'
jGeo = 'geographies'
jCounty = 'Counties'
jName = 'NAME'

def get_county(street, city, state, zip):
    addr = '&street=' + quote(street)
    ct = '&city=' + quote(city)
    st = '&state=' + quote(state)
    zp = '&zip=' + quote(zip)

    target = v.census_link + addr + ct + st + zp
    logging.info('')
    logging.info('Requesting census information from:')
    logging.info(target)

    with requests.Session() as s:
        for i in range(0, v.max_retries):
            response = s.get(target)
            if response.status_code == 200:
                json_geo = json.loads(response.content)
                break
            error('NON-200 RESPONSE RECEIVED FROM CENSUS API!!!')
            error(response.text)
            logging.error(response) # no idea what this'll look like
            sleep(1)
    if json_geo is None:
        error('EMPTY JSON RESPONSE FROM CENSUS API!!! TRIES: ' + i)
        return None

    logging.info('Successfully retrieved census API data.')

    matched_addrs = json_geo[jRes][jAddr]
    num_addrs = len(matched_addrs)
    if num_addrs > 1:
        for addr in matched_addrs:
            prev = addr
            if addr == prev: continue
            warning('More than one corresponding address found! Manual intervention required!')
            return None

    try: # try to match address to census info
        counties = matched_addrs[0][jGeo][jCounty]
        num_counties = len(counties)
        if num_counties > 1: # should theoretically never have more than one county
            for county in counties:
                prev = county
                if county.lower() == prev.lower(): continue
                warning('More than one corresponding county found! Manual intervention required!')
                return None
    except IndexError:
        warning('No counties found for this address! Manual intervention required!',
              'Address: ' + street + ', ' + city + ', ' + state + ' ' + zip,
              'Census link: ' + target)
        return None

    # if the address is matched, there should be at least one county, but we handle
    # exceptions anyways. like professionals.
    try:
        county = counties[0][jName]
        # HACK this is kinda cursed but we're doing it
        if 'county' in county.lower(): county_actual = county[:len(county) - len(' county')] # :D
        else: county_actual = county
        if county_actual is None:
            warning('County format for ' + county + ' is non-standard.')
            return county
    except IndexError:
        # based on census response, we should never, ever end up here
        error('NO COUNTIES FOUND FOR THIS ADDRESS!!! MANUAL INTERVENTION REQUIRED!!! WEIRD!!!')
        return None

    return county_actual
