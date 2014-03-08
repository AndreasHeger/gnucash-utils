#!/usr/bin/env python

import re
import os
import time
import socket
import datetime

HOSTNAME = socket.gethostname()
WIDTH = 400
HEIGHT = 200

DIR = "/mnt/ramdisk/"
OUTDIR = '/mnt/ramdisk/'
LOG = "/mnt/ramdisk/temperature.log"
LOG = "/home/andreas/temperature.log"


def getLastLine(filename, pattern, read_size=1024, max_lines=100):
    """return last lines of a file matching pattern.

    Only check up to *max_lines* lines.

    Returns an empty string if file is empty or no line
    matches the pattern.
    """

    # U is to open it with Universal newline support
    f = open(filename, 'rU')
    offset = read_size
    f.seek(0, 2)
    file_size = f.tell()
    if file_size == 0:
        return ""
    nlines = 0
    while 1:
        if file_size < offset:
            offset = file_size
        f.seek(-1 * offset, 2)
        read_str = f.read(offset)
        # Remove newline at the end
        if read_str[offset - 1] == '\n':
            read_str = read_str[:-1]
        lines = read_str.split('\n')
        nlines += len(lines)
        matching = [x for x in lines if pattern.search(x)]
        if len(matching) > 1:
            return matching[-1]
        if nlines > max_lines:
            return ""
        if offset == file_size:   # reached the beginning
            return read_str
        offset += read_size
    f.close()


# define the desired colors for the graphs
COLLECTIONS = {
    'top-pi':
    {'Attic': ('#FF0000', 57, 'Attic'),
     'AiringCabinet': ('#EA8C09', 57, 'AiringCabinet'),
     'KeevaCupBoard': ('#176C01', 57, 'KeevaCupBoard'),
     'KeevaRoomBack': ('#24AC02', 57, 'KeevaRoomBack'),
     'KeevaRoomTop': ('#31EA03', 57, 'KeevaRoomTop'),
     'NiamhRoomBack': ('#1647EA', 57, 'NiamhRoomBack'),
     'NiamhRoomTop': ('#17A8EA', 57, 'NiamhRoomTop'),
     'LandingTop': ('#10A8E0', 57, 'LandingTop'),
     },
    'mid-pi':
    {'LivingRoomWindow': ('#FF0000', 55, 'LivingRoomWindow'),
     'LivingRoomCupBoard': ('#990000', 55, 'LivingRoomCupBoard'),
     'LandingMiddle': ('#00AA00', 55, 'LandingMiddle'),
     'LandingBottom': ('#008800', 55, 'LandingBottom'),
     },
}


lastline = getLastLine(LOG, re.compile("INFO - status"))

d_date, d_time, status = re.match(
    "(\S+) (\S+) - DaemonLog - INFO - status: (\S+)",
    lastline).groups()

current_time=datetime.datetime.now()
log_time=datetime.datetime.strptime(
    "%s %s" % (d_date, d_time),
    "%Y-%m-%d %H:%M:%S,%f")

delta = current_time - log_time
if delta.total_seconds():
    status_string = '<img border="0" src="../images/not_available.png>'
else:
    status_string = []
    for section in status.split(","):
        key, value = section.split("=")
        if value == "ok":
            status_string.append(
                '<img border="0" src="../images/pass.png>')
        elif value == "fail":
            status_string.append(
                '<img border="0" src="../images/fail.png>')
    status_string = " ".join(status)

definition = 'DEF:%(key)s=%(DIR)s/temperature.rrd:%(key)s:AVERAGE'
line = 'LINE1:%(key)s%(color)s:"%(description)s [deg C]"'
statements = {'hourly': 'rrdtool graph %(OUTDIR)s/temperature_%(period)s.png --width %(WIDTH)i --height %(HEIGHT)i --start -4h',
              'daily': 'rrdtool graph %(OUTDIR)s/temperature_%(period)s.png  --width %(WIDTH)i --height %(HEIGHT)i --start -1d',
              'weekly': 'rrdtool graph %(OUTDIR)s/temperature_%(period)s.png --width %(WIDTH)i --height %(HEIGHT)i --start -7d', }

for period, statement_prefix in statements.items():
    section = HOSTNAME
    colors = COLLECTIONS[section]

    lines = []
    lines.append(statement_prefix % locals())

    for key, data in colors.items():
        color, networkid, location = data
        description = key

        lines.append(definition % locals())
        lines.append(line % locals())

    # add weather:
    if section == "top-pi":
        lines.append(
            'DEF:outside=%(DIR)s/weather.rrd:temperature:AVERAGE' % locals())
        lines.append('LINE1:outside#0000FF:"Outside"')

    lines.append("> %(OUTDIR)s/dashboard.log" % locals())
    statement = ' '.join(lines)
    os.system(statement)


datestring = time.asctime(time.localtime(time.time()))


print "Content-Type: text/html"
print
print '''\
<html>
<body>
<h1>8A Harley Road Dashboard - %(HOSTNAME)s</h1>
%(datestring)s
<p>%(status_string)s</p>
<form><button>Refresh</button></form>
<table>
<tr><th>Hourly</th></tr>
<tr><td><img border="0" title="hourly" alt="hourly" src="../images/temperature_hourly.png"></td></tr>
<tr><th>Daily</th></tr>
<tr><td><img border="0" title="daily" alt="daily" src="../images/temperature_daily.png"></td></tr>
<tr><th>Weekly</th></tr>
<tr><td><img border="0" title="weekly" alt="weekly" src="../images/temperature_weekly.png"></td></tr>
</table>
</body>
</html>
''' % locals()
