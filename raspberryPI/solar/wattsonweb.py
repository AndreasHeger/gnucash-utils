#!/usr/bin/env python
import os
import time
import rrdtool

import Utils

DIR = '/mnt/ramdisk/'
OUTDIR = '/mnt/ramdisk/'
LOG = '/mnt/ramdisk/wattson.log'

WIDTH = 400
HEIGHT = 200

datestring = time.asctime(time.localtime(time.time()))

rrd = os.path.join(DIR, "wattson.rrd")

# daily - power
rrdtool.graph(
    os.path.join(OUTDIR, "wattson_daily.png"),
    "--start", "-1d",
    "--width", str(WIDTH),
    "--height", str(HEIGHT),
    "DEF:grid_power=%(rrd)s:grid_power:AVERAGE" % locals(),
    "DEF:solar_power=%(rrd)s:solar_power:AVERAGE" % locals(),
    "LINE1:grid_power#0000FF:'grid power'",
    "LINE1:solar_power#FF0000:'solar power'",
)

# weekly - power
rrdtool.graph(
    os.path.join(OUTDIR, "wattson_weekly.png"),
    "--start", "-7d",
    "--width", str(WIDTH),
    "--height", str(HEIGHT),
    "DEF:grid_power=%(rrd)s:grid_power:AVERAGE" % locals(),
    "DEF:solar_power=%(rrd)s:solar_power:AVERAGE" % locals(),
    "LINE1:grid_power#0000FF:'grid power'",
    "LINE1:solar_power#FF0000:'solar power'",
)

status = Utils.getStatusFromLog(LOG)
status_string = Utils.statusToHTML(status)

datestring = time.asctime(time.localtime(time.time()))

print "Content-Type: text/html"
print
print '''\
<html>
<body>
<h1>8A Harley Road Energy Usage</h1>
%(datestring)s
<p>%(status_string)s</p>
<form><button>Refresh</button></form>
<table>
<tr><th>Daily</th></tr>
<tr><td><img border="0" title="daily" alt="daily" src="../images/wattson_daily.png"></td></tr>
<tr><th>Weekly</th></tr>
<tr><td><img border="0" title="weekly" alt="weekly" src="../images/wattson_weekly.png"></td></tr>
</table>
</body>
</html>
''' % locals()
