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
import subprocess

NAME_PREFIX = 'RT_'

PARAMS = {
    'SensorGroup' : 0,
}

CONFIG = {
    "KeevaRoomBack" : '10-0008029db5bc',
    "KeevaRoomTop"  : 'o28.3DA0D4040000',
    "KeevaCupBoard" : '10-0008029d938d',
    "AiringCabinet" : '10-0008029db6c3',
    "Attic"         : '10-0008029da542',
    "NiamhRoomBack" : "o28.6BFED3040000",
    "NiamhRoomTop"  : "o28.45C0D4040000",
    "LivingRoomWindow" : "28-000004d41fb1",
    "LivingRoomCupBoard": "28-000004d45cae",
    "LandingTop": "o10.ED859D020800",
    "LandingMiddle": "28-000004d3f73e",
    "LandingBottom": "10-0008029dc359",
}

SENSOR_GROUPS = [ (
        "KeevaRoomBack",
        "KeevaRoomTop",
        "KeevaCupBoard",
        "AiringCabinet",
        "Attic",
        "NiamhRoomBack",
        "NiamhRoomTop", 
        "LandingTop",
        ), 
                  (
        "LivingRoomWindow",
        "LivingRoomCupBoard",
        "LandingMiddle",
        "LandingBottom",
        ) ]


CACHE = {}

def get_value(name):
    """Return a value for the requested metric"""

    fn = CONFIG[name[len(NAME_PREFIX):]]
    if fn[0] == "o":
        try:
            temperature = subprocess.check_output(["owread", "/%s/temperature" % fn[1:]])
        except subprocess.CalledProcessError:
            return CACHE.get(name, 0)
        temperature = float(temperature)
    else:
        tfile = open("/sys/bus/w1/devices/w1_bus_master1/%s/w1_slave" % fn )
        text = tfile.readlines()
        tfile.close()
        status, temperature_data = text
        if not status.endswith("YES\n"):
            return CACHE.get(name, 0)
        else:
            temperature_data = temperature_data.split()[-1]
            temperature = float(temperature_data[2:])
            temperature = temperature / 1000
    CACHE[name] = temperature

    return temperature

def metric_init(lparams):
    """Initialize metric descriptors"""

    if "SensorGroup" not in lparams:
        raise ValueError("parameter 'SensorGroup' not found")

    descriptors = []

    sensor_group = int(lparams['SensorGroup'])

    # create descriptors
    for sensor_name in SENSOR_GROUPS[sensor_group]:
        descriptors.append({
                'name': '%s%s' % (NAME_PREFIX, sensor_name),
                'call_back': get_value,
                'time_max': 60,
                'value_type': 'float',
                'units': 'Celsius',
                'slope': 'both',
                'format': '%f',
                'description': "Room temperature (Celsius) at %s" % (sensor_name),
                'groups': 'temperature'
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

