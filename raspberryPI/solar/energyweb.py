#!/usr/bin/env python
import os
import time
import rrdtool

import Utils

DIR = '/mnt/ramdisk/'
OUTDIR = '/mnt/ramdisk/'
LOG = '/mnt/ramdisk/energy.log'

WIDTH = 400
HEIGHT = 200

datestring = time.asctime(time.localtime(time.time()))

rrd = os.path.join(DIR, "wattson.rrd")

for period, trendtime in (("weekly", 43200),
                           ("daily", 7200)):
    rrdtool.graph(
        os.path.join(OUTDIR, "usage_%s.png" % period),
        "--start", "-%s" % period,
        "--width", str(WIDTH),
        "--height", str(HEIGHT),
        "-v 'Watts'",
        "-t '%s' "% datestring,
        "DEF:avg=%(rrd)s:avgwatt:AVERAGE" % locals(),
        "DEF:min=%(rrd)s:minwatt:MIN" % locals(),
        "DEF:max=%(rrd)s:maxwatt:MAX" % locals(),
        "DEF:avgl=%(rrd)s:avgwatt:LAST" % locals(),
        "DEF:minl=%(rrd)s:minwatt:LAST" % locals(),
        "DEF:maxl=%(rrd)s:maxwatt:LAST" % locals(),
        "CDEF:smoothed=avg,%(trendtime)i,TREND" % locals(),
        "TEXTALIGN:left",
        "AREA:max#FFAAAA:'max    '",
        "GPRINT:max:MAX:'%5.0lf W'",
        "LINE:max#990000:",
        "GPRINT:maxl:LAST:'(last %5.0lf W)\l'",
        "AREA:avg#0095E4:'average'",
        "GPRINT:avg:AVERAGE:'%5.0lf W'",
        "GPRINT:avg:LAST:'(last %5.0lf W)\l'",
        "LINE:min#DFEBFA:'min    '",
        "GPRINT:min:MIN:'%5.0lf W'",
        "GPRINT:min:LAST:'(last %5.0lf W)\l'",
        "LINE:avg#0000FF:",
        "LINE2:smoothed#000000:'average trend'"
    )


# status = Utils.getStatusFromLog(LOG)
# status_string = Utils.statusToHTML(status)
status_string = ""


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
<tr><td><img border="0" title="daily" alt="daily" src="../images/usage_daily.png"></td></tr>
<tr><th>Weekly</th></tr>
<tr><td><img border="0" title="weekly" alt="weekly" src="../images/usage_weekly.png"></td></tr>
</table>
</body>
</html>
''' % locals()
