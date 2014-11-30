# Commands to make a raspbian image RO.
# 
# See: http://openenergymonitor.org/emon/node/5331

apt-get -y update
apt-get -y upgrade

apt-get -y remove --purge wolfram-engine triggerhappy
# Remove X-Server and related stuff:
apt-get -y remove --purge xserver-common lightdm
insserv -r x11-common

# auto-remove some X11 related libs
apt-get -y autoremove --purge

# install packages required for monitoring
apt-get -y install rrdtool python-rrdtool python-daemon apache2

# turn off 
if [ ! -e /etc/default/rcS.orig ]; then
cp /etc/default/rcS /etc/default/rcS.orig
sh -c "echo 'RAMTMP=yes' >> /etc/default/rcS"
fi

mkdir /mnt/ramdisk

# create fstab
if [ ! -e /etc/fstab.orig ] ; then
mv /etc/fstab /etc/fstab.orig
sh -c "echo 'tmpfs           /tmp            tmpfs   nodev,nosuid,size=30M,mode=1777       0    0' >> /etc/fstab"
sh -c "echo 'tmpfs           /var/log        tmpfs   nodev,nosuid,size=30M,mode=1777       0    0' >> /etc/fstab"
sh -c "echo 'proc            /proc           proc    defaults                              0    0' >> /etc/fstab"
sh -c "echo '/dev/mmcblk0p1  /boot           vfat    defaults                              0    2' >> /etc/fstab"
sh -c "echo '/dev/mmcblk0p2  /               ext4    defaults,ro,noatime,errors=remount-ro 0    1' >> /etc/fstab"
# add ramdisk for monitoring
sh -c "echo 'tmpfs           /mnt/ramdisk    tmpfs   defaults,size=200M                    0    0' >> /etc/fstab"
# add mount point for diskstation
sh -c "echo '192.168.0.2:/volume1/data       /mnt/diskstation        nfs     user,noauto' >> /etc/fstab"
sh -c "echo ' ' >> /etc/fstab"
fi

if [ ! -e /etc/mtab.orig ]; then
mv /etc/mtab /etc/mtab.orig
ln -s /proc/self/mounts /etc/mtab
fi

cat <<EOT1 > /usr/bin/rpi-rw
#!/bin/sh
mount -o remount,rw /dev/mmcblk0p2  /
echo "Filesystem is unlocked - Write access"
echo "type ' rpi-ro ' to lock"
EOT1

cat <<EOT2 > /usr/bin/rpi-ro
#!/bin/sh
sudo mount -o remount,ro /dev/mmcblk0p2  /
echo "Filesystem is locked - Read Only access"
echo "type ' rpi-rw ' to unlock"
EOT2

chmod +x  /usr/bin/rpi-rw
chmod +x  /usr/bin/rpi-ro

mkdir /usr/share/solar
mkdir /usr/lib/cgi-bin

#######################################################
echo "change /etc/init.d/apache2 to create log dir"
if [ ! -e /etc/init.d/apache2.orig ] ; then
cp /etc/init.d/apache2 /etc/init.d/apache2.orig)
perl -p -e "s/start\)\n/start)\nmkdir /var/log/apache2" < /etc/init.d/apache2.orig > /etc/init.d/apache2
fi

#######################################################
echo "setting up monitoring of solar"

cp monitor_solar.sh /etc/init.d/monitor_solar
chmod 755 /etc/init.d/monitor_solar
cp monitor_solar.py /usr/share/solar/monitor_solar.py
chmod u+x /etc/init.d/monitor_solar

#######################################################
echo "setting up monitoring of weather"

cp monitor_weather.sh /etc/init.d/monitor_weather
chmod 755 /etc/init.d/monitor_weather
cp monitor_weather.py /usr/share/solar/monitor_weather.py
chmod u+x /etc/init.d/monitor_weather

#######################################################
echo "setting up monitoring of temperature"
cp monitor_temperature.sh /etc/init.d/monitor_temperature
chmod 755 /etc/init.d/monitor_temperature
cp monitor_temperature.py /usr/share/solar/monitor_temperature.py
chmod u+x /etc/init.d/monitor_temperature

#######################################################
echo "setting up web services"
cp *web.py Utils.py /usr/lib/cgi-bin/
cp Utils.py /usr/share/solar/Utils.py
chown -R www-data:www-data /usr/lib/cgi-bin/*.py /mnt/ramdisk
cp images/*.png /mnt/ramdisk

# The following needs to be done to activate the various services
# depending on which machine we are on:
#
# update-rc.d monitor_weather defaults 80
# update-rc.d monitor_temperature defaults 80
# update-rc.d monitor_solar defaults 80
# sudo rename 's/S01/S90/' /etc/rc*.d/S*monito*

##########################################################
# Turned off because of RO
#
echo "Setting up ramdisk backup"
mkdir /var/ramdisk-backup
mv ramdisk_backup.sh /etc/init.d/ramdisk
chmod 755 /etc/init.d/ramdisk
chown root:root /etc/init.d/ramdisk

update-rc.d ramdisk defaults 00 99
 
echo "# setting up daily ramdisk backup"
echo "@daily  /etc/init.d/ramdisk sync >> /dev/null 2>&1" | crontab

# If apache does not start up, 
# make sure /var/log/apache2 exists

