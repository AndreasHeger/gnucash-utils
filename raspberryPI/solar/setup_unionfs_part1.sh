# Install packages needed



# Instructions from http://blog.pi3g.com/2014/04/make-raspbian-system-read-only/
#
# run as sudo ./make_ro.sh

# Disable swap
dphys-swapfile swapoff
dphys-swapfile uninstall
update-rc.d dphys-swapfile disable

# Install Union FS
aptitude install unionfs-fuse

# Create Mount Script
cp mount_unionfs /usr/local/bin

chmod +x /usr/local/bin/mount_unionfs

cp fstab_unionfs /etc/fstab

# setup files
cp -al /etc /etc_org
mv /var /var_org
mkdir /etc_rw
mkdir /var /var_rw
reboot
