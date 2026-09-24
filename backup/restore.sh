#!/bin/bash l

module load rclone

SCRIPT_DIR="$HOME/.chpc-config/backup"

mkdir -p $BACKUP/logs
LOG=$BACKUP/logs/rclone-restore-`date +%F`.log

LG15=$COMMON/lin-group15

function rclone-restore() {
    echo "---> Restoring $1 to $2" >> $LOG
    rclone -v --stats 900s --stats-file-name-length 0 --retries 5 --log-file $LOG --exclude-from $SCRIPT_DIR/exclude.txt -1 sync $1 $2
}

echo "---> Script Start: `date` <---" > $LOG

while read -r local remote; do
    rclone-restore "$remote" "$local"
done < $SCRIPT_DIR/directories.txt

echo "---> Script End: `date` <---" >> $LOG
