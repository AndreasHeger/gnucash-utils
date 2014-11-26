#!/bin/bash

echo "top-pi"
echo "setting up monitoring of weather and temperature"

echo "top-pi" > /etc/hostname

if grep --quiet ramdisk /etc/fstab; then
    echo "fstab entry for ramdisk exists"
else
    echo "fstab entry for ramdisk does not exist, setup unionfs first"
    exit 0
fi



apt-get -y install rrdtool python-rrdtool python-daemon ganglia-webfrontend

mkdir /usr/share/solar
mkdir /usr/lib/cgi-bin

echo "setting up monitoring of temperature and weather"

cp monitor_weather.sh /etc/init.d/monitor_weather
chmod 755 /etc/init.d/monitor_weather
cp monitor_weather.py /usr/share/solar/monitor_weather.py
cp Utils.py /usr/share/solar/Utils.py
chmod u+x /etc/init.d/monitor_weather
update-rc.d monitor_weather defaults 80

cp monitor_temperature.sh /etc/init.d/monitor_temperature
chmod 755 /etc/init.d/monitor_temperature
cp monitor_temperature.py /usr/share/solar/monitor_temperature.py
chmod u+x /etc/init.d/monitor_temperature
update-rc.d monitor_temperature defaults 80
cp *web.py Utils.py /usr/lib/cgi-bin/
chown -R www-data:www-data /usr/lib/cgi-bin/*.py /mnt/ramdisk
cp images/*.png /mnt/ramdisk
sudo rename 's/S01/S90/' /etc/rc*.d/S*monito*

##########################################################
# Turned off because of RO
#
# echo "Setting up ramdisk backup"
# mkdir /var/ramdisk-backup
# mv ramdisk_backup.sh /etc/init.d/ramdisk
# chmod 755 /etc/init.d/ramdisk
## chown root:root /etc/init.d/ramdisk

# update-rc.d ramdisk defaults 00 99
# 
# echo "# setting ramdisk backup"
# echo "@daily  /etc/init.d/ramdisk sync >> /dev/null 2>&1" | crontab


