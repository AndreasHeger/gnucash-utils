#!/usr/bin/env python
'''Test script for testing the parser
'''

import os
import time
import urllib
import Utils

URL = "http://www.wunderground.com/personal-weather-station/dashboard?ID=IOXFORDS46#"

infile = urllib.urlopen(URL)
outfile = open('weather.xml', 'w')
l = infile.readlines()
outfile.write("".join(l))
outfile.close()

values = Utils.parseWeather(l)

