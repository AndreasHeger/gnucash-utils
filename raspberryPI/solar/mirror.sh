#! /bin/bash

echo "mirroring from monitoring stations"
python solar_mirror.py --config=mirror_mid-pi.ini mirror
python solar_mirror.py --config=mirror_top-pi.ini mirror
python solar_mirror.py --config=mirror_bottom-pi.ini mirror

echo "mounting diskstation"
mount /mnt/diskstation
if test -d /mnt/diskstation/solar; then
	echo "mirroring to diskstation"
	cp -a *.log /mnt/diskstation/solar/
	cp -a csvdb /mnt/diskstation/solar/ 
fi

echo "unmounting diskstation"
umount /mnt/diskstation

