# generate_ips_yesterday.py ← FortiGate IPS Critical Events Report (YESTERDAY) – CLEAN VERSION

import sys
import pandas as pd
import re
from pathlib import Path
from datetime import datetime, timedelta
import json

BASE_FOLDER = Path(__file__).parent
RAW_LOG_FOLDER   = BASE_FOLDER / "Raw Logs"
OUTPUT_FOLDER    = BASE_FOLDER / "daily_reports"
ERROR_FOLDER     = BASE_FOLDER / "error_logs"

RAW_LOG_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)
ERROR_FOLDER.mkdir(exist_ok=True)

RAW_PATTERN = re.compile(r'(\w+)=(?:"([^"]*)"|(\S+))')

def find_log_for_date(target_date):
    y_str = target_date.strftime("%Y_%m_%d")
    y_ymd = target_date.strftime("%Y%m%d")

    candidates = [
        f"disk-ips-{y_str}",
        f"disk-ips-{y_ymd}",
        f"ips-{y_str}",
        f"ips-all-{y_str}",
        f"utm-ips-{y_str}",
    ]

    for name in candidates:
        for ext in [".log", ".txt", ""]:
            path = RAW_LOG_FOLDER / (name + ext)
            if path.exists():
                print(f"Found IPS log: {path.name}")
                return path, target_date

    # Fallback search
    for p in RAW_LOG_FOLDER.iterdir():
        if p.is_file() and y_str in p.name and "ips" in p.name.lower():
            print(f"Found by pattern: {p.name}")
            return p, target_date

    return None, target_date

def log_error(message):
    err_file = ERROR_FOLDER / f"ERROR_IPS_{datetime.now():%Y%m%d}.txt"
    with open(err_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}\n")
    print(f"\nERROR → {message}")

def parse_raw_line(line):
    line = line.strip()
    if not line or line.startswith('#'): return None
    matches = RAW_PATTERN.findall(line)
    if not matches: return None
    result = {}
    for key, quoted, unquoted in matches:
        result[key] = quoted if quoted else unquoted
    return result

