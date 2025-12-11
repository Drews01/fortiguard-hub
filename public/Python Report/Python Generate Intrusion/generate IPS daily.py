# generate_ips_yesterday.py ← FortiGate IPS Critical Events Report (YESTERDAY)

import sys
import pandas as pd
import re
from pathlib import Path
from datetime import datetime, timedelta

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

    # Fallback: any file with the date + "ips"
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

def create_table(df, title, columns=None, top_n=10):
    if df.empty:
        return f"<h2>{title}</h2><p>No data available.</p>"
    if columns:
        df = df[columns]
    df = df.head(top_n)
    return f"<h2>{title}</h2>" + df.to_html(index=False, border=0, classes="table")


def main():
    # Accept date argument (YYYY_MM_DD), else use yesterday
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
        log_error(f"IPS log not found for {report_date.strftime('%Y_%m_%d')}!\nLooking for: disk-ips-{report_date.strftime('%Y_%m_%d')}.log")
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
        log_error("No IPS events found!")
        input("Press Enter...")
        return

    df = pd.DataFrame(logs)
    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], errors='coerce')
    df = df.dropna(subset=['datetime']).sort_values('datetime')

    # Critical severity only (high + critical)
    critical = df[df['severity'].isin(['high', 'critical'])].copy()

    # Safe field access
    critical['attack'] = critical.get('attack', 'Unknown Attack')
    critical['action'] = critical.get('action', 'unknown')
    critical['srcip'] = critical.get('srcip', 'Unknown')
    critical['dstip'] = critical.get('dstip', 'Unknown')
    critical['srccountry'] = critical.get('srccountry', 'Unknown')
    critical['service'] = critical.get('service', '-')
    critical['msg'] = critical.get('msg', '-')

    total_critical = len(critical)

    # Top 10 Critical Attacks with Source & Destination IPs
    top_attacks = critical['attack'].value_counts().head(10)
    top_attack_details = critical.groupby('attack').apply(lambda x: x.head(1)).set_index('attack').loc[top_attacks.index]

    # Prepare detailed table
    detail_table = critical[['attack', 'action', 'srcip', 'srccountry', 'dstip', 'service', 'msg']].copy()
    detail_table['count'] = critical.groupby('attack')['attack'].transform('count')
    detail_table = detail_table.drop_duplicates('attack').set_index('attack').loc[top_attacks.index].reset_index()

    report_file = OUTPUT_FOLDER / f"IPS_Critical_Events_{report_date:%Y%m%d}.html"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>FortiGate IPS Critical Events - {report_date:%Y-%m-%d}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f8f9fa; }}
            .container {{ max-width: 1500px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
            h1 {{ color: #e74c3c; text-align: center; }}
            h2 {{ color: #c0392b; border-bottom: 3px solid #eee; padding-bottom: 10px; }}
            .stats {{ background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; padding: 30px; border-radius: 12px; text-align: center; font-size: 1.5em; }}
            .stats span {{ font-size: 3em; font-weight: bold; display: block; margin: 10px 0; }}
            .table {{ width: 100%; border-collapse: collapse; margin: 25px 0; font-size: 0.95em; }}
            .table th, .table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            .table th {{ background-color: #e74c3c; color: white; text-align: center !important; }}
            .table tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .highlight {{ background-color: #fff5f5 !important; font-weight: bold; }}
            footer {{ text-align: center; margin-top: 60px; color: #7f8c8d; }}
        </style>
    </head>
    <body>
    <div class="container">
        <h1>IPS (Intrusion Prevention System) Events</h1>
        <p style="text-align:center; font-size:1.3em;">
            FortiGate UTM has IPS (Intrusion Prevention System) which detects then prevents attacks by analysing packets of data, 
            looking for patterns known to exist in threats, and stops the attack once recognized.
        </p>
        <p style="text-align:center; font-size:2em; color:#e74c3c; font-weight:bold;">
            {report_date.strftime('%A, %d %B %Y')} ← SELECTED DATE REPORT
        </p>

        <div class="stats">
            <span>{total_critical:,}</span>
            Total Critical IPS Events in 24 hours
        </div>

        <div style="display:flex; flex-wrap:wrap; gap:30px; margin-top:40px;">
            <div style="flex:2;">
                <h2>Top 10 Critical Attacks</h2>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Attack Name</th>
                            <th>Action</th>
                            <th>Count</th>
                            <th>Source IP</th>
                            <th>Country</th>
                            <th>Target IP</th>
                            <th>Service</th>
                        </tr>
                    </thead>
                    <tbody>
                    {
                        ''.join(
                            f"<tr class='highlight'>" +
                            f"<td><strong>{row['attack']}</strong></td>" +
                            f"<td>{row['action'].title()}</td>" +
                            f"<td><strong>{int(top_attacks[row['attack']]):,}</strong></td>" +
                            f"<td>{row['srcip']}</td>" +
                            f"<td>{row['srccountry']}</td>" +
                            f"<td>{row['dstip']}</td>" +
                            f"<td>{row['service']}</td>" +
                            f"</tr>"
                            for _, row in detail_table.iterrows()
                        )
                    }
                    </tbody>
                </table>
            </div>
        </div>

        <h2>All Critical IPS Events (Latest First)</h2>
        {
            critical[['datetime', 'attack', 'action', 'srcip', 'srccountry', 'dstip', 'service', 'msg']]
            .sort_values('datetime', ascending=False)
            .to_html(index=False, border=0, classes="table")
        }

        <footer>
            FortiGate IPS Critical Events Report • Generated on {datetime.now():%Y-%m-%d %H:%M} • Source: {log_file.name}
        </footer>
    </div>
    </body>
    </html>
    """

    report_file.write_text(html, encoding='utf-8')
    print("="*80)
    print("SUCCESS! IPS Critical Events Report Generated")
    print(f"→ Date        : {report_date.strftime('%d %B %Y')}")
    print(f"→ Total Events: {total_critical:,}")
    print(f"→ Saved as    : {report_file.name}")
    print("="*80)
    try:
        if sys.stdin and sys.stdin.isatty():
            input("\nPress Enter to close...")
    except Exception:
        pass

if __name__ == "__main__":
    main()