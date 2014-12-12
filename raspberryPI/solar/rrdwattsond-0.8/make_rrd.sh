#!/bin/sh

# make a rrd for wattson

if [ -e wattson.rrd ]; then
    echo "wattson.rrd already exists!"
    exit 1
fi

# 1.1.2011 00:00:00 EET
MINTIME=1293832800

# Use default base interval (-s 300) = 300s = 5mins
# heartbeat is 600 s (10 mins)
# Compute min/avg/max for
# RRA: 50% of undefined values(0.5)
# A: interval=5m, keep 168h = 7 days  
# B: interval=30m, keep for 14 days
# C: interval=1h, keep for 30 days (~1 month)
# D: interval=2h, keep for 66 days (~2 months)
# E: interval=24h, keep for 3650 days (~10 years)
# LAST: keep value every 5 mins for 50 hours

# watthour is computed from avgwatt (collected every five minutes)
# by dividing by 12

rrdtool create wattson.rrd -b $MINTIME \
DS:minwatt:GAUGE:600:U:U \
DS:avgwatt:GAUGE:600:U:U \
DS:maxwatt:GAUGE:600:U:U \
DS:watthour:COMPUTE:avgwatt,12,/ \
RRA:MIN:0.5:1:2016 \
RRA:MIN:0.5:6:700 \
RRA:MIN:0.5:12:720 \
RRA:MIN:0.5:24:800 \
RRA:MIN:0.5:288:3650 \
RRA:AVERAGE:0.5:1:2016 \
RRA:AVERAGE:0.5:6:700 \
RRA:AVERAGE:0.5:12:720 \
RRA:AVERAGE:0.5:24:800 \
RRA:AVERAGE:0.5:288:3650 \
RRA:MAX:0.5:1:2016 \
RRA:MAX:0.5:6:700 \
RRA:MAX:0.5:12:720 \
RRA:MAX:0.5:24:800 \
RRA:MAX:0.5:288:3650 \
RRA:LAST:0.5:1:600
