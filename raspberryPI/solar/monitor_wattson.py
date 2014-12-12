#!/usr/bin/env python

# http://www.gavinj.net/2012/06/building-python-daemon-process.html

import os
import time
import sys
import logging
import subprocess
import rrdtool
import serial
import io
import termios

# third party libs
from daemon import runner

# for solar monitoring
import re

RANGES = {'grid_power': (0, 10000),
          'solar_power': (0, 4000)}

DAILY_PROFILES = ('grid_power',
                  'solar_power')

# aggregates
SHORT_TERM_DAYS = 7
MEDIUM_TERM_DAYS = 30
LONG_TERM_DAYS = 90

# number of readings and periods in days for profiles
SHORT_TERM_VALUES_PER_AGGREGATE = 1
SHORT_TERM_NUM_VALUES = SHORT_TERM_DAYS * \
    24 * 60 // SHORT_TERM_VALUES_PER_AGGREGATE
MEDIUM_TERM_VALUES_PER_AGGREGATE = 5
MEDIUM_TERM_NUM_VALUES = MEDIUM_TERM_DAYS * \
    24 * 60 // MEDIUM_TERM_VALUES_PER_AGGREGATE
LONG_TERM_VALUES_PER_AGGREGATE = 10
LONG_TERM_NUM_VALUES = LONG_TERM_DAYS * \
    24 * 60 // LONG_TERM_VALUES_PER_AGGREGATE

# Gather every 10 seconds
HEART_BEAT = 10


class App():

    def __init__(self):
        self.stdin_path = '/dev/null'
        # tty not available as init script
        self.stdout_path = '/dev/null'
        self.stderr_path = '/dev/null'
        self.pidfile_path = '/mnt/ramdisk/solardaemon.pid'
        self.pidfile_timeout = 5

        # open tcp connection
        self.connection = None

        # rrd database names to store data into
        self.rrd_directory = "/mnt/ramdisk"
        self.rrd_power = os.path.join(
            self.rrd_directory, 'wattson.rrd')

        self.port = '/dev/ttyUSB0'
        # stty settings
        self.stty = "5:0:8be:0:0:0:0:0:0:a" + ":0" * 26

    def communicate(self, command):
        '''communicate with wattson energy monitor'''

        logger.debug('sending commands %s' % command)
        ser = self.connection
        ser.flush()
        ser.flushInput()
        ser.flushOutput()
        ser.write(command + "\r")

        time.sleep(1)
        
        logger.debug("waiting for return data")

        for i in range(5):
            r = []
            while ser.inWaiting() > 0:
                r.append(ser.read(1))
            if len(r) > 0:
                break
            time.sleep(0.1)

        logger.debug("received %i bytes after %i tries" %
                     (len(r), i))

        if len(r) == 0:
            return None

        # skip first character
        r = ''.join(r[1:])
        # remove everything after line break
        r = re.sub("\r(.*|$)", "", r)
        # remove new-line
        r = r.rstrip()
        if len(r) == 0:
            return None
        return r

        
    def setup_connection(self):

        logger.debug("wattson: port=%s" % self.port)
        
        # 19200, 8N1
        # 8 data bits, no parity bit, 1 stop bit
        self.connection = serial.Serial(
            port=self.port,
            baudrate=19200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS)

        self.connection.open()
        assert self.connection.isOpen()

        data = self.communicate("nows")

        logger.info("connected to wattson device %s" % data)

    def run(self):
        '''main loop.
        '''

        self.createDatabase()

        while True:

            logger.info("connecting to wattson")
            self.setup_connection()

            while True:
                
                grid_status, solar_status = "ok", "ok"
                    
                # first command always fails
                solar_power = self.communicate("noww")
                solar_power = self.communicate("noww")
                if solar_power is None:
                    solar_status = "fail"
                    solar_power = 0
                else:
                    assert len(solar_power) == 4
                    solar_power = int(solar_power, 16)

                # get current energy usage in watts
                grid_power = self.communicate("nowp")
                if grid_power is None:
                    grid_status = "fail"
                    grid_power = 0
                else:
                    assert len(grid_power) == 4, \
                        "malformed grid power: %s" % list(grid_power)
                    grid_power = int(grid_power, 16)

                logger.debug(
                    "acquired values: grid=%s, solar=%s" %
                    (grid_power, solar_power))

                logger.info(
                    "status: grid=%s, solar=%s" %
                    (grid_status, solar_status))

                self.updateDatabase(grid_power,
                                    solar_power)

                time.sleep(HEART_BEAT)
                
            logger.warn("lost connection - will retry")

    def updateDatabase(self, grid_power, solar_power):
        '''update rrd database with values'''
        
        rrdtool.update(
            self.rrd_power,
            "N:" + ":".join(map(str, (grid_power,
                                      solar_power))))

    def createDatabase(self):
        '''create rrd databases. Existing databases will
        not be overwritten'''

        params = globals()
        params.update(locals())

        if not os.path.exists(self.rrd_power):
            logging.info(
                "creating new rrd database %s" % self.rrd_power)
            data_sources = []
            for profile in DAILY_PROFILES:
                mi, ma = RANGES[profile]
                data_sources.append(
                    'DS:%s:GAUGE:120:%i:%i' % (profile, mi, ma))

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

            rrdtool.create(self.rrd_power,
                           '--step', str(HEART_BEAT),
                           *data_sources + rra)

    def __del__(self):
        if self.connection:
            self.connection.close()

app = App()

logger = logging.getLogger("DaemonLog")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler("/mnt/ramdisk/wattson.log")
handler.setFormatter(formatter)
logger.addHandler(handler)
app.run()

daemon_runner = runner.DaemonRunner(app)
# This ensures that the logger file handle does not get closed during
# daemonization
daemon_runner.daemon_context.files_preserve = [handler.stream]
daemon_runner.do_action()
