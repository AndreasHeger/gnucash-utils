#!/usr/bin/env python

# http://www.gavinj.net/2012/06/building-python-daemon-process.html

import sys
import os
import time
import lockfile
import signal
import logging
import rrdtool

# third party libs
from daemon import runner

# for solar monitoring
import socket
import re
import struct

##########################################################################
##########################################################################
##########################################################################
##########################################################################
RANGES = {'voltage': (0, 500),
          'current': (0, 100),
          'power': (0, 4000),
          'frequency': (0, 100),
          'temperature': (-50, 200),
          'energy': (0, 10000000)}

DAILY_PROFILES = ('voltage_1', 'voltage_2',
                  'current_1', 'current_2',
                  'power_1', 'power_2',
                  'power_total')

DAILY_ENERGY = ('energy_total', 'energy_daily')
DAILY_GRID = ('temperature_intern',
              'frequency_grid',
              'voltage_grid',
              'current_grid')

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

##########################################################################
##########################################################################
##########################################################################
##########################################################################
# Send UDP broadcast packets
##########################################################################
UDP_PORT = 1300
UDP_MESSAGE = "55 aa 00 40 02 00 0b 49 20 41 4d 20 53 45 52 56 45 52 04 3a"
UDP_REPEATS = 1

SOLAR_HOST = '192.168.0.45'    # The remote host

# TCP connection settings
TCP_HOST = ''                 # Symbolic name meaning the local host
TCP_PORT = 1200              # The same port as used by the server

TCP_MESSAGE_QUERY1 = "55 aa 01 03 02 00 00 01 05"
TCP_MESSAGE_QUERY2 = "55 aa 01 00 02 00 00 01 02"
TCP_MESSAGE_QUERY3 = "55 aa 04 00 02 00 00 01 05"
TCP_MESSAGE_QUERY_DATA = "55 aa 01 02 02 00 00 01 04"

# Gather every 60 seconds
HEART_BEAT = 10

##########################################################################


def toMsg(data):
    '''convert data to message.'''
    return re.sub(" ", "", data).decode('hex')


def fromMsg(data):
    '''decode message from SAMIL Inverter'''

    result = Result()
    result.fromData(data)

    return result


class Result:

    '''Container for SAMIL Inverter Status.'''

    def fromData(self, data):

        assert len(data) == 63
        fmt = "!7shhhhhhhhh20shhhhhhih"

        # A, B, C, D, E are unknown content
        # missing: operating time
        #          heat sink temperature
        (A, self.internal_temperature,
         self.voltage1, self.voltage2,
         self.current1, self.current2,
         B, C, D,
         self.energy_today, D,
         self.power1, self.power2,
         self.grid_current, self.grid_voltage, self.grid_frequency,
         self.power_total, self.energy_total, self.E) = struct.unpack(fmt, data)

        # unit conversion
        self.internal_temperature *= 0.1  # Celsius
        self.voltage1 *= 0.1  # V
        self.voltage2 *= 0.1  # V
        self.current1 *= 0.1  # A
        self.current2 *= 0.1  # A
        self.power1 *= 1.0  # W
        self.power2 *= 1.0  # W
        self.grid_frequency *= 0.01  # Hz
        self.grid_current *= 0.1  # A
        self.grid_voltage *= 0.1  # V
        self.power_total *= 1.0  # W
        self.energy_today *= 0.01  # kWh
        self.energy_total *= 0.1  # kWh

    @classmethod
    def header(cls):
        return "\t".join(('T [C]',
                          'V1 [V]',
                          'V2 [V]',
                          'A1 [A]',
                          'A2 [A]',
                          'P1 [W]',
                          'P2 [W]',
                          'P [W]'
                          'Ed [kWh]',
                          'E [kWh]',
                          'GV [V]',
                          'GA [A]',
                          'Gf [Hz]'))

    def __str__(self):
        return "\t".join(map(str, (
            self.internal_temperature,
            self.voltage1,
            self.voltage2,
            self.current1,
            self.current2,
            self.power1,
            self.power2,
            self.power_total,
            self.energy_today,
            self.energy_total,
            self.grid_voltage,
            self.grid_current,
            self.grid_frequency)))

