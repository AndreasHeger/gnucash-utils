#!/usr/bin/env python

# http://www.gavinj.net/2012/06/building-python-daemon-process.html

import time
import logging
import serial
import re

# third party libs
from daemon import runner
from Monitor import Monitor


class App(Monitor):

    def __init__(self, *args, **kwargs):
        
        Monitor.__init__(self, *args, **kwargs)

        self.port = '/dev/ttyUSB0'
        # stty settings
        self.stty = "5:0:8be:0:0:0:0:0:0:a" + ":0" * 26

    def communicate(self, command):
        '''communicate with wattson energy monitor'''

        self.logger.debug('sending commands %s' % command)
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

        self.logger.debug("received %i bytes after %i tries" %
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
        
    def setup(self):

        Monitor.setup(self)
        self.logger.debug("wattson: port=%s" % self.port)
        
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

        self.logger.info("connected to wattson device %s" % data)

    def monitor(self):
        '''
        '''
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

        self.logger.debug(
            "acquired values: grid=%s, solar=%s" %
            (grid_power, solar_power))

        self.logger.debug(
            "status: grid=%s, solar=%s" %
            (grid_status, solar_status))

        values = {'WattsonGridPower': grid_power,
                  'WattsonSolarPower': solar_power}

        return values

logger = logging.getLogger("DaemonLog")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler("/mnt/ramdisk/wattson.log")
handler.setFormatter(formatter)
logger.addHandler(handler)
app = App(logger=logger, heart_beat=1)
# app.run()

daemon_runner = runner.DaemonRunner(app)
# This ensures that the logger file handle does not get closed during
# daemonization
daemon_runner.daemon_context.files_preserve = [handler.stream]
daemon_runner.do_action()
