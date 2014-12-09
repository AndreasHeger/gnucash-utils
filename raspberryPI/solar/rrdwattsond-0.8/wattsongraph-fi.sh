#!/bin/sh

# sleep 5 seconds that rrdwattsond has enough time to write data to RRD
sleep 5

cd /var/rrdwattsond

export LANG=fi_FI.UTF-8
export LC_ALL=fi_FI.UTF-8
export LANGUAGE=fi_FI.UTF-8

RRDTOOL=/usr/bin/rrdtool
OUTDIR=.
RRDFILE=wattson.rrd
WIDTH=600
HEIGHT=250

###########################################################################
NICETIME=`date "+%d.%m.%Y %H.%M"`
NOW=`date "+%Y-%m-%d %R %Z"`;
TRENDTIME=7200

for TIME in "25h" "1week" "1month" "1year"; do
  SUFF="-$TIME"
  [ "$TIME" = "25h" ] && SUFF=""
  [ "$TIME" = "1week" ] && TRENDTIME="43200"
  [ "$TIME" = "1month" ] && TRENDTIME="86400"
  [ "$TIME" = "1year" ] && TRENDTIME="604800"

  $RRDTOOL graph $OUTDIR/energy$SUFF.png -l 0 -X 1 -t "$NICETIME" \
    -v "Watts" --start -$TIME --width $WIDTH --height $HEIGHT \
  DEF:avg=$RRDFILE:avgwatt:AVERAGE \
  DEF:min=$RRDFILE:minwatt:MIN \
  DEF:max=$RRDFILE:maxwatt:MAX \
  DEF:avgl=$RRDFILE:avgwatt:LAST \
  DEF:minl=$RRDFILE:minwatt:LAST \
  DEF:maxl=$RRDFILE:maxwatt:LAST \
  CDEF:smoothed=avg,$TRENDTIME,TREND \
  TEXTALIGN:left \
  AREA:max#FFAAAA:"max      " \
  GPRINT:max:MAX:'%5.0lf W' \
  LINE:max#990000: \
  GPRINT:maxl:LAST:'(viim. %5.0lf W)\l' \
  AREA:avg#0095E4:"keskiarvo" \
  GPRINT:avg:AVERAGE:'%5.0lf W' \
  GPRINT:avg:LAST:'(viim. %5.0lf W)\l' \
  LINE:min#DFEBFA:"min      " \
  GPRINT:min:MIN:'%5.0lf W' \
  GPRINT:min:LAST:'(viim. %5.0lf W)\l' \
  LINE:avg#0000FF: \
  LINE2:smoothed#000000:"keskiarvotrendi" \
   >/dev/null
done
###########################################################################
