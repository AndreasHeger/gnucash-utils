#!/bin/bash

echo "setting up: mid-pi"
echo "front-pi" > /etc/hostname

echo "installing watson"

# (cd ./rrdwattsond-0.8; install.sh) 

echo "activating wattson monitoring"
# update-rc.d monitor_weather defaults 80
# update-rc.d monitor_temperature defaults 80
# update-rc.d monitor_solar defaults 80
update-rc.d monitor_wattson defaults 80
sudo rename 's/S01/S90/' /etc/rc*.d/S*monito*
