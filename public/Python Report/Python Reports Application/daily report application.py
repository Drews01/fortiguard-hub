# generate_appctrl_yesterday.py ← Always uses YESTERDAY's Application Control log

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

# Regex to parse key="value" or key=value
RAW_PATTERN = re.compile(r'(\w+)=(?:"([^"]*)"|(\S+))')

def find_log_for_date(target_date):
    y_str = target_date.strftime("%Y_%m_%d")   # 2025_12_08
    y_ymd = target_date.strftime("%Y%m%d")     # 20251208

    candidates = [
        f"disk-appctrl-{y_str}",
        f"disk-appctrl-{y_ymd}",
        f"app-ctrl-all-{y_str}",
        f"app-ctrl-all-{y_ymd}",
        f"application-control-{y_str}",
    ]

    for name in candidates:
        for ext in [".log", ".txt", ""]:
            path = RAW_LOG_FOLDER / (name + ext)
            if path.exists():
                print(f"Found log: {path.name}")
                return path, target_date

    # Fallback: any file containing the date
    for p in RAW_LOG_FOLDER.iterdir():
        if p.is_file() and y_str in p.name:
            print(f"Found by date pattern: {p.name}")
            return p, target_date

    return None, target_date

def log_error(message):
    err_file = ERROR_FOLDER / f"ERROR_APPCTRL_{datetime.now():%Y%m%d}.txt"
    with open(err_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}\n")
    print(f"\nERROR → {message}\n→ Logged to: {err_file}")

def parse_raw_line(line):
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    matches = RAW_PATTERN.findall(line)
    if not matches:
        return None
    result = {}
    for key, quoted, unquoted in matches:
        value = quoted if quoted else unquoted
        result[key] = value
    return result

def create_count_table(series, title, col1, col2, top_n=10):
    if series.empty:
        return f"<h2>{title}</h2><p>No data available.</p>"
    top = series.value_counts().head(top_n)
    df = pd.DataFrame({col1: top.index, col2: top.values})
    return f"<h2>{title}</h2>" + df.to_html(index=False, border=0, classes="table table-striped")


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
    today = datetime.now()

    if not log_file:
        log_error(f"Application Control log not found for {report_date.strftime('%Y_%m_%d')}!\nLooking for files like: disk-appctrl-{report_date.strftime('%Y_%m_%d')}.log")
        input("\nPress Enter to exit...")
        return

    print(f"Generating Application Control Report for {report_date.strftime('%d %B %Y')}...\n")

    logs = []
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parsed = parse_raw_line(line)
            if parsed:
                logs.append(parsed)

    if not logs:
        log_error("No valid log lines found!")
        input("Press Enter to exit...")
        return

    df = pd.DataFrame(logs)
    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], errors='coerce')
    df = df.dropna(subset=['datetime']).sort_values('datetime').reset_index(drop=True)

    # Only blocked events
    blocked = df[
        (df['type'] == 'utm') &
        (df['subtype'] == 'app-ctrl') &
        (df['action'] == 'block')
    ].copy()

    blocked['app_safe'] = blocked.get('app', 'Unknown').fillna('Unknown')
    blocked['hostname_safe'] = blocked.get('hostname', blocked.get('dstip', 'No Hostname'))
    blocked['url_safe'] = blocked.get('url', '-')
    blocked['srcip'] = blocked.get('srcip', 'Unknown')
    blocked['apprisk'] = blocked.get('apprisk', 'unknown')

    # Use selected date for filename and title
    report_file = OUTPUT_FOLDER / f"AppCtrl_Blocked_{report_date:%Y%m%d}.html"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>FortiGate Application Control Block Report - {report_date:%Y-%m-%d}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; background: #f8f9fa; }}
            .container {{ max-width: 1400px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
            h1 {{ color: #9b59b6; text-align: center; }}
            h2 {{ color: #8e44ad; border-bottom: 2px solid #ddd; padding: 10px; border-radius: 5px; background: #f0e6ff; }}
            .stats {{ font-size: 1.1em; background: #f0f2f5; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            .table {{ width: 100%; border-collapse: collapse; margin: 25px 0; font-size: 0.95em; }}
            .table th, .table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            .table th {{ background-color: #9b59b6; color: white; text-align: center !important; }}
            .table tr:nth-child(even) {{ background-color: #f9f9f9; }}
            footer {{ text-align: center; margin-top: 50px; color: #7f8c8d; font-size: 0.9em; }}
        </style>
    </head>
    <body>
    <div class="container">
        <h1>FortiGate Application Control - Blocked Applications Report</h1>
        <p style="text-align:center; font-size:1.5em; color:#e74c3c; font-weight:bold;">
            {report_date.strftime('%A, %d %B %Y')} ← SELECTED DATE REPORT
        </p>

        <div class="stats">
            <b>Source Log File:</b> {log_file.name}<br>
            <b>Report Date:</b> {report_date.strftime('%d %B %Y')}<br>
            <b>Total Logs Processed:</b> {len(df):,}<br>
            <b>Blocked Application Events:</b> 
                <span style="color:#e74c3c; font-size:1.5em; font-weight:bold;">{len(blocked):,}</span>
        </div>
        <hr>

        {create_count_table(blocked['app_safe'], "Top 10 Blocked Applications", "Application", "Block Count")}
        {create_count_table(blocked['srcip'], "Top 10 Source IPs (Users/Devices)", "Source IP", "Attempts")}
        {create_count_table(blocked['hostname_safe'], "Top 10 Destination Hosts", "Hostname / IP", "Hits")}
        {create_count_table(blocked.get('appcat', pd.Series()), "Blocked by Application Category", "Category", "Count")}
        {create_count_table(blocked['apprisk'], "Blocks by Application Risk Level", "Risk Level", "Count")}

        <h2>High & Elevated Risk Blocked Applications</h2>
        <p>Only applications with <code>apprisk=high</code> or <code>elevated</code> are shown:</p>
        {
            blocked[blocked['apprisk'].isin(['high', 'elevated'])]
            [['datetime', 'srcip', 'app_safe', 'hostname_safe', 'url_safe', 'apprisk', 'msg']]
            .head(50)
            .to_html(index=False, border=0, classes="table")
        }

        <h2>All Blocked Events (Latest First)</h2>
        {
            blocked[['datetime', 'srcip', 'app_safe', 'hostname_safe', 'url_safe', 'apprisk', 'service', 'msg']]
            .sort_values('datetime', ascending=False)
            .to_html(index=False, border=0, classes="table")
        }

        <footer>
            FortiGate Application Control Daily Report • Generated on {today:%Y-%m-%d %H:%M}
        </footer>
    </div>
    </body>
    </html>
    """

    report_file.write_text(html_content, encoding='utf-8')
    print("="*80)
    print("SUCCESS! Application Control Report Generated")
    print(f"→ Report Date : {report_date.strftime('%d %B %Y')}")
    print(f"→ Saved as    : {report_file.name}")
    print(f"→ Blocked apps: {len(blocked):,}")
    print("="*80)
    try:
        if sys.stdin and sys.stdin.isatty():
            input("\nPress Enter to close...")
    except Exception:
        pass

if __name__ == "__main__":
    main()