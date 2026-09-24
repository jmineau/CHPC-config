import pandas as pd
from matplotlib import colors as mcolors
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from datetime import timedelta
from pathlib import Path
import socket

gimli_dir = Path('~/public_html/gimli').expanduser()
users_linkdir = Path('~/users').expanduser()
output_plot = gimli_dir / 'weekly_usage.json'
TOP_N = 10
MATPLOTLIB_TAB10 = [mcolors.to_hex(color) for color in plt.get_cmap('tab10').colors]

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
def axis_ceiling(series, total_ram_gb):
    series_max = series.max() if not series.empty else 0
    return max(total_ram_gb, series_max) * 1.1


TIME_FORMAT_STOPS = [
    dict(dtickrange=[None, 1000], value='%H:%M:%S.%L'),
    dict(dtickrange=[1000, 60 * 1000], value='%H:%M:%S'),
    dict(dtickrange=[60 * 1000, 60 * 60 * 1000], value='%H:%M'),
    dict(dtickrange=[60 * 60 * 1000, 24 * 60 * 60 * 1000], value='%a %H:%M'),
    dict(dtickrange=[24 * 60 * 60 * 1000, 7 * 24 * 60 * 60 * 1000], value='%a %d'),
    dict(dtickrange=[7 * 24 * 60 * 60 * 1000, 31 * 24 * 60 * 60 * 1000], value='%b %d'),
    dict(dtickrange=[31 * 24 * 60 * 60 * 1000, 365 * 24 * 60 * 60 * 1000], value='%b %Y'),
    dict(dtickrange=[365 * 24 * 60 * 60 * 1000, None], value='%Y'),
]


def add_ram_line(fig, row, total_ram_gb):
    fig.add_hline(
        y=total_ram_gb,
        line_color='#ff0000',
        line_dash='dash',
        line_width=3,
        row=row,
        col=1,
    )
    fig.add_annotation(
        x=0.01,
        y=total_ram_gb,
        xref='x domain',
        yref=f'y{row}',
        text=f'<b>Total RAM: {total_ram_gb:.1f} GB</b>',
        showarrow=False,
        xanchor='left',
        yanchor='bottom',
        yshift=6,
        font=dict(color='#ff0000', size=14),
        row=row,
        col=1,
    )


fig = make_subplots(
    rows=2,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.08,
    subplot_titles=(
        'By User (RSS may count shared memory multiple times)',
        f'By Program (Top {TOP_N}; remainder grouped as "other")',
    ),
)

for index, col in enumerate(user_pivot.columns):
    fig.add_trace(
        go.Scatter(
            x=user_pivot.index,
            y=user_pivot[col],
            mode='lines',
            name=col,
            legend='legend',
            line=dict(width=2.5, color=MATPLOTLIB_TAB10[index % len(MATPLOTLIB_TAB10)]),
            opacity=0.8,
            hovertemplate='%{fullData.name}<br>%{y:.2f} GB<extra></extra>',
        ),
        row=1,
        col=1,
    )

if user_system is not None:
    fig.add_trace(
        go.Scatter(
            x=user_system.index,
            y=user_system.values,
            mode='lines',
            name='system',
            legend='legend',
            line=dict(width=2.5, dash='dot', color=MATPLOTLIB_TAB10[len(user_pivot.columns) % len(MATPLOTLIB_TAB10)]),
            opacity=0.8,
            hovertemplate='%{fullData.name}<br>%{y:.2f} GB<extra></extra>',
        ),
        row=1,
        col=1,
    )

fig.add_trace(
    go.Scatter(
        x=user_total.index,
        y=user_total.values,
        mode='lines',
        name='Total',
        legend='legend',
        line=dict(color='#111111', width=4),
        hovertemplate='%{fullData.name}<br>%{y:.2f} GB<extra></extra>',
    ),
    row=1,
    col=1,
)

