# Commands to make a raspbian image RO.
# 
# See: http://openenergymonitor.org/emon/node/5331

apt-get remove --purge wolfram-engine triggerhappy
# Remove X-Server and related stuff:
apt-get remove --purge xserver-common lightdm
insserv -r x11-common

# auto-remove some X11 related libs
apt-get autoremove --purge

apt-get -y update
apt-get -y upgrade

cp /etc/default/rcS /etc/default/rcS.orig
sh -c "echo 'RAMTMP=yes' >> /etc/default/rcS"
mv /etc/fstab /etc/fstab.orig
sh -c "echo 'tmpfs           /tmp            tmpfs   nodev,nosuid,size=30M,mode=1777       0    0' >> /etc/fstab"
sh -c "echo 'tmpfs           /var/log        tmpfs   nodev,nosuid,size=30M,mode=1777       0    0' >> /etc/fstab"
sh -c "echo 'proc            /proc           proc    defaults                              0    0' >> /etc/fstab"
sh -c "echo '/dev/mmcblk0p1  /boot           vfat    defaults                              0    2' >> /etc/fstab"
sh -c "echo '/dev/mmcblk0p2  /               ext4    defaults,ro,noatime,errors=remount-ro 0    1' >> /etc/fstab"
sh -c "echo 'tmpfs           /mnt/ramdisk    tmpfs   defaults,size=200M                    0    0' >> /etc/fstab"

sh -c "echo ' ' >> /etc/fstab"
mv /etc/mtab /etc/mtab.orig
ln -s /proc/self/mounts /etc/mtab

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





