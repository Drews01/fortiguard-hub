# generate_daily_yesterday.py ← Always processes YESTERDAY's Web Filter log

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
    y_str = target_date.strftime("%Y_%m_%d")   # 2025_12_08
    y_ymd = target_date.strftime("%Y%m%d")     # 20251208

    candidates = [
        f"disk-webfilter-{y_str}",
        f"disk-webfilter-{y_ymd}",
        f"webfilter-{y_str}",
        f"webfilter-{y_ymd}",
        f"disk-webf-{y_str}",           # sometimes shortened
    ]

    for name in candidates:
        for ext in [".log", ".txt", ""]:
            path = RAW_LOG_FOLDER / (name + ext)
            if path.exists():
                print(f"Found log: {path.name}")
                return path, target_date

    # Fallback: any file containing the date
    for p in RAW_LOG_FOLDER.iterdir():
        if p.is_file() and y_str in p.name and "webfilter" in p.name.lower():
            print(f"Found by pattern: {p.name}")
            return p, target_date

    return None, target_date

def log_error(message):
    err_file = ERROR_FOLDER / f"ERROR_WEBFILTER_{datetime.now():%Y%m%d}.txt"
    with open(err_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}\n")
    print(f"\nERROR → {message}\n→ Logged to: {err_file}")

def parse_raw_line(line):
    line = line.strip()
    if not line or line.startswith('#'): return None
    matches = RAW_PATTERN.findall(line)
    if not matches: return None
    result = {}
    for key, quoted, unquoted in matches:
        result[key] = quoted if quoted else unquoted
    return result

def create_count_table(series, title, col1, col2, top_n=10):
    if series.empty:
        return f"<h2>{title}</h2><p>No data</p>"
    
    top = series.value_counts().head(top_n)
    df = pd.DataFrame({col1: top.index, col2: top.values})
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
        log_error(f"Web Filter log not found for {report_date.strftime('%Y_%m_%d')}!\nLooking for: disk-webfilter-{report_date.strftime('%Y_%m_%d')}.log")
        input("\nPress Enter to exit...")
        return

    print(f"Processing data for: {report_date.strftime('%d %B %Y')}")
    print(f"Log file: {log_file.name}\n")

    logs = []
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parsed = parse_raw_line(line)
            if parsed:
                logs.append(parsed)

    if not logs:
        log_error("No valid log entries found!")
        input("Press Enter...")
        return

    df = pd.DataFrame(logs)
    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], errors='coerce')
    df = df.dropna(subset=['datetime']).sort_values('datetime').reset_index(drop=True)

    # Blocked web requests
    blocked = df[
        (df['action'] == 'blocked') & 
        (df.get('subtype', '').str.contains('webfilter', na=False))
    ].copy()

    # Safe column access
    blocked['url'] = blocked.get('url', blocked.get('hostname', 'Unknown'))
    blocked['catdesc'] = blocked.get('catdesc', 'Uncategorized')
    blocked['srcip'] = blocked.get('srcip', 'Unknown')
    blocked['hostname'] = blocked.get('hostname', '-')
    blocked['msg'] = blocked.get('msg', '-')

    # Use selected date for filename
    report_file = OUTPUT_FOLDER / f"WebFilter_Blocked_{report_date:%Y%m%d}.html"

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Web Filter Block Report - {report_date:%Y-%m-%d}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; background: #f8f9fa; }}
            .container {{ max-width: 1400px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
            h1 {{ color: #e74c3c; text-align: center; }}
            h2 {{ color: #c0392b; }}
            .stats {{ background: #f0f2f5; padding: 20px; border-radius: 8px; margin: 20px 0; font-size: 1.1em; }}
            .table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            .table th, .table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            .table th {{ background-color: #e74c3c; color: white; text-align: center !important; }}
            .table tr:nth-child(even) {{ background-color: #f9f9f9; }}
            footer {{ text-align: center; margin-top: 60px; color: #7f8c8d; }}
        </style>
    </head>
    <body>
    <div class="container">
        <h1>FortiGate Web Filter Block Report</h1>
        <h2 style="text-align:center; color:#c0392b; font-size:1.8em;">
            {report_date.strftime('%A, %d %B %Y')} ← SELECTED DATE REPORT
        </h2>

        <div class="stats">
            <b>Source Log File:</b> {log_file.name}<br>
            <b>Report Date:</b> {report_date.strftime('%d %B %Y')}<br>
            <b>Total Logs Processed:</b> {len(df):,}<br>
            <b>Blocked Web Requests:</b> 
                <span style="color:#e74c3c; font-size:1.6em; font-weight:bold;">{len(blocked):,}</span>
        </div>
        <hr>

        {create_count_table(blocked['srcip'], "Top 10 Users Trying to Access Blocked Sites", "Source IP", "Attempts")}
        {create_count_table(blocked['url'], "Top 15 Blocked URLs", "URL", "Hits", 15)}
        {create_count_table(blocked['catdesc'], "Top Blocked Categories", "Category", "Count")}

        <h2>High-Risk Blocks (crlevel = high)</h2>
        {blocked[blocked.get('crlevel', '') == 'high'][['datetime','srcip','hostname','url','catdesc','msg']]
         .head(25).to_html(index=False, border=0, classes="table") if 'crlevel' in blocked.columns else "<p>No high-risk blocks today.</p>"}

        <h2>All Blocked Events (Latest First)</h2>
        {blocked[['datetime','srcip','hostname','url','catdesc','msg']]
         .sort_values('datetime', ascending=False)
         .to_html(index=False, border=0, classes="table")}

        <footer>
            FortiGate Web Filter Daily Report • Generated on {datetime.now():%Y-%m-%d %H:%M}
        </footer>
    </div>
    </body>
    </html>
    """

    report_file.write_text(html, encoding='utf-8')

    print("="*80)
    print("SUCCESS! Web Filter Report Generated")
    print(f"→ Report Date : {report_date.strftime('%d %B %Y')}")
    print(f"→ Saved as    : {report_file.name}")
    print(f"→ Blocked URLs: {len(blocked):,}")
    print("="*80)
    try:
        if sys.stdin and sys.stdin.isatty():
            input("\nPress Enter to close...")
    except Exception:
        pass

if __name__ == "__main__":
    main()