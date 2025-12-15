# generate_av_yesterday.py
# FortiGate Antivirus (infected file) daily report – always uses yesterday's log

import pandas as pd
import re
from pathlib import Path
from datetime import datetime, timedelta
import sys
import json

BASE_FOLDER = Path(__file__).parent
RAW_LOG_FOLDER   = BASE_FOLDER / "Raw Logs"
OUTPUT_FOLDER    = BASE_FOLDER / "daily_reports"
OUTPUT_FOLDER.mkdir(exist_ok=True)

# Accept date argument (YYYY_MM_DD), else use yesterday
if len(sys.argv) > 1:
    try:
        target_date = datetime.strptime(sys.argv[1], "%Y_%m_%d")
    except Exception:
        print("Invalid date format. Use YYYY_MM_DD.")
        sys.exit(1)
else:
    target_date = datetime.now() - timedelta(days=1)

date_str   = target_date.strftime("%Y_%m_%d")   # 2025_12_10
date_dash  = target_date.strftime("%Y-%m-%d")   # 2025-12-10
date_ymd   = target_date.strftime("%Y%m%d")     # 20251210

# Most common filenames for AV logs (adjust if yours are different)
possible_files = [
    RAW_LOG_FOLDER / f"disk-antivirus-{date_str}.log",           # ← MAIN ONE YOU HAVE
    RAW_LOG_FOLDER / f"disk-antivirus-{date_dash}.log",          # in case someone uses dashes
    RAW_LOG_FOLDER / f"antivirus-{date_str}.log",
    RAW_LOG_FOLDER / f"av-{date_str}.log",
    RAW_LOG_FOLDER / f"disk-av-{date_str}.log",                  # old style fallback
    RAW_LOG_FOLDER / f"utm-virus-{date_str}.log",
]

log_file = None
for p in possible_files:
    if p.exists():
        log_file = p
        break

if not log_file:
    print(f"ERROR: Log not found for {date_str}!")
    print("Tried these filenames:")
    for p in possible_files:
        print(f"  - {p.name}")
    try:
        if sys.stdin.isatty():
            input("\nPress Enter to exit...")
    except:
        pass
    sys.exit(1)

print(f"Found log: {log_file.name}")
print(f"Generating AV report for {target_date.strftime('%d %B %Y')}...\n")

# === Parse FortiGate key="value" lines ===
def parse_line(line: str):
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    # Matches both "quoted" and unquoted values
    matches = re.findall(r'(\w+)=(?:"([^"]*)"|(\S+))', line)
    if not matches:
        return None
    d = {}
    for key, quoted_val, unquoted_val in matches:
        d[key] = quoted_val if quoted_val else unquoted_val
    return d

entries = []
with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        parsed = parse_line(line)
        if parsed and parsed.get("subtype") == "virus" and parsed.get("eventtype") == "infected":
            entries.append(parsed)

if not entries:
    print("No infected virus events found in the log.")
    sys.exit(0)

df = pd.DataFrame(entries)

# Create proper datetime
df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], errors='coerce')
df = df.dropna(subset=['datetime']).sort_values('datetime')

# === Critical fields (feel free to add/remove) ===
df['srcip']       = df.get('srcip', 'N/A')
df['user_agent']  = df.get('agent', 'N/A')
df['url']         = df.get('url', 'N/A')
df['filename']    = df.get('filename', 'N/A')
df['virus']       = df.get('virus', 'Unknown')
df['action']      = df.get('action', 'N/A')
df['crlevel']     = df.get('crlevel', 'low').str.lower()
df['level']       = df.get('level', 'info')
df['service']     = df.get('service', 'N/A')
df['profile']     = df.get('profile', 'N/A')
# Destination IP: FortiGate sometimes uses 'dstip' or 'dst' or 'destip'
df['destip']      = df.get('dstip', df.get('dst', df.get('destip', 'N/A')))

# Focus on blocked + critical/high events
critical_df = df[
    ((df['action'] == 'blocked') | (df['action'] == 'block')) &
    (df['crlevel'].isin(['critical', 'high']) | (df['level'] == 'warning'))
].copy()

print(f"Total virus events       : {len(df):,}")
print(f"Blocked & Critical/High events : {len(critical_df):,}")

# === Statistics ===
virus_counts     = critical_df['virus'].value_counts().head(10)
url_counts       = critical_df['url'].value_counts().head(10)
filename_counts  = critical_df['filename'].value_counts().head(10)
top_src_ips      = critical_df['srcip'].value_counts().head(10)  # clear name

# Pie chart – top 8 viruses
# === PIE CHART – FIXED & SAFE ===
# === PIE CHART – FINAL 100% WORKING FIX ===
top8_viruses = virus_counts.head(8)

virus_labels = [f"{virus}<br>{count:,}" for virus, count in top8_viruses.items()]
virus_values = [int(count) for count in top8_viruses.values]   # ← fixes int64 error

# This is the key: use json.dumps with safe types
pie_labels = json.dumps(virus_labels)
pie_values = json.dumps(virus_values)
# === Generate HTML report ===
output_file = OUTPUT_FOLDER / f"AV_Infected_Report_{target_date.strftime('%Y%m%d')}.html"

