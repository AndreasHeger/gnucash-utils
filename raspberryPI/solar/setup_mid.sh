#!/bin/bash

echo "setting up: mid-pi"
echo "mid-pi" > /etc/hostname

echo "activating solar and temperature monitoring"
# update-rc.d monitor_weather defaults 80
update-rc.d monitor_temperature defaults 80
update-rc.d monitor_solar defaults 80
sudo rename 's/S01/S90/' /etc/rc*.d/S*monito*

echo "setting up mirroring"
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

echo "setting up mirroring"

cd
mkdir mirror
cd mirror
ln -fs ../Projects/raspberryPI/solar/mirror_*.ini .
ln -fs ../Projects/raspberryPI/solar/mirror.sh .
ln -fs ../Projects/raspberryPI/solar/solar_mirror.py .

cat <<EOC | crontab
SHELL=/bin/bash
# daily backup from ramdisk to SD card
@daily  /etc/init.d/ramdisk sync >> /dev/null 2>&1
# mirroring: run 30 minutes after one am, every day
30 1 * * *    (cd /home/pi/mirror; ./mirror.sh >> /mnt/ramdisk/mirroring.log 2>&1)
EOC


