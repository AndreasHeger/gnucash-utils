#!/bin/bash
echo "pi-mid"

# once only: add the following to fstab
# tmpfs           /mnt/ramdisk tmpfs      defaults,size=256M 0 0
# 192.168.0.2:/volume1/data       /mnt/diskstation        nfs     user,noauto

mkdir /mnt/ramdisk
mkdir /mnt/diskstation

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

# setup mirroring
# Note: need to setup passwordless ssh beforehand
# ssh-copy-id -i .ssh/pi_rsa pi@192.168.0.55
# ssh-copy-id -i .ssh/pi_rsa pi@192.168.0.57
# ssh-copy-id -i .ssh/pi_rsa pi@192.168.0.59
# scp -i .ssh/pi_rsa .ssh/pi_rsa pi@192.168.0.55:.ssh/
# scp -i .ssh/pi_rsa .ssh/pi_rsa pi@192.168.0.57:.ssh/
# scp -i .ssh/pi_rsa .ssh/pi_rsa pi@192.168.0.59:.ssh/

# sudo rename 's/S01/S90/' /etc/rc*.d/S*monito*
# sudo apt-get install sqlite3 python-lxml
# make sure rpcbind is started at boot
# sudo update-rc.d rpcbind enable

cd
mkdir mirror
cd mirror
ln -fs ../Projects/raspberryPI/solar/mirror_*.ini .
ln -fs ../Projects/raspberryPI/solar/mirror.sh .
ln -fs ../Projects/raspberryPI/solar/solar_mirror.py .
