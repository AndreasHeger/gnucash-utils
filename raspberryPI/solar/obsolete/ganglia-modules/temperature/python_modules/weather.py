#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Temperature sensing module for ganglia
#
# Copyright (C) 2011 by Michael T. Conigliaro <mike [at] conigliaro [dot] org>.
# All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import re
import os
import urllib
import time

NAME_PREFIX = 'WEATHER_'

PARAMS = {
}

URL = "http://www.wunderground.com/cgi-bin/findweather/getForecast?query=51.746%2C-1.296&sp=IOXFORDS54"

LAST_COLLECTION = 0

# collect new data every 2 minutes
TIME_DIFFERENCE = 120

CACHE = { 'wind_direction' : 0,
          'wind_speed' : 0,
          'temperature' : 0,
          'sunrise' : 0,
          'sunset' : 0 }

rx_temp = re.compile( 'tempActual.*pwsid="([^"]+)".*value="([^"]+)"' )
rx_winddirection = re.compile( 'windCompass.*pwsid="([^"]+)".*value="([^"]+)"' )
rx_windspeed = re.compile( 'windCompassSpeed.*pwsid="([^"]+)".*>([0-9.]+)</span>' )
rx_sunrise = re.compile( '"sRise".*>([0-9.:]+)</span> AM</div>' )
rx_sunset = re.compile( '"sSet".*>([0-9.:]+)</span> PM</div>' )

def time2float( timeval ):
    '''converts a x:xx value to hrs.'''
    hours, minutes = timeval.split(":")
    return float(hours) + float(minutes) / 60.0

def get_value(name):
    """Return a value for the requested metric"""

    now = time.time()
    global LAST_COLLECTION

    if now - LAST_COLLECTION > TIME_DIFFERENCE:
        infile = urllib.urlopen( URL )

        station, temperature = None, None
        wind_direction, wind_speed = None, None

        for line in infile:
            x = rx_temp.search( line )
            if x:
                station, temperature = x.groups()
                temperature = ( float(temperature) - 32) * 5.0 / 9.0
                continue
            x = rx_winddirection.search( line )
            if x:
                station, wind_direction = x.groups()
                wind_direction = float( wind_direction )
                continue
            x = rx_windspeed.search( line )
            if x:
                station, wind_speed = x.groups()
                wind_speed = float( wind_speed )
                continue
            x = rx_sunrise.search( line )
            if x:
                sunrise = time2float(x.groups()[0])

                continue
            x = rx_sunset.search( line )
            if x:
                sunset = time2float(x.groups()[0]) + 12.0
                continue
            
        CACHE['temperature'] = temperature
        CACHE['wind_direction'] = wind_direction
        CACHE['wind_speed' ] = wind_speed
        CACHE['sunrise' ] = sunrise
        CACHE['sunset' ] = sunset

        LAST_COLLECTION = now

    return CACHE[name[len(NAME_PREFIX):]]

def metric_init(lparams):
    """Initialize metric descriptors"""

    global PARAMS

    # set parameters
    for key in lparams:
        PARAMS[key] = lparams[key]

    descriptors = []

    # create descriptors
    descriptors.append({
            'name': '%s%s' % (NAME_PREFIX, 'temperature' ),
            'call_back': get_value,
            'time_max': 600,
            'value_type': 'float',
            'units': 'Celsius',
            'slope': 'both',
            'format': '%f',
            'description': "Temperature",
            'groups': 'weather'
            })

    descriptors.append({
            'name': '%s%s' % (NAME_PREFIX, 'wind_speed' ),
            'call_back': get_value,
            'time_max': 600,
            'value_type': 'float',
            'units': 'mph',
            'slope': 'both',
            'format': '%f',
            'description': "Wind speed",
            'groups': 'weather'
            })

    descriptors.append({
            'name': '%s%s' % (NAME_PREFIX, 'wind_direction' ),
            'call_back': get_value,
            'time_max': 600,
            'value_type': 'float',
            'units': 'degrees',
            'slope': 'both',
            'format': '%f',
            'description': "Wind direction",
            'groups': 'weather'
            })

    descriptors.append({
            'name': '%s%s' % (NAME_PREFIX, 'sunrise' ),
            'call_back': get_value,
            'time_max': 600,
            'value_type': 'float',
            'units': 'hours',
            'slope': 'both',
            'format': '%f',
            'description': "Sun rise",
            'groups': 'weather'
            })

    descriptors.append({
            'name': '%s%s' % (NAME_PREFIX, 'sunset' ),
            'call_back': get_value,
            'time_max': 600,
            'value_type': 'float',
            'units': 'hours',
            'slope': 'both',
            'format': '%f',
            'description': "Sun set",
            'groups': 'weather'
            })

    return descriptors

def metric_cleanup():
    """Cleanup"""
    pass


# the following code is for debugging and testing
if __name__ == '__main__':
    descriptors = metric_init(PARAMS)
    for d in descriptors:
        print (('%s = %s') % (d['name'], d['format'])) % (d['call_back'](d['name']))

