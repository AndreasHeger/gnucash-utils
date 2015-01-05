#!/usr/bin/env python

# http://www.gavinj.net/2012/06/building-python-daemon-process.html

import os
import sys
import time
import logging

from Monitor import Monitor

# third party libs
from daemon import runner

# for solar monitoring
import socket
import re
import struct

HEART_BEAT = 10

#####################################################
# Send UDP broadcast packets
#####################################################
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

    def items(self):
        return (
            ("Solar.InternalTemperature",
             self.internal_temperature),
            ("Solar.Voltage.West", self.voltage1),
            ("Solar.Voltage.East", self.voltage2),
            ("Solar.Current.West", self.current1),
            ("Solar.Current.East", self.current2),
            ("Solar.Power.West", self.power1),
            ("Solar.Power.East", self.power2),
            ("Solar.Grid.Frequency",
             self.grid_frequency),
            ("Solar.Grid.Current",
             self.grid_current),
            ("Solar.Grid.Voltage",
             self.grid_voltage),
            ("Solar.Power.Total",
             self.power_total),
            ("Solar.Energy.Today",
             self.energy_today),
            ("Solar.Energy.Total",
             self.energy_total))


class App(Monitor):

    label = "solar"

    def __init__(self, *args, **kwargs):

        Monitor.__init__(self, *args, **kwargs)
        # open tcp connection
        self.connection = None

    def setup(self):
        
        Monitor.setup(self)

        self.logger.debug("TCP:%i opening" % TCP_PORT)
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                tcp.bind((TCP_HOST, TCP_PORT))
            except socket.error, msg:
                logger.debug(
                    "error connecting: %s - retry in 20s" % msg)
                time.sleep(20)
                continue
            break

        self.logger.debug("TCP:%i listening" % TCP_PORT)
        tcp.settimeout(20)

        while True:
            pid = os.fork()

            if pid == 0:

                self.logger.debug("UDP:%i sending welcome" % UDP_PORT)
                # wait 1 second
                time.sleep(1)

                udp = socket.socket(socket.AF_INET,
                                    socket.SOCK_DGRAM)
                udp.bind(('', 0))
                udp.setsockopt(socket.SOL_SOCKET,
                               socket.SO_BROADCAST, 1)
                udp.setsockopt(socket.SOL_SOCKET,
                               socket.SO_REUSEADDR, 1)
                udp.sendto(toMsg(UDP_MESSAGE),
                           ('<broadcast>', UDP_PORT))

                udp.close()
                self.logger.debug("UDP:%i closed" % UDP_PORT)
                # exit child process
                os._exit(0)

            else:
                self.logger.debug(
                    "TCP: waiting for contact from inverter")

                try:
                    tcp.listen(1)
                    conn, addr = tcp.accept()
                except socket.timeout:
                    logger.debug("no connection - retrying")
                    continue

                self.logger.debug('TCP: connected to inverter: %s:%s' %
                             (str(addr), str(conn)))

                self.logger.debug("sent message 1")
                conn.send(toMsg(TCP_MESSAGE_QUERY1))
                data = conn.recv(1024)

                self.logger.debug("sent message 2")
                conn.send(toMsg(TCP_MESSAGE_QUERY2))
                data = conn.recv(1024)

                self.logger.debug("sent message 3")
                conn.send(toMsg(TCP_MESSAGE_QUERY3))
                data = conn.recv(1024)
                break

        self.connection = conn
        self.tcp = tcp

    def monitor(self):

        conn = self.connection
        tcp = self.tcp

        while True:
            try:
                logger.debug("getting data")
                conn.send(toMsg(TCP_MESSAGE_QUERY_DATA))
                data = conn.recv(1024)
            except OSError:
                break

            if len(data) == 0:
                self.logger.warn(
                    "received 0 bytes - closing connection "
                    "and restarting")
                conn.close()
                tcp.close()
                self.setup()
                continue

            if len(data) == 63:
                values = fromMsg(data)
                logger.info("%s" % str(values))
                logger.info("status: solar=ok")
            else:
                self.logger.debug("received %i bytes" % len(data))
                values = None
                self.logger.info("status: solar=fail")
            break

        return values

    def __del__(self):
        if self.connection:
            self.connection.close()

logger = logging.getLogger("DaemonLog")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler("/mnt/ramdisk/solar.log")
handler.setFormatter(formatter)
logger.addHandler(handler)

app = App(logger=logger, heart_beat=HEART_BEAT)
# app.run()

daemon_runner = runner.DaemonRunner(app)
# This ensures that the logger file handle does not get closed during
# daemonization
daemon_runner.daemon_context.files_preserve = [handler.stream]
daemon_runner.do_action()

