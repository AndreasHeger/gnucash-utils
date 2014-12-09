#!/bin/sh -x

if [ `whoami` != "root" ] ;then
   echo "use sudo -s and run $0 as root"
   exit
fi

mkdir -p /usr/local/bin
cp rrdwattsond /usr/local/bin/
cp rrdwattsond.init /etc/init.d/rrdwattsond
cp rrdwattsond.conf.dist /etc/rrdwattsond.conf
cp wattsongraph-en.sh /usr/local/bin/
cp wattsongraph-fi.sh /usr/local/bin/
./make_rrd.sh
mv wattson.rrd /mnt/ramdisk
chmod a+x /usr/local/bin/rrdwattsond /etc/init.d/rrdwattsond
chmod a+x /usr/local/bin/wattsongraph-fi.sh /usr/local/bin/wattsongraph-en.sh
cd /etc/rc2.d
ln -s ../init.d/rrdwattsond S99rrdwattsond
cd /etc/rc3.d
ln -s ../init.d/rrdwattsond S99rrdwattsond

echo "NOW edit /etc/rrdwattsond.conf and then start it by command:"
echo "/etc/init.d/rrdwattsond start"

