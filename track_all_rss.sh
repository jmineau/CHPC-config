#!/bin/bash

# Define the destination for the CSV log file
LOGFILE="$HOME/public_html/gimli/usage.csv"

# Check if the file exists and add a header row if it is missing
if [ ! -f "$LOGFILE" ]; then
    echo "Timestamp,User,Memory_MB" > "$LOGFILE"
fi

# Store the current time to use in every row
CURRENT_TIME=$(date '+%Y-%m-%d %H:%M:%S')

# Fetch user and RSS columns from all running processes
# Skip the header row using awk
# Accumulate the RSS values per user
# Print the timestamp, user, and converted memory as comma-separated values
# Sort the results by memory usage in descending order and append to the log
ps -eo user,rss | awk -v ts="$CURRENT_TIME" '
    NR>1 {sum[$1]+=$2} 
    END {
        for (user in sum) {
            printf "%s,%s,%.2f\n", ts, user, sum[user]/1024
        }
    }' | sort -t, -nr -k3 >> "$LOGFILE"


$HOME/software/python/miniforge3/envs/Main/bin/python $HOME/.chpc-config/plot_memory.py