for index, col in enumerate(prog_pivot.columns):
    fig.add_trace(
        go.Scatter(
            x=prog_pivot.index,
            y=prog_pivot[col],
            mode='lines',
            name=col,
            legend='legend2',
            line=dict(width=2.5, color=MATPLOTLIB_TAB10[index % len(MATPLOTLIB_TAB10)]),
            opacity=0.8,
            hovertemplate='%{fullData.name}<br>%{y:.2f} GB<extra></extra>',
        ),
        row=2,
        col=1,
    )

if prog_other is not None:
    fig.add_trace(
        go.Scatter(
            x=prog_other.index,
            y=prog_other.values,
            mode='lines',
            name='other',
            legend='legend2',
            line=dict(width=2.5, dash='dot', color=MATPLOTLIB_TAB10[len(prog_pivot.columns) % len(MATPLOTLIB_TAB10)]),
            opacity=0.8,
            hovertemplate='%{fullData.name}<br>%{y:.2f} GB<extra></extra>',
        ),
        row=2,
        col=1,
    )

fig.add_trace(
    go.Scatter(
        x=prog_total.index,
        y=prog_total.values,
        mode='lines',
        name='Total',
        legend='legend2',
        line=dict(color='#111111', width=4),
        hovertemplate='%{fullData.name}<br>%{y:.2f} GB<extra></extra>',
    ),
    row=2,
    col=1,
)

add_ram_line(fig, 1, total_ram_gb)
add_ram_line(fig, 2, total_ram_gb)

for annotation in fig.layout.annotations:
    if annotation.text.startswith('By '):
        annotation.update(font=dict(color='#b8860b', size=15))

fig.update_layout(
    title=dict(text=f'{hostname} RSS Memory Usage (Past Week)', x=0.5, font=dict(size=24)),
    height=900,
    hovermode='x unified',
    plot_bgcolor='rgba(247, 237, 221, 0.96)',
    paper_bgcolor='rgba(0, 0, 0, 0)',
    font=dict(family='Arial, sans-serif', size=14, color='#f5deb3'),
    margin=dict(l=80, r=170, t=100, b=70),
    legend=dict(
        title=dict(text='Users'),
        orientation='v',
        yanchor='top',
        y=0.985,
        xanchor='left',
        x=1.005,
        bgcolor='rgba(42, 24, 16, 0.75)',
        bordercolor='#8B4513',
        borderwidth=1,
        itemclick='toggle',
        itemdoubleclick='toggleothers',
        font=dict(size=12),
        itemsizing='constant',
    ),
    legend2=dict(
        title=dict(text='Programs'),
        orientation='v',
        yanchor='top',
        y=0.44,
        xanchor='left',
        x=1.005,
        bgcolor='rgba(42, 24, 16, 0.75)',
        bordercolor='#8B4513',
        borderwidth=1,
        itemclick='toggle',
        itemdoubleclick='toggleothers',
        font=dict(size=12),
        itemsizing='constant',
    ),
)

fig.update_yaxes(
    title_text='Memory Usage (GB)',
    gridcolor='rgba(101, 67, 33, 0.18)',
    zerolinecolor='rgba(101, 67, 33, 0.25)',
    tickfont=dict(color='#f5deb3'),
    title_font=dict(color='#f5deb3'),
    row=1,
    col=1,
    range=[0, axis_ceiling(user_total, total_ram_gb)],
)
fig.update_yaxes(
    title_text='Memory Usage (GB)',
    gridcolor='rgba(101, 67, 33, 0.18)',
    zerolinecolor='rgba(101, 67, 33, 0.25)',
    tickfont=dict(color='#f5deb3'),
    title_font=dict(color='#f5deb3'),
    row=2,
    col=1,
    range=[0, axis_ceiling(prog_total, total_ram_gb)],
)
fig.update_xaxes(
    gridcolor='rgba(101, 67, 33, 0.12)',
    tickangle=30,
    tickfont=dict(color='#f5deb3'),
    tickformatstops=TIME_FORMAT_STOPS,
)

pio.write_json(fig, output_plot, pretty=False)
print(f"Success! Plot saved to {output_plot}")