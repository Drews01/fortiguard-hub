# generate_dns_yesterday.py ← ALWAYS uses yesterday's log (super simple)
import pandas as pd
import re
from pathlib import Path
import json
from datetime import datetime, timedelta

BASE_FOLDER = Path(__file__).parent
RAW_LOG_FOLDER   = BASE_FOLDER / "Raw Logs"
OUTPUT_FOLDER    = BASE_FOLDER / "daily_reports"
OUTPUT_FOLDER.mkdir(exist_ok=True)


# Accept date argument (YYYY_MM_DD), else use yesterday
import sys
if len(sys.argv) > 1:
    try:
        target_date = datetime.strptime(sys.argv[1], "%Y_%m_%d")
    except Exception:
        print("Invalid date format. Use YYYY_MM_DD.")
        exit(1)
else:
    target_date = datetime.now() - timedelta(days=1)

date_str = target_date.strftime("%Y_%m_%d")      # 2025_12_08
date_dash = target_date.strftime("%Y-%m-%d")     # 2025-12-08
date_ymd = target_date.strftime("%Y%m%d")        # 20251208

# Try these filenames (most common first)
possible_files = [
    RAW_LOG_FOLDER / f"disk-dns-{date_str}.log",
    RAW_LOG_FOLDER / f"disk-dns-{date_str}",
    RAW_LOG_FOLDER / f"disk-dns-{date_dash}.log",
    RAW_LOG_FOLDER / f"dns-{date_str}.log",
    RAW_LOG_FOLDER / f"dns-all-{date_str}.log",
]

log_file = None
for p in possible_files:
    if p.exists():
        log_file = p
        break

if not log_file:
    print(f"ERROR: Log not found for {date_str}!")
    print(f"Looking for files like: disk-dns-{date_str}.log in Raw Logs folder")
    try:
        if sys.stdin and sys.stdin.isatty():
            input("Press Enter to exit...")
    except Exception:
        pass
    exit()

print(f"Found log: {log_file.name}")
print(f"Generating report for {target_date.strftime('%d %B %Y')}...\n")

# === Parse log (same as before) ===
def parse_line(line):
    line = line.strip()
    if not line or line.startswith('#'): return None
    matches = re.findall(r'(\w+)=(?:"([^"]*)"|(\S+))', line)
    if not matches: return None
    d = {}
    for k, q, u in matches:
        d[k] = q if q else u
    return d

logs = []
with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        p = parse_line(line)
        if p and p.get("subtype") == "dns":
            logs.append(p)

df = pd.DataFrame(logs)
df['datetime'] = pd.to_datetime(df.get('date', '') + ' ' + df.get('time', ''), errors='coerce')
df = df.dropna(subset=['datetime']).sort_values('datetime')

# Normalize fields
df['qname'] = df.get('qname', '').str.lower()
df['qtype'] = df.get('qtype', df.get('type', 'N/A'))
df['action'] = df.get('action', 'pass')
df['cat'] = df.get('cat', '0')
df['catdesc'] = df.get('catdesc', df.get('category', 'Unknown'))
# Destination IP: sometimes 'dstip', 'dst', 'destip'
df['destip'] = df.get('dstip', df.get('dst', df.get('destip', 'N/A')))

# Category mapping (common FortiGuard DNS categories)
cat_map = {
    "62": "Phishing", "63": "Malicious Websites", "64": "Newly Observed Domain",
    "65": "Newly Registered Domain", "66": "Dynamic DNS", "67": "Spam URLs",
    "68": "Gambling", "69": "Pornography"
}
df['category'] = df['cat'].map(cat_map).fillna("Other")

# Focus on notable threats where category is known or action is blocked/deny
notable = df[(df['category'] != 'Other') | (df['action'].isin(['blocked','block','deny']))].copy()

cat_counts = notable['category'].value_counts()
domain_counts = notable['qname'].value_counts().head(10)
top_src_ips = notable.get('srcip', pd.Series()).value_counts().head(10)

# Pie chart data (use json.dumps for safety)
import json
top8 = cat_counts.head(8)
pie_labels = json.dumps([f"{c}<br>{v:,}" for c, v in top8.items()])
pie_values = json.dumps([int(v) for v in top8.values])

# Output file with YESTERDAY's date
output_file = OUTPUT_FOLDER / f"DNS_Events_Report_{target_date.strftime('%Y%m%d')}.html"

