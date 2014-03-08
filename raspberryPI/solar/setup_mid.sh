#!/bin/bash

echo "pi-mid"
echo "setting up monitoring of solar and temperature"

cp monitor_solar.sh /etc/init.d/monitor_solar
chmod 755 /etc/init.d/monitor_solar
cp monitor_solar.py /usr/share/solar/monitor_solar.py
chmod u+x /etc/init.d/monitor_solar
update-rc.d monitor_solar defaults 80
cp solarweb.py /usr/lib/cgi-bin/

cp monitor_temperature.sh /etc/init.d/monitor_temperature
chmod 755 /etc/init.d/monitor_temperature
cp monitor_temperature.py /usr/share/solar/monitor_temperature.py
chmod u+x /etc/init.d/monitor_temperature
update-rc.d monitor_temperature defaults 80

cp images/*.png /mnt/ramdisk
cp *web.py Utils.py /usr/lib/cgi-bin/
chown -R www-data:www-data /usr/lib/cgi-bin/*.py /mnt/ramdisk

# sudo rename 's/S01/S90/' /etc/rc*.d/S*monito*
