#!/usr/bin/env python
import os, time

DIR='/mnt/ramdisk/'
OUTDIR='/mnt/ramdisk/'
 
import rrdtool

rrd = os.path.join( DIR, "solar_power.rrd" )
rrd_energy = os.path.join( DIR, "solar_energy.rrd" )

# daily - power
rrdtool.graph( 
    os.path.join( OUTDIR,"power_daily.png"),
    "--start", "-1d",
    "--width", "700",
    "--height", "200",
    "DEF:power_1=%(rrd)s:power_1:AVERAGE" % locals(),
    "DEF:power_2=%(rrd)s:power_2:AVERAGE" % locals(),
    "DEF:power_total=%(rrd)s:power_total:AVERAGE" % locals(),
    "LINE1:power_1#0000FF:'power 1'",
    "LINE1:power_2#FF0000:'power 2'",
    "LINE1:power_total#00FF00:'power total'",
    )

# weekly - power
rrdtool.graph( 
    os.path.join( OUTDIR,"power_weekly.png"),
    "--start", "-7d",
    "--width", "700",
    "--height", "200",
    "DEF:power_1=%(rrd)s:power_1:AVERAGE" % locals(),
    "DEF:power_2=%(rrd)s:power_2:AVERAGE" % locals(),
    "DEF:power_total=%(rrd)s:power_total:AVERAGE" % locals(),
    "LINE1:power_1#0000FF:'power 1'",
    "LINE1:power_2#FF0000:'power 2'",
    "LINE1:power_total#00FF00:'power total'",
    )

# daily - voltage
rrdtool.graph( 
    os.path.join( OUTDIR,"voltage_daily.png"),
    "--start", "-1d",
    "--width", "700",
    "--height", "200",
    "DEF:voltage_1=%(rrd)s:voltage_1:AVERAGE" % locals(),
    "DEF:voltage_2=%(rrd)s:voltage_2:AVERAGE" % locals(),
    "LINE1:voltage_1#0000FF:'voltage 1'",
    "LINE1:voltage_2#FF0000:'voltage 2'",
    )

# weekly - voltage
rrdtool.graph( 
    os.path.join( OUTDIR,"voltage_weekly.png"),
    "--start", "-7d",
    "--width", "700",
    "--height", "200",
    "DEF:voltage_1=%(rrd)s:voltage_1:AVERAGE" % locals(),
    "DEF:voltage_2=%(rrd)s:voltage_2:AVERAGE" % locals(),
    "LINE1:voltage_1#0000FF:'voltage 1'",
    "LINE1:voltage_2#FF0000:'voltage 2'",
    )

# power generated over the last 3 month
rrdtool.graph( 
    os.path.join( OUTDIR,"energy.png"),
    "--start", "-90d",
    "--width", "700",
    "--height", "200",
    "DEF:energy_daily=%(rrd_energy)s:energy_daily:MAX" % locals(),
    "LINE1:energy_daily#FF0000:'energy / kWh'",
    )

import cgi

datestring = time.asctime(time.localtime(time.time()))

print "Content-Type: text/html"
print
print '''\
<html>
<body>
<h1>8A Harley Road Solar</h1>
%(datestring)s
<form><button>Refresh</button></form>
<table>
<tr><th>Daily</th></tr>
<tr><td><img border="0" title="daily" alt="daily" src="../images/power_daily.png"></td></tr>
<tr><th>Weekly</th></tr>
<tr><td><img border="0" title="weekly" alt="weekly" src="../images/power_weekly.png"></td></tr>
<tr><th>Daily</th></tr>
<tr><td><img border="0" title="daily" alt="daily" src="../images/voltage_daily.png"></td></tr>
<tr><th>Weekly</th></tr>
<tr><td><img border="0" title="weekly" alt="weekly" src="../images/voltage_weekly.png"></td></tr>
<tr><th>Energy</th></tr>
<tr><td><img border="0" title="weekly" alt="weekly" src="../images/energy.png"></td></tr>
</table>
</body>
</html>
''' % locals()

