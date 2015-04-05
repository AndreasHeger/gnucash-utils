#!/bin/bash

echo "setting up: master-pi"
echo "master-pi" > /etc/hostname

# make sure rpcbind is started at boot
update-rc.d rpcbind enable

echo "activating solar and temperature monitoring"
# update-rc.d monitor_weather defaults 80
# update-rc.d monitor_temperature defaults 80
update-rc.d monitor_solar defaults 80
sudo rename 's/S01/S90/' /etc/rc*.d/S*monito*

echo "activating carbon-cache daemon"
update-rc.d carbon-cache defaults 80

echo "activating dashing"
update-rc.d dashing defaults 80

# echo "setting up mirroring"
# setup mirroring
# Note: you need to setup passwordless ssh beforehand
# by running:
# ssh-copy-id -i .ssh/pi_rsa pi@192.168.0.55
# ssh-copy-id -i .ssh/pi_rsa pi@192.168.0.57
# ssh-copy-id -i .ssh/pi_rsa pi@192.168.0.59
# scp -i .ssh/pi_rsa .ssh/pi_rsa pi@192.168.0.55:.ssh/
# scp -i .ssh/pi_rsa .ssh/pi_rsa pi@192.168.0.57:.ssh/
# scp -i .ssh/pi_rsa .ssh/pi_rsa pi@192.168.0.59:.ssh/

# apt-get install sqlite3 python-lxml
# cd
# mkdir mirror
# cd mirror
# ln -fs ../Projects/raspberryPI/solar/mirror_*.ini .
# ln -fs ../Projects/raspberryPI/solar/mirror.sh .
# ln -fs ../Projects/raspberryPI/solar/solar_mirror.py .

# cat <<EOC | crontab
# SHELL=/bin/bash
# # daily backup from ramdisk to SD card
# @daily  /etc/init.d/ramdisk sync >> /dev/null 2>&1
# # mirroring: run 30 minutes after one am, every day
# 30 1 * * *    (cd /home/pi/mirror; ./mirror.sh >> /mnt/ramdisk/mirroring.log 2>&1)
# EOC