html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Antivirus Infected Files - {target_date.strftime('%Y-%m-%d')}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin:40px; background:#f8f9fa; }}
        .container {{ max-width:1600px; margin:auto; background:white; padding:30px; border-radius:10px; box-shadow:0 0 20px rgba(0,0,0,0.1); }}
        h1 {{ color:#e74c3c; text-align:center; }}
        h2 {{ color:#c0392b; }}
        .stats {{ background:#f0f2f5; padding:20px; border-radius:8px; margin:20px 0; }}
        table {{ width:100%; border-collapse:collapse; margin:25px 0; font-size:0.95em; }}
        th, td {{ border:1px solid #ddd; padding:10px; text-align:left; }}
        th {{ background:#e74c3c; color:white; }}
        tr:nth-child(even) {{ background:#f9f9f9; }}
        .pie {{ width:420px; height:420px; margin:30px auto; }}
        .flex {{ display:flex; flex-wrap:wrap; gap:30px; justify-content:space-around; }}
    </style>
</head>
<body>
<div class="container">
    <h1>Antivirus – Infected File Events (Blocked & Critical/High)</h1>
    <p style="text-align:center; font-size:1.9em; color:#e74c3c;">
        {target_date.strftime('%A, %d %B %Y')} ← REPORT DATE
    </p>

    <div class="stats">
        <b>Log File:</b> {log_file.name}<br>
        <b>Total Virus Events:</b> {len(df):,}<br>
        <b>Blocked & Critical/High Events:</b> 
            <span style="color:#e74c3c; font-size:1.6em;">{len(critical_df):,}</span>
    </div>

    <div class="flex">
        <!-- Top Viruses -->
        <div>
            <h2>Top 10 Detected Viruses / Malware</h2>
            <table>
                <tr><th>Virus / Malware Name</th><th>Count</th></tr>
                {''.join(f"<tr><td>{v}</td><td>{c:,}</td></tr>" for v,c in virus_counts.items())}
            </table>
        </div>

        <!-- Pie Chart -->
        <div class="pie">
            <canvas id="pieChart"></canvas>
        </div>

        <!-- Top URLs -->
        <div>
            <h2>Top 10 Infected URLs</h2>
            <table>
                <tr><th>URL</th><th>Count</th></tr>
                {''.join(f"<tr><td title='{u}'>{u[:80]}{'...' if len(u)>80 else ''}</td><td>{c:,}</td></tr>" for u,c in url_counts.items())}
            </table>
        </div>
    </div>

    <h2 style="margin-top:50px;">Top 10 Source IPs (Infected Attempts)</h2>
    <table>
        <tr><th>Source IP</th><th>Count</th></tr>
        {''.join(f"<tr><td>{ip}</td><td>{c:,}</td></tr>" for ip,c in top_src_ips.items())}
    </table>

    <h2 style="margin-top:60px; color:#c0392b;">Detailed Blocked & Critical Events (Most Recent 100)</h2>
    <table style="font-size:0.92em; width:100%; table-layout:fixed; border-collapse:collapse;">
        <tr style="background:#e74c3c; color:white;">
            <th width="135">Date & Time</th>
            <th width="110">Source IP</th>
            <th width="110">Destination IP</th>
            <th width="320">URL</th>
            <th width="140">Filename</th>
            <th width="200">Virus Name</th>
            <th width="90">Action</th>
            <th width="300">User-Agent</th>
        </tr>
        {''.join(
            f"<tr style='height:55px;'>"
            f"<td style='white-space:nowrap; line-height:1.4; vertical-align:top;'>"
            f"  <div><b>{row['datetime'].strftime('%d %b %Y')}</b></div>"
            f"  <div style='color:#7f8c8d; font-size:0.9em;'>{row['datetime'].strftime('%H:%M:%S')}</div>"
            f"</td>"
            f"<td style='font-family:consolas; vertical-align:top;'>{row['srcip']}</td>"
            f"<td style='font-family:consolas; vertical-align:top;'>{row['destip']}</td>"
            f"<td style='word-break:break-all; font-size:0.9em; vertical-align:top;' title='{row['url']}'>"
            f"  {row['url'][:80]}{'...' if len(row['url'])>80 else ''}"
            f"</td>"
            f"<td style='word-break:break-all; vertical-align:top;'>{row['filename']}</td>"
            f"<td style='word-break:break-all; font-size:0.9em; vertical-align:top;' title='{row['virus']}'>"
            f"  {row['virus'][:45]}{'...' if len(row['virus'])>45 else ''}"
            f"</td>"
            f"<td style='text-align:center; vertical-align:middle;'>"
            f"  <span style='background:#c0392b; color:white; padding:5px 12px; border-radius:6px; font-weight:bold;'>"
            f"    {row['action'].upper()}"
            f"  </span>"
            f"</td>"
            f"<td style='font-size:0.85em; color:#34495e; vertical-align:top;' title='{row['user_agent']}'>"
            f"  {row['user_agent'][:70]}{'...' if len(row['user_agent'])>70 else ''}"
            f"</td>"
            f"</tr>"
            for _, row in critical_df.sort_values('datetime', ascending=False).head(100).iterrows()
        )}
    </table>

    <script>
        // pie_labels and pie_values are already JSON arrays (e.g. ["A","B"]) so insert them directly
        new Chart(document.getElementById('pieChart'), {{
            type: 'pie',
            data: {{
                labels: {pie_labels},
                datasets: [{{
                    data: {pie_values},
                    backgroundColor: ['#e74c3c','#c0392b','#e67e22','#d35400','#f39c12','#e91e63','#9b59b6','#8e44ad']
                }}]
            }},
            options: {{ responsive: true, plugins: {{ legend: {{ position: 'right' }} }} }}
        }});
    </script>
</div>
</body>
</html>
"""

output_file.write_text(html, encoding='utf-8')

print("="*80)
print("AV REPORT GENERATED SUCCESSFULLY GENERATED!")
print(f"→ File : {output_file.name}")
print(f"→ Date : {target_date.strftime('%d %B %Y')}")
print(f"→ Blocked & Critical events : {len(critical_df):,}")
print("="*80)

try:
    if sys.stdin.isatty():
        input("Press Enter to close...")
except:
    pass