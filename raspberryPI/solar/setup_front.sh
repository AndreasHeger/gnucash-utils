#!/bin/bash

echo "setting up: mid-pi"
echo "front-pi" > /etc/hostname

echo "installing watson"

(cd ./rrdwatson-0.8; install.sh) 

echo "activating solar and temperature monitoring"
# update-rc.d monitor_weather defaults 80
# update-rc.d monitor_temperature defaults 80
# update-rc.d monitor_solar defaults 80
sudo rename 's/S01/S90/' /etc/rc*.d/S*monito*