def main():
    if len(sys.argv) > 1:
        try:
            report_date = datetime.strptime(sys.argv[1], "%Y_%m_%d")
        except Exception:
            print("Invalid date format. Use YYYY_MM_DD.")
            return
    else:
        report_date = datetime.now() - timedelta(days=1)

    log_file, _ = find_log_for_date(report_date)
    if not log_file:
        log_error(f"IPS log not found for {report_date.strftime('%Y_%m_%d')}!")
        input("\nPress Enter to exit...")
        return

    print(f"Processing IPS events for: {report_date.strftime('%d %B %Y')}\n")

    logs = []
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parsed = parse_raw_line(line)
            if parsed and parsed.get("subtype") == "ips" and parsed.get("eventtype") == "signature":
                logs.append(parsed)

    if not logs:
        log_error("No IPS events found in the log!")
        input("Press Enter...")
        return

    df = pd.DataFrame(logs)
    df['datetime'] = pd.to_datetime(df.get('date','') + ' ' + df.get('time',''), errors='coerce')
    df = df.dropna(subset=['datetime']).sort_values('datetime')

    # Normalize fields
    df['severity'] = df.get('severity', '').str.lower()
    df['action']   = df.get('action', '').str.lower()
    df['attack']   = df.get('attack', df.get('msg', 'Unknown Attack'))
    df['srcip']    = df.get('srcip', 'Unknown')
    df['dstip']    = df.get('dstip', df.get('dst', df.get('destip', 'N/A')))
    df['srccountry'] = df.get('srccountry', 'Unknown')
    df['service']  = df.get('service', '-')
    df['msg']      = df.get('msg', '-')

    # Critical events only
    critical = df[
        (df['severity'].isin(['high', 'critical'])) |
        (df['action'].isin(['blocked', 'block', 'deny']))
    ].copy()

    total_critical = len(critical)

    # Top 10 attacks
    top_attacks = critical['attack'].value_counts().head(10)

    # Pie chart data
    top8 = top_attacks.head(8)
    pie_labels = json.dumps([f"{a}<br>{c:,}" for a, c in top8.items()])
    pie_values = json.dumps([int(v) for v in top8.values])

    report_file = OUTPUT_FOLDER / f"IPS_Critical_Events_{report_date:%Y%m%d}.html"

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>FortiGate IPS Critical Events - {report_date:%Y-%m-%d}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin:40px; background:#f8f9fa; }}
        .container {{ max-width:1600px; margin:auto; background:white; padding:30px; border-radius:10px; box-shadow:0 0 20px rgba(0,0,0,0.1); }}
        h1 {{ color:#e74c3c; text-align:center; }}
        h2 {{ color:#c0392b; margin-top:40px; }}
        .stats {{ background:linear-gradient(135deg,#e74c,#c0392b); color:white; padding:25px; border-radius:12px; text-align:center; font-size:1.4em; }}
        .stats span {{ font-size:3.5em; font-weight:bold; display:block; }}
        table {{ width:100%; border-collapse:collapse; margin:25px 0; font-size:0.94em; table-layout:fixed; }}
        th, td {{ border:1px solid #ddd; padding:10px; text-align:left; vertical-align:top; }}
        th {{ background:#e74c3c; color:white; }}
        tr:nth-child(even) {{ background:#f9f9f9; }}
        .blocked {{ background:#c0392b; color:white; padding:5px 12px; border-radius:6px; font-weight:bold; }}
    </style>
</head>
<body>
<div class="container">
    <h1>IPS Critical & Blocked Events Report</h1>
    <p style="text-align:center; font-size:2em; color:#e74c3c; margin:20px 0;">
        {report_date.strftime('%A, %d %B %Y')}
    </p>

    <div class="stats">
        <span>{total_critical:,}</span>
        Critical / Blocked IPS Events (24h)
    </div>

    <div style="display:flex; flex-wrap:wrap; gap:30px; margin-top:40px;">
        <div style="flex:1; min-width:600px;">
            <h2>Top 10 Attacks</h2>
            <table>
                <tr><th>Rank</th><th>Attack Name</th><th>Count</th><th>Action</th><th>Source IP Example</th></tr>
                {''.join(
                    f"<tr><td><strong>{i+1}</strong></td>"
                    f"<td style='word-break:break-all;'>{attack}</td>"
                    f"<td><strong>{count:,}</strong></td>"
                    f"<td class='blocked'>{critical[critical['attack']==attack]['action'].iloc[0].upper()}</td>"
                    f"<td>{critical[critical['attack']==attack]['srcip'].iloc[0]}</td></tr>"
                    for i, (attack, count) in enumerate(top_attacks.items())
                )}
            </table>
        </div>

        <div style="width:420px;">
            <h2>Attack Distribution</h2>
            <canvas id="ipsPie" width="400" height="400"></canvas>
        </div>
    </div>

    <h2>Detailed Events (Most Recent 200)</h2>
    <table>
        <thead>
            <tr style="background:#e74c3c; color:white;">
                <th width="135">Date & Time</th>
                <th width="110">Source IP</th>
                <th width="110">Dest IP</th>
                <th width="380">Attack / Signature</th>
                <th width="90">Action</th>
                <th width="100">Service</th>
                <th>Message</th>
            </tr>
        </thead>
        <tbody>
        {''.join(
            f"<tr>"
            f"<td style='white-space:nowrap;'><b>{row['datetime'].strftime('%d %b %Y')}</b><br>"
            f"<span style='color:#7f8c8d;'>{row['datetime'].strftime('%H:%M:%S')}</span></td>"
            f"<td style='font-family:consolas;'>{row.get('srcip','N/A')}</td>"
            f"<td style='font-family:consolas;'>{row.get('dstip','N/A')}</td>"
            f"<td style='word-break:break-all;'>{row.get('attack','')[:70]}{'...' if len(str(row.get('attack',''))) > 70 else ''}</td>"
            f"<td style='text-align:center;'><span class='blocked'>{str(row.get('action','')).upper()}</span></td>"
            f"<td>{row.get('service','-')}</td>"
            f"<td style='font-size:0.9em;'>{row.get('msg','')[:100]}{'...' if len(str(row.get('msg',''))) > 100 else ''}</td>"
            f"</tr>"
            for _, row in critical.sort_values('datetime', ascending=False).head(200).iterrows()
        )}
        </tbody>
    </table>

    <script>
        new Chart(document.getElementById('ipsPie'), {{
            type: 'pie',
            data: {{ 
                labels: {pie_labels},
                datasets: [{{ data: {pie_values}, 
                    backgroundColor: ['#e74c3c','#c0392b','#e67e22','#d35400','#f39c12','#e91e63','#9b59b6','#8e44ad'] }}]
            }},
            options: {{ responsive: true, plugins: {{ legend: {{ position: 'right' }} }} }}
        }});
    </script>

    <div style="text-align:center; margin-top:60px; color:#7f8c8d;">
        Generated on {datetime.now():%Y-%m-%d %H:%M} • Log: {log_file.name}
    </div>
</div>
</body>
</html>"""

    report_file.write_text(html, encoding='utf-8')
    print("="*80)
    print("SUCCESS! IPS Report Generated!")
    print(f"→ Date         : {report_date.strftime('%d %B %Y')}")
    print(f"→ Events       : {total_critical:,}")
    print(f"→ File         : {report_file.name}")
    print("="*80)

    try:
        if sys.stdin.isatty():
            input("\nPress Enter to close...")
    except:
        pass

if __name__ == "__main__":
    main()