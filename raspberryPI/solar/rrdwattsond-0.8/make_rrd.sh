#!/bin/sh

# make a rrd for wattson

if [ -e wattson.rrd ]; then
    echo "wattson.rrd already exists!"
    exit 1
fi

# 1.1.2011 00:00:00 EET
MINTIME=1293832800

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
