# Copyright (c) 2013- Andreas Heger
# All rights reserved.
#
# Author: Andreas Heger, 2013
#
# Please send feedback to 
#
# 
#
# /etc/init.d/ramdisk
#
### BEGIN INIT INFO
# Provides: ramdisk
# Required-Start: 
# Should-Start:
# Required-Stop:
# Should-Stop:
# Default-Start:  2 3 4 5
# Default-Stop:   0 1 6
# Short-Description: ramdisk mirroring at startup
# Description:    mirrors ramdisk contents at startup and shutdown
### END INIT INFO

case "$1" in
  start)
    echo "Copying files to ramdisk"
    rsync -av /var/ramdisk-backup/ /mnt/ramdisk/
    echo [`date +"%Y-%m-%d %H:%M"`] Ramdisk Synched from HD >> /var/log/ramdisk_sync.log
    ;;
  sync)
    echo "Synching files from ramdisk to Harddisk"
    /usr/bin/rpi-rw
    echo [`date +"%Y-%m-%d %H:%M"`] Ramdisk Synched to HD >> /var/log/ramdisk_sync.log
    rsync -av --delete --recursive --force /mnt/ramdisk/ /var/ramdisk-backup/
    /usr/bin/rpi-ro
    ;;
  stop)
    echo "Synching logfiles from ramdisk to Harddisk"
    /usr/bin/rpi-rw
    echo [`date +"%Y-%m-%d %H:%M"`] Ramdisk Synched to HD >> /var/log/ramdisk_sync.log
    rsync -av --delete --recursive --force /mnt/ramdisk/ /var/ramdisk-backup/
    /usr/bin/rpi-ro
    ;;
  *)
    echo "Usage: /etc/init.d/ramdisk {start|stop|sync}"
    exit 1
    ;;
esac

exit 0
