#!/bin/bash -l

# Set the TERM environment variable
export TERM=xterm

module load rclone

# Define logs
mkdir -p $BACKUP/logs
LOG=$BACKUP/rclone.log
CRONLOG=$BACKUP/cron.log

LG24=$COMMON/lin-group24


function rclone-sync() {
    # Perform rclone sync from argument 1 (local dir) to arg 2 (remote dir)

    echo "Syncing $1 to $2" >> $LOG

    # Create log file for each directory
    local filename=$(echo "$1" | tr '/' '_')
    local dir_log=$BACKUP/logs/$filename.log

    echo -e "\n--------------------------------------------------" >> $dir_log
    echo -e "Sync Start: `date`\n" >> $dir_log

    rclone -v --stats 900s --stats-file-name-length 0 --retries 5 --log-file $dir_log --max-size 50M --exclude-from $BACKUP/exclude.txt -l sync $1 $2

    echo -e "\nSync End: `date`" >> $dir_log
}


# Check if rclone is already running
if [[ $(pgrep -u $USER rclone) ]]; then
  echo "rclone already running. aborting..." >> $CRONLOG
  exit
fi

echo "---> Script Start: `date` <---" > $LOG

# loop through 'directories.txt' file containing the files to transfer
while read -r local remote; do
    eval rclone-sync "$local" "$remote"
done < $BACKUP/directories.txt

echo "---> Script End: `date` <---" >> $LOG
