#!/bin/bash

echo "pi-top"
echo "setting up monitoring of weather and temperature"

cp monitor_weather.sh /etc/init.d/monitor_weather
chmod 755 /etc/init.d/monitor_weather
cp monitor_weather.py /usr/share/solar/monitor_weather.py
chmod u+x /etc/init.d/monitor_weather
update-rc.d monitor_weather defaults 80

cp monitor_temperature.sh /etc/init.d/monitor_temperature
chmod 755 /etc/init.d/monitor_temperature
cp monitor_temperature.py /usr/share/solar/monitor_temperature.py
chmod u+x /etc/init.d/monitor_temperature
update-rc.d monitor_temperature defaults 80
cp temperatureweb.py /usr/lib/cgi-bin/
chown -R www-data:www-data /usr/lib/cgi-bin/temperatureweb.py /mnt/ramdisk
cp images/*.png /mnt/ramdisk
sudo rename 's/S01/S90/' /etc/rc*.d/S*monito*
