#!/usr/bin/env python
import os, time

DIR="/mnt/ramdisk/unspecified/192.168.0."
OUTDIR='/mnt/ramdisk/'
 
#define the desired colors for the graphs
COLLECTIONS = {
    'top' :
        { 'Attic'         : ('#FF0000', 57, 'RT_Attic' ),
          'AiringCabinet' : ('#EA8C09', 57, 'RT_AiringCabinet' ),
          'KeevaCupBoard' : ('#176C01', 57, 'RT_KeevaCupBoard' ),
          'KeevaRoomBack' : ('#24AC02', 57, 'RT_KeevaRoomBack' ),
          'KeevaRoomTop'  : ('#31EA03', 57, 'RT_KeevaRoomTop' ),
          'NiamhRoomBack' : ('#1647EA', 57, 'RT_NiamhRoomBack' ),
          'NiamhRoomTop'  : ('#17A8EA', 57, 'RT_NiamhRoomTop' ),
          'Outside'       : ('#0000FF', 57, 'WEATHER_temperature' ),
          },
    'middle': 
    { 'LivingRoomWindow'   : ('#FF0000', 55, 'RT_LivingRoomWindow' ),
      'LivingRoomCupBoard' : ('#990000', 55, 'RT_LivingRoomCupBoard' ),
      'LandingTop'         : ('#00FF00', 57, 'RT_LandingTop' ),
      'LandingMiddle'      : ('#00AA00', 55, 'RT_LandingMiddle' ),
      'LandingBottom'      : ('#008800', 55, 'RT_LandingBottom' ),
      'Outside'            : ('#0000FF', 57, 'WEATHER_temperature' ),
      },
    }

definition = 'DEF:%(key)s=%(DIR)s%(networkid)i/%(location)s.rrd:sum:AVERAGE'
line = 'LINE1:%(key)s%(color)s:"%(description)s [deg C]"' 
statements = { 'hourly': 'rrdtool graph %(OUTDIR)s/%(section)s_%(period)s.png --width 700 --height 200 --start -4h',
               'daily': 'rrdtool graph %(OUTDIR)s/%(section)s_%(period)s.png  --width 700 --height 200 --start -1d',
               'weekly': 'rrdtool graph %(OUTDIR)s/%(section)s_%(period)s.png --width 700 --height 200 --start -7d', }
               
for period, statement_prefix in statements.items(): 
    for section, colors in COLLECTIONS.items():
        lines = []
        lines.append( statement_prefix % locals() )

        for key, data in colors.items():
            color, networkid, location = data
            description = key

            lines.append( definition % locals() )
            lines.append( line % locals() )

        lines.append( "> %(OUTDIR)s/dashboard.log" % locals())
        statement = ' '.join( lines )
        os.system( statement )

import cgi

datestring = time.asctime(time.localtime(time.time()))

print "Content-Type: text/html"
print
print '''\
<html>
<body>
<h1>8A Harley Road Dashboard</h1>
%(datestring)s
<form><button>Refresh</button></form>
<table>
<tr><th>Hourly</th></tr>
<tr><td><img border="0" title="hourly" alt="hourly" src="../images/top_hourly.png"></td></tr>
<tr><th>Daily</th></tr>
<tr><td><img border="0" title="daily" alt="daily" src="../images/top_daily.png"></td></tr>
<tr><th>Weekly</th></tr>
<tr><td><img border="0" title="weekly" alt="weekly" src="../images/top_weekly.png"></td></tr>
<tr><th>Hourly</th></tr>
<tr><td><img border="0" title="hourly" alt="hourly" src="../images/middle_hourly.png"></td></tr>
<tr><th>Daily</th></tr>
<tr><td><img border="0" title="daily" alt="daily" src="../images/middle_daily.png"></td></tr>
<tr><th>Weekly</th></tr>
<tr><td><img border="0" title="weekly" alt="weekly" src="../images/middle_weekly.png"></td></tr>
</table>
</body>
</html>
''' % locals()

