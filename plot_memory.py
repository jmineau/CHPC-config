import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta
from pathlib import Path
import socket

gimli_dir = Path('~/public_html/gimli').expanduser()
users_linkdir = Path('~/users').expanduser()
output_plot = gimli_dir / 'weekly_usage.png'
TOP_N = 10

# UID -> display name mapping
uid_to_name = {}
if users_linkdir.exists():
    for link_path in users_linkdir.iterdir():
        if link_path.is_symlink():
            target = link_path.readlink()
            uid = target.name
            if uid.startswith('u') and uid[1:].isdigit():
                uid_to_name[uid] = link_path.name

# Shared constants
one_week_ago = pd.Timestamp.now() - timedelta(days=7)

with open('/proc/meminfo', 'r') as f:
    for line in f:
        if line.startswith('MemTotal'):
            total_ram_gb = int(line.split()[1]) / (1024 * 1024)
            break

hostname = socket.gethostname()

# --- Load and trim user data ---
user_csv = gimli_dir / 'usage.csv'
user_df = pd.read_csv(user_csv)
user_df['Timestamp'] = pd.to_datetime(user_df['Timestamp'], format='ISO8601', errors='coerce')
user_df['Timestamp'] = user_df['Timestamp'].dt.round('min')
user_df = user_df[user_df['Timestamp'] >= one_week_ago]
user_df.to_csv(user_csv, index=False)

user_df['UserType'] = user_df['User'].apply(
    lambda x: x if x.startswith('u') and len(x) > 1 and x[1].isdigit() else 'system'
)
user_grouped = user_df.groupby(['Timestamp', 'UserType'], as_index=False)['Memory_MB'].mean()
user_pivot = user_grouped.pivot(index='Timestamp', columns='UserType', values='Memory_MB') / 1024
user_total = user_pivot.sum(axis=1)
user_system = user_pivot.pop('system') if 'system' in user_pivot.columns else None
user_pivot.columns = [uid_to_name.get(uid, uid) for uid in user_pivot.columns]

# --- Load and trim program data ---
prog_csv = gimli_dir / 'program_usage.csv'
prog_df = pd.read_csv(prog_csv)
prog_df['Timestamp'] = pd.to_datetime(prog_df['Timestamp'], format='ISO8601', errors='coerce')
prog_df['Timestamp'] = prog_df['Timestamp'].dt.round('min')
prog_df = prog_df[prog_df['Timestamp'] >= one_week_ago]
prog_df.to_csv(prog_csv, index=False)

top_programs = prog_df.groupby('Program')['Memory_MB'].sum().nlargest(TOP_N).index
prog_df = prog_df.copy()
prog_df['Program'] = prog_df['Program'].where(prog_df['Program'].isin(top_programs), other='other')
prog_grouped = prog_df.groupby(['Timestamp', 'Program'], as_index=False)['Memory_MB'].mean()
prog_pivot = prog_grouped.pivot(index='Timestamp', columns='Program', values='Memory_MB') / 1024
prog_total = prog_pivot.sum(axis=1)
prog_other = prog_pivot.pop('other') if 'other' in prog_pivot.columns else None
prog_pivot = prog_pivot[prog_pivot.mean().sort_values(ascending=False).index]

# --- Helper ---
def add_ram_line(ax, total_ram_gb):
    ax.axhline(y=total_ram_gb, color='red', linestyle='--', linewidth=4, zorder=10)
    ax.text(0.01, total_ram_gb * 1.01, f'Total RAM: {total_ram_gb:.1f} GB',
            transform=ax.get_yaxis_transform(),
            verticalalignment='bottom', color='red', fontsize=17, fontweight='bold')

# --- Figure: 2 subplots sharing x-axis ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), sharex=True, layout='constrained')
fig.suptitle(f'{hostname} RSS Memory Usage (Past Week)', fontsize=24, fontweight='bold')

# User subplot
for col in user_pivot.columns:
    ax1.plot(user_pivot.index, user_pivot[col], alpha=0.7, label=col, linewidth=3)
if user_system is not None:
    ax1.plot(user_system.index, user_system.values, label='system', linestyle=':', linewidth=3, alpha=0.7)
ax1.plot(user_total.index, user_total.values, color='black', linewidth=5, label='Total')
add_ram_line(ax1, total_ram_gb)
ax1.set_ylim(0, max(total_ram_gb, user_total.max()) * 1.1)
ax1.set_ylabel('Memory Usage (GB)', fontsize=18)
ax1.set_title('By User  (RSS: may count shared memory multiple times)', fontsize=16, color='grey')
ax1.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=14)
ax1.grid(True, linestyle='--', alpha=0.7, linewidth=0.8)
ax1.tick_params(axis='both', which='major', labelsize=15)

# Program subplot
for col in prog_pivot.columns:
    ax2.plot(prog_pivot.index, prog_pivot[col], alpha=0.7, label=col, linewidth=3)
if prog_other is not None:
    ax2.plot(prog_other.index, prog_other.values, label='other', linestyle=':', linewidth=3, alpha=0.7)
ax2.plot(prog_total.index, prog_total.values, color='black', linewidth=5, label='Total')
add_ram_line(ax2, total_ram_gb)
ax2.set_ylim(0, max(total_ram_gb, prog_total.max()) * 1.1)
ax2.set_ylabel('Memory Usage (GB)', fontsize=18)
ax2.set_title(f'By Program  (Top {TOP_N}; remainder grouped as "other")', fontsize=16, color='grey')
ax2.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=14)
ax2.grid(True, linestyle='--', alpha=0.7, linewidth=0.8)
ax2.tick_params(axis='both', which='major', labelsize=15)

# Shared x-axis: one tick per day, rotated neatly
ax2.xaxis.set_major_locator(mdates.DayLocator())
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%a %d'))
for label in ax2.get_xticklabels():
    label.set_rotation(30)
    label.set_ha('right')
    label.set_fontsize(15)

plt.savefig(output_plot, dpi=300, bbox_inches='tight')
print(f"Success! Plot saved to {output_plot}")