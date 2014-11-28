#!/bin/bash

echo "setting up: bottom-pi"
echo "bottom-pi" > /etc/hostname

echo "activating temperature monitoring"
# update-rc.d monitor_weather defaults 80
update-rc.d monitor_temperature defaults 80
# update-rc.d monitor_solar defaults 80
sudo rename 's/S01/S90/' /etc/rc*.d/S*monito*
