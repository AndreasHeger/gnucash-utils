#!/bin/bash

# Backup-script for graphite whisper databases.
# Uses flock to lock databases before saving via
# rsync

# Local dir
local_dir=/mnt/ramdisk/graphite/storage/whisper
backup_dir=/mnt/diskstation/graphite

# Note: rpcbind needs to running
echo "starting backup at `date`"

echo "mounting diskstation"
mount /mnt/diskstation

env LD_PRELOAD=/home/pi/flockit/libflockit.so FLOCKIT_FILE_PREFIX=${local_dir} rsync -rzt -i ${local_dir} ${backup_dir}

echo "unmounting diskstation"
umount /mnt/diskstation

echo "backup completed successfully"
