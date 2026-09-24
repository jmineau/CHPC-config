#!/bin/bash

# Define the destination for the CSV log files
LOGFILE="$HOME/public_html/gimli/usage.csv"
PROG_LOGFILE="$HOME/public_html/gimli/program_usage.csv"

# Check if the files exist and add header rows if missing
if [ ! -f "$LOGFILE" ]; then
    echo "Timestamp,User,Memory_MB" > "$LOGFILE"
fi
if [ ! -f "$PROG_LOGFILE" ]; then
    echo "Timestamp,Program,Memory_MB" > "$PROG_LOGFILE"
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

# Fetch comm (short process name) and RSS columns from all running processes
# Accumulate RSS values per program name and append to the program log
ps -eo comm,rss | awk -v ts="$CURRENT_TIME" '
    NR>1 {sum[$1]+=$2}
    END {
        for (prog in sum) {
            printf "%s,%s,%.2f\n", ts, prog, sum[prog]/1024
        }
    }' | sort -t, -nr -k3 >> "$PROG_LOGFILE"


$HOME/software/python/miniforge3/envs/Main/bin/python $HOME/.chpc-config/gimli/plot_memory.py
