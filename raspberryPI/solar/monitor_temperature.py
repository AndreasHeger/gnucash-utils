#!/usr/bin/env python
'''Monitor temperature.

Adding a new sensor
===================

1. Mirror all data. The steps below will delete the values in the
   existing rrd database.

2. Add columns for the new sensor to the relevant tables in the sqlite
   database. For example::

      for x in `sqlite3 csvdb ".tables" | xargs --max-args=1 | grep top_temperature`; do  \
           sqlite3 csvdb "ALTER TABLE $x ADD COLUMN BoilerWater FLOAT;"; done

3. Stop the monitoring daemon

3. Delete old rrd database. For example::

      rm /mnt/ramdisk/temperature.rrd

4. Restart the monitoring daemon. The new rrd will be
   automatically created.

'''

import logging
import subprocess
import socket
from Monitor import Monitor

# third party libs
from daemon import runner

HOSTNAME = socket.gethostname()

CONFIG = {
    "Temperature.TopFloor.FrontFloor": '10-0008029db5bc',
    "Temperature.TopFloor.FrontWall": 'o28.3DA0D4040000',
    "Temperature.TopFloor.FrontCupBoard": '10-0008029d938d',
    "Temperature.TopFloor.AiringCabinet": '10-0008029db6c3',
    "Temperature.TopFloor.Attic": '10-0008029da542',
    "Temperature.TopFloor.BackFloor": "o28.6BFED3040000",
    "Temperature.TopFloor.BackWall": "o28.45C0D4040000",
    "Temperature.LivingRoom.Window": "28-000004d41fb1",
    "Temperature.LivingRoom.CupBoard": "28-000004d45cae",
    "Temperature.Landing.Top": "o10.ED859D020800",
    "Temperature.Landing.Middle": "28-000004d3f73e",
    "Temperature.Landing.Bottom": "10-0008029dc359",
    "Temperature.Water.Tank": "o10.B1B29D020800",
    "Temperature.Water.Boiler": "o10.0ec89d020800",
    "Temperature.Hallway.Top": "28-000004d49218",
    "Temperature.Hallway.Bottom": "28-00000584f21d",
    "Temperature.GroundFloor.BackDoor": "28-000004d422f5",
    "Temperature.GroundFloor.BackWindow": "28-0000058528bc",

}

SENSOR_GROUPS = [
    ("Temperature.TopFloor.FrontFloor",
     "Temperature.TopFloor.FrontWall",
     "Temperature.TopFloor.FrontCupBoard",
     "Temperature.TopFloor.AiringCabinet",
     "Temperature.TopFloor.Attic",
     "Temperature.TopFloor.BackFloor",
     "Temperature.TopFloor.BackWall",
     "Temperature.Landing.Top",
     "Temperature.Water.Tank",
     "Temperature.Water.Boiler"),
    ("Temperature.LivingRoom.Window",
     "Temperature.LivingRoom.CupBoard",
     "Temperature.Landing.Middle",
     "Temperature.Landing.Bottom"),
    ("Temperature.Hallway.Top",
     "Temperature.Hallway.Bottom",
     "Temperature.GroundFloor.BackDoor",
     "Temperature.GroundFloor.BackWindow"),
]

CACHE = {}

# set heart-beat
HEART_BEAT = 10


class App(Monitor):

    def __init__(self, *args, **kwargs):
        Monitor.__init__(self, *args, **kwargs)

        if HOSTNAME == "top-pi":
            self.sensor_group = 0
        elif HOSTNAME == "mid-pi":
            self.sensor_group = 1
        elif HOSTNAME == "bottom-pi":
            self.sensor_group = 2
        else:
            raise ValueError('unknown host')
            
    def monitor(self):
        '''acquire values
        '''

        values = {}
        success = {}
        for key in SENSOR_GROUPS[self.sensor_group]:
            logger.debug("acquiring %s" % key)
            fn = CONFIG[key]

            if fn[0] == "o":
                try:
                    temperature = subprocess.check_output(
                        ["owread", "/%s/temperature" % fn[1:]])
                    success[key] = 'ok'
                except subprocess.CalledProcessError:
                    logger.debug("%s from cache" % key)
                    temperature = CACHE.get(key, 0)
                    success[key] = 'fail'
                temperature = float(temperature)
            else:
                try:
                    tfile = open(
                        "/sys/bus/w1/devices/w1_bus_master1/%s/w1_slave" % fn)
                except IOError:
                    tfile = None
                if tfile:
                    text = tfile.readlines()
                    tfile.close()
                    status, temperature_data = text
                    if not status.endswith("YES\n"):
                        logger.debug("%s from cache" % key)
                        temperature = CACHE.get(key, 0)
                    else:
                        temperature_data = temperature_data.split()[-1]
                        temperature = float(temperature_data[2:])
                        temperature = temperature / 1000
                    success[key] = 'ok'
                else:
                    logger.debug("%s from cache" % key)
                    success[key] = 'fail'
                    temperature = CACHE.get(key, 0)

            CACHE[key] = temperature
            values[key] = temperature
            self.logger.debug(
                "status: %s" %
                (",".join(
                    ['%s=%s' % (x, y) for x, y in success.items()])))

        return values

logger = logging.getLogger("DaemonLog")
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler("/mnt/ramdisk/temperature.log")
handler.setFormatter(formatter)
logger.addHandler(handler)

app = App(logger=logger, heart_beat=HEART_BEAT)

daemon_runner = runner.DaemonRunner(app)
# This ensures that the logger file handle does not get closed during
# daemonization
daemon_runner.daemon_context.files_preserve = [handler.stream]
daemon_runner.do_action()
