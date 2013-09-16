#!/bin/bash

echo "pi-mid"
echo "setting up monitoring of solar and temperature"

mv monitor_solar.sh /etc/init.d/monitor_solar
chmod 755 /etc/init.d/monitor_solar
mv monitor_solar.py /usr/share/solar/monitor_solar.py
chmod u+x /etc/init.d/monitor_solar
update-rc.d monitor_solar defaults 80
mv solarweb.py /usr/lib/cgi-bin/

mv monitor_temperature.sh /etc/init.d/monitor_temperature
chmod 755 /etc/init.d/monitor_temperature
mv monitor_temperature.py /usr/share/solar/monitor_temperature.py
chmod u+x /etc/init.d/monitor_temperature
update-rc.d monitor_temperature defaults 80

mv temperatureweb.py /usr/lib/cgi-bin/
chown -R www-data:www-data /usr/lib/cgi-bin/temperatureweb.py /usr/lib/cgi-bin/solarweb.py /mnt/ramdisk

# sudo rename 's/S01/S90/' /etc/rc*.d/S*monito*
