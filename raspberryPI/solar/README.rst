The scripts in these directory perform two tasks:

* monitoring the temperature across the house
* monitoring power generation from our roof PV system

The scripts are installed onto two raspberry PIs

================
Solar Monitoring 
================

Inverter: Samil 

Installation instructions
=========================

The following instructions assume that you are root.

1. Open a port in the firewall if active. Necessary to communicate
with the SAMIL inverter. The inverter communicates by default on
ports 1200 and 1300::

   vi /etc/sysconfig/iptables

Append rules (before any of the REJECT rules)::

   -A INPUT -m state --state NEW -m tcp -p tcp --dport 1200 -j ACCEPT
   -A INPUT -m state --state NEW -m udp -p udp --dport 1300 -j ACCEPT

Restart::

   /etc/init.d/iptables restart

Create memory disk::

   mkdir /mnt/ramdisk
   chmod 777 /mnt/ramdisk

Add the following to /etc/fstab::

   tmpfs           /mnt/ramdisk tmpfs      defaults,size=256M 0 0

Update software::

   apt-get install rrdtool python-rrdtool python-daemon

4. Install daemon script::

   mv monitor_solar /etc/init.d/monitor_solar
   mkdir /usr/share/solar
   mv monitor_solar.py /usr/share/solar/solar_monitor.py
   chmod u+x /etc/init.d/monitor_solar
   update-rc.d monitor_solar defaults 80   

5. Install web frontend. Install apache, php, etc::

   apt-get install ganglia-webfrontend
   chmod 775 solarweb.py
   mv solarweb.py /usr/lib/cgi-bin/
   ln -s /usr/lib/cgi-bin/solarweb.py /home/pi/solarweb.py
   chown -R www-data:www-data /usr/lib/cgi-bin/solarweb.py /mnt/ramdisk
   ln -s /mnt/ramdisk /var/www/images

6. Setup backups of rrd directories::

   mkdir /var/ramdisk-backup
   mv ramdisk_backup.sh /etc/init.d/ramdisk
   chmod 755 /etc/init.d/ramdisk
   chown root:root /etc/init.d/ramdisk

Activate at start::

   update-rc.d ramdisk defaults 00 99

Setup cronjob as root, every 5mins past midnight::

   echo "@daily  /etc/init.d/ramdisk sync >> /dev/null 2>&1" | sudo crontab

8. Install temperature monitoring system::

   mv monitor_temperature.sh /etc/init.d/monitor_temperature
   chmod 755 /etc/init.d/monitor_temperature
   update-rc.d monitor_weather defaults 80
   chmod 775 temperatureweb.py
   mv temperatureweb.py /usr/lib/cgi-bin/
   ln -s /usr/lib/cgi-bin/temperatureweb.py /home/pi/temperatureweb.py
   chown -R www-data:www-data /usr/lib/cgi-bin/temperatureweb.py /mnt/ramdisk

9. Install weather monitoring system::

   mv monitor_weather.sh /etc/init.d/monitor_weather
   chmod 755 /etc/init.d/monitor_weather
   mv monitor_weather.py /usr/share/solar/monitor_weather.py
   chmod u+x /etc/init.d/monitor_weather
   update-rc.d monitor_weather defaults 80

