# clean up the log directory
mount -o remount,rw /
for f in $(find . -name \*log); do > $f; done
cd /var_org/log
rm -f *.gz

reboot
