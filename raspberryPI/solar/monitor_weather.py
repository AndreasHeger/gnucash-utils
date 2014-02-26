#!/usr/bin/env python
'''Monitor temperature.
'''

import os
import time
import logging
import rrdtool
import urllib
import re

# third party libs
from daemon import runner

##########################################################################
##########################################################################
##########################################################################
##########################################################################
URL = "http://www.wunderground.com/cgi-bin/findweather/getForecast?query=51.746%2C-1.296&sp=IOXFORDS54"

LAST_COLLECTION = 0

# collect new data every 2 minutes
TIME_DIFFERENCE = 120

DATABASE = {'wind_direction': (-360, 360),
            'wind_speed': (0, 100),
            'temperature': (-50, 100)}

CACHE = {'wind_direction': 0,
         'wind_speed': 0,
         'temperature': 0,
         'sunrise': 0,
         'sunset': 0}

rx_temp = re.compile('tempActual.*pwsid="([^"]+)".*value="([^"]+)"')
rx_winddirection = re.compile('windCompass.*pwsid="([^"]+)".*value="([^"]+)"')
rx_windspeed = re.compile(
    'windCompassSpeed.*pwsid="([^"]+)".*>([0-9.]+)</span>')
rx_sunrise = re.compile('"sRise".*>([0-9.:]+)</span> AM</div>')
rx_sunset = re.compile('"sSet".*>([0-9.:]+)</span> PM</div>')


def time2float(timeval):
    '''converts a x:xx value to hrs.'''
    hours, minutes = timeval.split(":")
    return float(hours) + float(minutes) / 60.0

MIN_TEMPERATURE = -50
MAX_TEMPERATURE = 100

# 2 mins
HEART_BEAT = 120

# aggregates
SHORT_TERM_DAYS = 7
MEDIUM_TERM_DAYS = 30
LONG_TERM_DAYS = 90

# number of readings and periods in days for profiles
# 1 mins
SHORT_TERM_VALUES_PER_AGGREGATE = 1
SHORT_TERM_NUM_VALUES = SHORT_TERM_DAYS * \
    24 * 60 // SHORT_TERM_VALUES_PER_AGGREGATE
# 6 mins
MEDIUM_TERM_VALUES_PER_AGGREGATE = 3
MEDIUM_TERM_NUM_VALUES = MEDIUM_TERM_DAYS * \
    24 * 60 // MEDIUM_TERM_VALUES_PER_AGGREGATE
# 10 mins
LONG_TERM_VALUES_PER_AGGREGATE = 5
LONG_TERM_NUM_VALUES = LONG_TERM_DAYS * \
    24 * 60 // LONG_TERM_VALUES_PER_AGGREGATE


##########################################################################
##########################################################################
##########################################################################
# Daemon part
##########################################################################
class App():

    def __init__(self):
        self.stdin_path = '/dev/null'
        # tty not available for a spice
        self.stdout_path = '/dev/null'
        self.stderr_path = '/dev/null'
        self.pidfile_path = '/mnt/ramdisk/weather_daemon.pid'
        self.pidfile_timeout = 5

        # open tcp connection
        self.connection = None

        # rrd database names to store data into
        self.rrd_directory = "/mnt/ramdisk"
        self.rrd_database = os.path.join(self.rrd_directory, 'weather.rrd')

        self.sensor_group = 1

    def run(self):
        '''main loop.
        '''

        self.createDatabase()

        while True:

            logger.debug('starting iteration')
            try:
                values = {}

                logger.debug('open URL')
                infile = urllib.urlopen(URL)
                logger.debug('opened URL')
                station, temperature = None, None
                wind_direction, wind_speed = None, None

                for line in infile:

                    x = rx_temp.search(line)
                    if x:
                        station, temperature = x.groups()
                        temperature = (float(temperature) - 32) * 5.0 / 9.0
                        continue

                    x = rx_winddirection.search(line)
                    if x:
                        station, wind_direction = x.groups()
                        wind_direction = float(wind_direction)
                        continue

                    x = rx_windspeed.search(line)
                    if x:
                        station, wind_speed = x.groups()
                        wind_speed = float(wind_speed)
                        continue

                    x = rx_sunrise.search(line)
                    if x:
                        sunrise = time2float(x.groups()[0])
                        continue

                    x = rx_sunset.search(line)
                    if x:
                        sunset = time2float(x.groups()[0]) + 12.0
                        continue

                logger.debug('parsed data')

                values['temperature'] = temperature
                values['wind_direction'] = wind_direction
                values['wind_speed'] = wind_speed
                values['sunrise'] = sunrise
                values['sunset'] = sunset

                logger.debug("values collected: %s" % str(values))

                self.updateDatabase(values)
                logger.info("status: weather=ok")
                logger.debug("database updated")

            except Exception, msg:
                logger.warn("error ignored: msg=%s" % str(msg))
                logger.info("status: weather=fail")

            time.sleep(HEART_BEAT)

    def updateDatabase(self, values):
        '''update rrd database with values'''
        s = "N:" + \
            ":".join(map(str, ([values[x] for x in sorted(DATABASE.keys())])))
        logger.debug(s)

        rrdtool.update(self.rrd_database, s)

        logger.debug('database updated')

    def createDatabase(self):
        '''create rrd databases. Existing databases will not be overwritten'''

        params = globals()
        params.update(locals())

        if not os.path.exists(self.rrd_database):
            logger.info("creating new rrd database %s" % self.rrd_database)
            data_sources = []
            for key, ranges in sorted(DATABASE.items()):
                mi, ma = ranges
                data_sources.append('DS:%s:GAUGE:%i:%i:%i' %
                                    (key, 2 * HEART_BEAT, mi, ma))

            rra = [
                # short-term
                'RRA:AVERAGE:0.5:%(SHORT_TERM_VALUES_PER_AGGREGATE)i:%(SHORT_TERM_NUM_VALUES)i',
                # medium term
                'RRA:AVERAGE:0.5:%(MEDIUM_TERM_VALUES_PER_AGGREGATE)i:%(MEDIUM_TERM_NUM_VALUES)i',
                'RRA:MIN:0.5:%(MEDIUM_TERM_VALUES_PER_AGGREGATE)i:%(MEDIUM_TERM_NUM_VALUES)i',
                'RRA:MAX:0.5:%(MEDIUM_TERM_VALUES_PER_AGGREGATE)i:%(MEDIUM_TERM_NUM_VALUES)i',
                # longterm profile
                'RRA:AVERAGE:0.5:%(LONG_TERM_VALUES_PER_AGGREGATE)i:%(LONG_TERM_NUM_VALUES)i',
                'RRA:MIN:0.5:%(LONG_TERM_VALUES_PER_AGGREGATE)i:%(LONG_TERM_NUM_VALUES)i',
                'RRA:MAX:0.5:%(LONG_TERM_VALUES_PER_AGGREGATE)i:%(LONG_TERM_NUM_VALUES)i',
            ]

            rra = [x % params for x in rra]

            rrdtool.create(self.rrd_database,
                           '--step', str(HEART_BEAT),
                           *data_sources + rra)


app = App()
logger = logging.getLogger("DaemonLog")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler("/mnt/ramdisk/weather.log")
handler.setFormatter(formatter)
logger.addHandler(handler)

daemon_runner = runner.DaemonRunner(app)
# This ensures that the logger file handle does not get closed during
# daemonization
daemon_runner.daemon_context.files_preserve = [handler.stream]
daemon_runner.do_action()
