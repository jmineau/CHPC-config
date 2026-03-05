import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta
from pathlib import Path
import socket

# Define the file paths for the input data and the output image
gimli_dir = Path('~/public_html/gimli').expanduser()
csv_file = gimli_dir / 'usage.csv'
output_plot = gimli_dir / 'weekly_usage.png'
users_linkdir = Path('~/users').expanduser()

# Create a mapping from UID to name by reading symlinks in users directory
uid_to_name = {}
if users_linkdir.exists():
    for link_path in users_linkdir.iterdir():
        if link_path.is_symlink():
            target = link_path.readlink()
            # Extract UID from the target path (e.g., ../../u0790486 -> u0790486)
            uid = target.name
            if uid.startswith('u') and uid[1:].isdigit():
                uid_to_name[uid] = link_path.name

# Load the csv data and parse the timestamp column into datetime objects
df = pd.read_csv(csv_file, parse_dates=['Timestamp'])

# Round timestamps to nearest minute for cleaner grouping
df['Timestamp'] = df['Timestamp'].dt.round('min')

# Separate CHPC users from system users
df['UserType'] = df['User'].apply(lambda x: x if x.startswith('u') and len(x) > 1 and x[1].isdigit() else 'system')

# Calculate the exact cutoff time for seven days ago
one_week_ago = pd.Timestamp.now() - timedelta(days=7)

# Filter the dataframe to keep only the records within the past week
recent_df = df[df['Timestamp'] >= one_week_ago]

# Group system users together and take mean by timestamp and user type to avoid double counting
grouped_df = recent_df.groupby(['Timestamp', 'UserType'], as_index=False)['Memory_MB'].mean()

# Pivot the data so timestamps become the index and each user gets a column
pivot_df = grouped_df.pivot(index='Timestamp', columns='UserType', values='Memory_MB')

# Convert MB to GB
pivot_df = pivot_df / 1024

# Calculate total line (sum across all users at each timestamp)
total_usage = pivot_df.sum(axis=1)

# Separate system from CHPC users for proper ordering
system_col = None
if 'system' in pivot_df.columns:
    system_col = pivot_df['system'].copy()
    pivot_df = pivot_df.drop('system', axis=1)

# Rename CHPC user columns from UIDs to names where mapping exists
pivot_df.columns = [uid_to_name.get(uid, uid) for uid in pivot_df.columns]

# Initialize the plot figure with a wide aspect ratio
fig = plt.figure(figsize=(12, 6))

# Plot CHPC users with labels
for col in pivot_df.columns:
    plt.plot(pivot_df.index, pivot_df[col], alpha=0.7, label=col, linewidth=2.5)

# Plot system if it exists
if system_col is not None:
    plt.plot(system_col.index, system_col.values, label='system', linestyle=':', linewidth=3, alpha=0.7)

# Plot total usage as bold black line
plt.plot(total_usage.index, total_usage.values, color='black', linewidth=4, label='Total')

# Get total system RAM and plot as a horizontal line
with open('/proc/meminfo', 'r') as f:
    for line in f:
        if line.startswith('MemTotal'):
            # Extract memory in kB and convert to GB
            total_ram_kb = int(line.split()[1])
            total_ram_gb = total_ram_kb / (1024 * 1024)
            break
plt.axhline(y=total_ram_gb, color='red', linestyle='--', linewidth=3, zorder=10)

# Add text annotation on the red line
plt.text(pivot_df.index[0], total_ram_gb, f'  Total RAM: {total_ram_gb:.1f} GB', 
         verticalalignment='bottom', color='red', fontsize=14, fontweight='bold')

# Set y-axis limit to add space above the total RAM line
plt.ylim(0, max(total_ram_gb, total_usage.max()) * 1.1)

# Add descriptive titles and labels to the axes
hostname = socket.gethostname()
plt.suptitle(f'{hostname} RSS Memory Usage (Past Week)', fontsize=18, fontweight='bold')
plt.title('RSS (Resident Set Size): Memory held in RAM,\nincluding shared memory (may count same memory multiple times)',
          fontsize=14, color='grey', pad=10)
plt.ylabel('Memory Usage (GB)', fontsize=18)

# Add a legend outside the main plot area so it does not cover the data lines
plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=14)

# Add a subtle grid to make the values easier to read across the chart
plt.grid(True, linestyle='--', alpha=0.7, linewidth=0.8)

# Adjust tick label sizes
plt.tick_params(axis='both', which='major', labelsize=14)

fig.autofmt_xdate()  # Auto-format x-axis labels for better readability

# Adjust the layout so the legend is not cut off in the final image
plt.tight_layout()

# Save the generated figure to the current directory
plt.savefig(output_plot, dpi=300)

# Print a confirmation message to the terminal
print(f"Success! Plot saved to {output_plot}")