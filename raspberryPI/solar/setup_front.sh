#!/bin/bash

echo "setting up: front-pi"
echo "front-pi" > /etc/hostname

echo "activating wattson monitoring"
# update-rc.d monitor_weather defaults 80
# update-rc.d monitor_temperature defaults 80
# update-rc.d monitor_solar defaults 80
update-rc.d monitor_wattson defaults 80
sudo rename 's/S01/S90/' /etc/rc*.d/S*monito*

echo "activating carbon-cache daemon"
update-rc.d carbon-cache defaults 80
