# FortiGate_WebFilter_Daily_Report_SINGLE_FILE_PER_DAY.py
import pandas as pd
import re
from pathlib import Path
from datetime import datetime

# ================== CHANGE THIS PATH ONLY ==================
INPUT_FOLDER = Path(r"C:\Users\Andrew\Desktop\Python Generate Reports")   # ← Your folder
# ===========================================================

OUTPUT_FOLDER = INPUT_FOLDER / "daily_reports"
ERROR_FOLDER  = INPUT_FOLDER / "error_logs"
OUTPUT_FOLDER.mkdir(exist_ok=True)
ERROR_FOLDER.mkdir(exist_ok=True)

RAW_PATTERN = re.compile(r'(\w+)=(?:"([^"]*)"|(\S+))')

def find_todays_log():
    today_str = datetime.now().strftime("%Y_%m_%d")
    today_ymd = datetime.now().strftime("%Y%m%d")
    candidates = [
        f"disk-webfilter-{today_str}",
        f"disk-webfilter-{today_ymd}",
        f"webfilter-{today_str}",
    ]
    for name in candidates:
        for ext in ["", ".log", ".txt"]:
            path = INPUT_FOLDER / (name + ext)
            if path.exists():
                return path
    return None

def log_error(message):
    err_file = ERROR_FOLDER / f"ERROR_{datetime.now():%Y%m%d}.txt"
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
        result[key] = quoted if quoted else unquoted
    return result

def create_count_table(series, title, col1, col2, top_n=10):
    if series.empty:
        return f"<h2>{title}</h2><p>No data</p>"
    df_table = series.head(top_n).to_frame(name=col2)
    df_table.index.name = col1
    df_table = df_table.reset_index()
    return f"<h2>{title}</h2>" + df_table.to_html(index=False, border=0, classes="table")

def main():
    log_file = find_todays_log()
    today = datetime.now()

    if not log_file:
        log_error(f"Today's log file not found!\nExpected: disk-webfilter-{today.strftime('%Y_%m_%d')}.log")
        input("\nPress Enter to exit...")
        return

    print(f"Found: {log_file.name}")
    print(f"Processing {today.strftime('%d %B %Y')} data...\n")

    logs = []
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parsed = parse_raw_line(line)
            if parsed:
                logs.append(parsed)

    if not logs:
        log_error("No valid log lines found!")
        input("Press Enter...")
        return

    df = pd.DataFrame(logs)
    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], errors='coerce')
    df = df.dropna(subset=['datetime']).sort_values('datetime').reset_index(drop=True)
    blocked = df[(df['action'] == 'blocked') & (df.get('subtype', '') == 'webfilter')]

    # ONE AND ONLY ONE FILE PER DAY — OVERWRITES automatically if run again today
    report_file = OUTPUT_FOLDER / f"WebFilter_Blocked_{today:%Y%m%d}.html"

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Web Filter Block Report - {today:%Y-%m-%d}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            .table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            .table th, .table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            .table th {{ background-color: #f8f9fa; font-weight: bold; }}
            .table tr:nth-child(even) {{ background-color: #f9f9f9; }}
            h1, h2 {{ color: #2c3e50; }}
        </style>
    </head>
    <body>
    <h1>FortiGate Web Filter Block Report</h1>
    <h2>{today.strftime('%A, %d %B %Y')} — Updated: {today.strftime('%H:%M')}</h2>
    <p><b>Source file:</b> {log_file.name}<br>
       <b>Total logs processed:</b> {len(df):,}<br>
       <b>Blocked requests today:</b> <strong style="color:red;font-size:1.3em;">{len(blocked):,}</strong></p>
    <hr>

    {create_count_table(blocked['srcip'], "Top 10 Users Trying to Access Blocked Sites", "Source IP", "Attempts")}
    {create_count_table(blocked['url'], "Top 15 Blocked URLs", "URL", "Hits", 15)}
    {create_count_table(blocked['catdesc'], "Top Blocked Categories", "Category", "Count")}

    <h2>High-Risk Blocks (crlevel = high)</h2>
    {blocked[blocked['crlevel']=='high'][['datetime','srcip','hostname','url','catdesc','msg']].head(25).to_html(index=False, border=0, classes="table")}

    <h2>All Blocked Events (Chronological)</h2>
    {blocked[['datetime','srcip','hostname','url','catdesc','msg']].to_html(index=False, border=0, classes="table")}
    </body></html>
    """

    # This line OVERWRITES the file if it already exists (same date = same filename)
    report_file.write_text(html, encoding='utf-8')

    print("="*70)
    print("SUCCESS! Report generated (old one replaced if existed)")
    print(f"File → {report_file}")
    print(f"Blocked attempts today → {len(blocked):,}")
    print("="*70)
    input("\nPress Enter to close...")

if __name__ == "__main__":
    main()