##########################################################################
##########################################################################
##########################################################################
##########################################################################
# Daemon part
##########################################################################


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
        self.rrd_power = os.path.join(self.rrd_directory, 'solar_power.rrd')
        self.rrd_energy = os.path.join(self.rrd_directory, 'solar_energy.rrd')
        self.rrd_grid = os.path.join(self.rrd_directory, 'solar_grid.rrd')

    def setup_connection(self):

        logger.debug("TCP:%i opening" % TCP_PORT)
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                tcp.bind((TCP_HOST, TCP_PORT))
            except socket.error, msg:
                logger.debug("error connecting: %s - retry in 20s" % msg)
                time.sleep(20)
                continue
            break

        logger.debug("TCP:%i listening" % TCP_PORT)
        tcp.settimeout(20)

        while True:
            pid = os.fork()

            if pid == 0:

                logger.debug("UDP:%i sending welcome" % UDP_PORT)
                # wait 1 second
                time.sleep(1)

                udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                udp.bind(('', 0))
                udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                udp.sendto(toMsg(UDP_MESSAGE), ('<broadcast>', UDP_PORT))

                udp.close()
                logger.debug("UDP:%i closed" % UDP_PORT)
                # exit child process
                os._exit(0)

            else:
                logger.debug("TCP: waiting for contact from inverter")

                try:
                    tcp.listen(1)
                    conn, addr = tcp.accept()
                except socket.timeout:
                    logger.debug("no connection - retrying")
                    continue

                logger.debug('TCP: connected to inverter: %s:%s' %
                             (str(addr), str(conn)))

                logger.debug("sent message 1")
                conn.send(toMsg(TCP_MESSAGE_QUERY1))
                data = conn.recv(1024)

                logger.debug("sent message 2")
                conn.send(toMsg(TCP_MESSAGE_QUERY2))
                data = conn.recv(1024)

                logger.debug("sent message 3")
                conn.send(toMsg(TCP_MESSAGE_QUERY3))
                data = conn.recv(1024)
                break

        return tcp, conn

    def run(self):
        '''main loop. 
        '''

        self.createDatabase()

        while True:

            logger.info("trying to connect to inverter")
            tcp, conn = self.setup_connection()
            self.connection = conn

            while True:
                try:
                    logger.debug("getting data")
                    conn.send(toMsg(TCP_MESSAGE_QUERY_DATA))
                    data = conn.recv(1024)
                except OSError:
                    break

                if len(data) == 63:
                    values = fromMsg(data)
                    logger.debug("%s" % str(values))
                else:
                    logger.debug("received %i bytes" % len(data))
                    values = None

                if values:
                    self.updateDatabase(values)

                if len(data) == 0:
                    logger.warn(
                        "received 0 bytes - closing connection and restarting")
                    conn.close()
                    tcp.close()
                    break

                time.sleep(HEART_BEAT)

            logger.warn("lost connection - will retry")

    def updateDatabase(self, values):
        '''update rrd database with values'''
        rrdtool.update(self.rrd_power,
                       "N:" + ":".join(map(str, (values.voltage1,
                                                 values.voltage2,
                                                 values.current1,
                                                 values.current2,
                                                 values.power1,
                                                 values.power2,
                                                 values.power_total))))

        rrdtool.update(self.rrd_energy,
                       "N:" + ":".join((map(str, (values.energy_total,
                                                  values.energy_today)))))

        rrdtool.update(self.rrd_grid,
                       "N:" + ":".join((map(str, (values.internal_temperature,
                                                  values.grid_frequency,
                                                  values.grid_voltage,
                                                  values.grid_current)))))

    def createDatabase(self):
        '''create rrd databases. Existing databases will not be overwritten'''

        params = globals()
        params.update(locals())

        if not os.path.exists(self.rrd_power):
            logging.info("creating new rrd database %s" % self.rrd_power)
            data_sources = []
            for profile in DAILY_PROFILES:
                prefix, suffix = profile.split("_")
                mi, ma = RANGES[prefix]
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

        if not os.path.exists(self.rrd_energy):
            logging.info("creating new rrd database %s" % self.rrd_energy)
            data_sources = []
            for profile in DAILY_ENERGY:
                prefix, suffix = profile.split("_")
                mi, ma = RANGES[prefix]
                data_sources.append(
                    'DS:%s:GAUGE:1400:%i:%i' % (profile, mi, ma))

            rra = [
                'RRA:MAX:0.5:1440:7300']

            rrdtool.create(self.rrd_energy,
                           '--step', '60',
                           *data_sources + rra)

        if not os.path.exists(self.rrd_grid):
            logging.info("creating new rrd database %s" % self.rrd_grid)

            data_sources = []
            for profile in DAILY_GRID:
                prefix, suffix = profile.split("_")
                mi, ma = RANGES[prefix]
                data_sources.append(
                    'DS:%s:GAUGE:120:%i:%i' % (profile, mi, ma))

            lt_values_per_aggregate = 24 * 60
            params.update(locals())

            rra = [
                # medium term - 5 minute min/max/average
                'RRA:AVERAGE:0.5:%(MEDIUM_TERM_VALUES_PER_AGGREGATE)i:%(MEDIUM_TERM_NUM_VALUES)i',
                'RRA:MIN:0.5:%(MEDIUM_TERM_VALUES_PER_AGGREGATE)i:%(MEDIUM_TERM_NUM_VALUES)i',
                'RRA:MAX:0.5:%(MEDIUM_TERM_VALUES_PER_AGGREGATE)i:%(MEDIUM_TERM_NUM_VALUES)i',
                # long-term - keep daily min/max/average
                'RRA:MIN:0.5:%(lt_values_per_aggregate)i:%(LONG_TERM_DAYS)i',
                'RRA:MAX:0.5:%(lt_values_per_aggregate)i:%(LONG_TERM_DAYS)i',
                'RRA:AVERAGE:0.5:%(lt_values_per_aggregate)i:%(LONG_TERM_DAYS)i']

            rra = [x % params for x in rra]
            rrdtool.create(self.rrd_grid,
                           '--step', '60',
                           *data_sources + rra)

    def __del__(self):
        if self.connection:
            self.connection.close()

app = App()
logger = logging.getLogger("DaemonLog")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler("/mnt/ramdisk/solar.log")
handler.setFormatter(formatter)
logger.addHandler(handler)

daemon_runner = runner.DaemonRunner(app)
# This ensures that the logger file handle does not get closed during
# daemonization
daemon_runner.daemon_context.files_preserve = [handler.stream]
daemon_runner.do_action()