html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>DNS Events - {target_date.strftime('%Y-%m-%d')}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial; margin:40px; background:#f8f9fa; }}
        .container {{ max-width:1500px; margin:auto; background:white; padding:30px; border-radius:10px; box-shadow:0 0 20px rgba(0,0,0,0.1); }}
        h1 {{ color:#e74c3c; text-align:center; }}
        .stats {{ background:#f0f2f5; padding:20px; border-radius:8px; }}
        table {{ width:100%; border-collapse:collapse; margin:25px 0; }}
        th, td {{ border:1px solid #ddd; padding:12px; text-align:left; }}
        th {{ background:#e74c3c; color:white; }}
        tr:nth-child(even) {{ background:#f9f9f9; }}
        .pie {{ width:400px; height:400px; margin:30px auto; }}
    </style>
</head>
<body>
<div class="container">
    <h1>DNS (Domain Name System) Events</h1>
    <p style="text-align:center; font-size:1.8em; color:#e74c3c;">
        {target_date.strftime('%A, %d %B %Y')} ← SELECTED DATE REPORT
    </p>
    <div class="stats">
        <b>Log File:</b> {log_file.name}<br>
        <b>Total Threat Events:</b> {len(df):,}<br>
        <b>Notable Malicious Events:</b> <span style="color:#e74c3c; font-size:1.5em;">{len(notable):,}</span>
    </div>

    <div style="display:flex; flex-wrap:wrap; gap:30px; justify-content:space-around;">
        <div>
            <h2>Top Categories</h2>
            <table><tr><th>Category</th><th>Count</th></tr>
            {''.join(f"<tr><td>{c}</td><td>{v:,}</td></tr>" for c,v in cat_counts.head(10).items())}
            </table>
        </div>

        <div class="pie"><canvas id="pie"></canvas></div>

        <div>
            <h2>Top 10 Malicious Domains</h2>
            <table><tr><th>FQDN</th><th>Action</th><th>Count</th></tr>
            {''.join(f"<tr><td>{d}</td><td>{notable[notable['qname']==d]['action'].iloc[0]}</td><td>{c:,}</td></tr>" 
                     for d,c in domain_counts.items())}
            </table>
        </div>
    </div>

    <h2 style="margin-top:50px;">Top Source IPs (Notable)</h2>
    <table>
        <tr><th>Source IP</th><th>Count</th></tr>
        {''.join(f"<tr><td>{ip}</td><td>{c:,}</td></tr>" for ip,c in top_src_ips.items())}
    </table>

    <h2 style="margin-top:50px; color:#c0392b;">Detailed DNS Events (Most Recent 200)</h2>
    <table style="font-size:0.92em; width:100%; table-layout:fixed; border-collapse:collapse;">
        <tr style="background:#e74c3c; color:white;">
            <th width="135">Date & Time</th>
            <th width="110">Source IP</th>
            <th width="110">Destination IP</th>
            <th width="260">Query Name (qname)</th>
            <th width="90">QType</th>
            <th width="120">Category</th>
            <th width="90">Action</th>
            <th width="120">Response</th>
        </tr>
        {''.join(
            f"<tr style='height:48px;'>"
            f"<td style='white-space:nowrap; line-height:1.2; vertical-align:top;'>"
            f"  <div><b>{row['datetime'].strftime('%d %b %Y')}</b></div>"
            f"  <div style='color:#7f8c8d; font-size:0.9em;'>{row['datetime'].strftime('%H:%M:%S')}</div>"
            f"</td>"
            f"<td style='font-family:consolas; vertical-align:top;'>{row.get('srcip','N/A')}</td>"
            f"<td style='font-family:consolas; vertical-align:top;'>{row.get('destip','N/A')}</td>"
            f"<td style='word-break:break-all; font-size:0.95em; vertical-align:top;' title='{row.get('qname','')}'>{row.get('qname','')[:60]}{'...' if len(str(row.get('qname',''))) > 60 else ''}</td>"
            f"<td style='vertical-align:top;'>{row.get('qtype','N/A')}</td>"
            f"<td style='vertical-align:top;'>{row.get('category','Other')}</td>"
            f"<td style='text-align:center; vertical-align:middle;'><span style='background:#c0392b; color:white; padding:4px 10px; border-radius:6px; font-weight:bold;'>{str(row.get('action','')).upper()}</span></td>"
            f"<td style='vertical-align:top;'>{row.get('rcode', row.get('response', ''))}</td>"
            f"</tr>"
            for _, row in notable.sort_values('datetime', ascending=False).head(200).iterrows()
        )}
    </table>

    <script>
        new Chart(document.getElementById('pie'), {{
            type: 'pie',
            data: {{ labels: {pie_labels}, datasets: [{{ data: {pie_values}, 
                backgroundColor: ['#e74c3c','#e67e22','#f1c40f','#27ae60','#3498db','#9b59b6','#1abc9c','#34495e'] }}] }},
            options: {{ responsive:true, plugins:{{legend:{{position:'right'}}}} }}
        }});
    </script>
</div>
</body>
</html>
"""

output_file.write_text(html, encoding='utf-8')
print("="*70)
print("DONE! DNS Report Generated")
print(f"→ File: {output_file.name}")
print(f"→ Date: {target_date.strftime('%d %B %Y')}")
print(f"→ Malicious events found: {len(notable):,}")
print("="*70)
try:
    if sys.stdin and sys.stdin.isatty():
        input("Press Enter to close...")
except Exception:
    pass