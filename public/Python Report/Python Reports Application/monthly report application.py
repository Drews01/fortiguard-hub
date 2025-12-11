# generate_appctrl_monthly_FROM_DAILY_HTML.py  ← YOUR CODE, NOW USING daily_reports FOLDER
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from bs4 import BeautifulSoup
import os

os.system("")  # Enable colors/UTF-8 in Windows terminal

BASE_FOLDER = Path(__file__).parent
DAILY_REPORTS_FOLDER = BASE_FOLDER / "daily_reports"
MONTHLY_OUTPUT = BASE_FOLDER / "monthly_reports"
MONTHLY_OUTPUT.mkdir(exist_ok=True)

def get_month_from_user():
    print("\n" + "═" * 76)
    print("   FORTIGATE APPLICATION CONTROL – MONTHLY REPORT FROM DAILY HTML")
    print("═" * 76)
    print("1. Current month    2. Specific month    3. Last month")
    while True:
        c = input("\nChoose (1/2/3) [Enter = current]: ").strip() or "1"
        if c == "1":
            return datetime.now().strftime("%Y%m")
        if c == "3":
            now = datetime.now()
            y, m = now.year, now.month - 1
            if m == 0: m, y = 12, y - 1
            return f"{y}{m:02d}"
        if c == "2":
            i = input("Enter YYYYMM (e.g. 202512): ").strip()
            if len(i) == 6 and i.isdigit():
                return i
        print("Invalid input. Try again.")

def extract_blocked_events(html_path):
    """Extract blocked app events from daily FortiGate HTML (last table), removing header rows inside body."""
    try:
        soup = BeautifulSoup(open(html_path, encoding="utf-8"), "html.parser")
        tables = soup.find_all("table", class_="table")
        if not tables:
            return pd.DataFrame()

        last_table = tables[-1]
        rows = last_table.find_all("tr")

        # Get header from FIRST row only
        header_cells = rows[0].find_all(["th", "td"])
        headers = [cell.get_text(strip=True).lower() for cell in header_cells]

        data_rows = []
        for row in rows[1:]:
            cols = [td.get_text(strip=True) for td in row.find_all("td")]

            # Skip empty or malformed rows
            if len(cols) != len(headers):
                continue

            # --- HARD FIX: Remove duplicated header rows inside table body ---
            if [c.lower() for c in cols] == headers:
                continue

            data_rows.append(dict(zip(headers, cols)))

        return pd.DataFrame(data_rows)

    except Exception as e:
        print(f"Error reading {html_path.name}: {e}")
        return pd.DataFrame()



# ═══════════════════════════════════════════════════════════════════
def main():
    # Accept optional month argument (YYYYMM or YYYY_MM or YYYY-MM)
    if len(sys.argv) > 1:
        raw = sys.argv[1]
        month_str = raw.replace('_', '').replace('-', '')
    else:
        # If interactive, ask user; otherwise default to last month
        try:
            if sys.stdin and sys.stdin.isatty():
                month_str = get_month_from_user()
            else:
                now = datetime.now()
                y, m = now.year, now.month - 1
                if m == 0: m, y = 12, y - 1
                month_str = f"{y}{m:02d}"
        except Exception:
            now = datetime.now()
            y, m = now.year, now.month - 1
            if m == 0: m, y = 12, y - 1
            month_str = f"{y}{m:02d}"
    month_name = datetime.strptime(month_str, "%Y%m").strftime("%B %Y")

    # Find all daily HTML reports for this month
    pattern = f"AppCtrl_Blocked_{month_str}*.html"
    daily_files = sorted(DAILY_REPORTS_FOLDER.glob(pattern))

    if not daily_files:
        print(f"\nNo daily reports found: {pattern}")
        try:
            if sys.stdin and sys.stdin.isatty():
                input("\nPress Enter to exit...")
        except Exception:
            pass
        return

    print(f"\nFound {len(daily_files)} daily reports → compiling {month_name}...\n")

    all_dataframes = []
    for file in daily_files:
        df_day = extract_blocked_events(file)
        if not df_day.empty:
            all_dataframes.append(df_day)

    if not all_dataframes:
        print("No blocked events found in any daily report.")
        try:
            if sys.stdin and sys.stdin.isatty():
                input()
        except Exception:
            pass
        return

    blocked = pd.concat(all_dataframes, ignore_index=True)

    cols_to_clean = ["app", "srcip", "appcat", "apprisk"]
    for col in cols_to_clean:
        if col in blocked.columns:
            blocked = blocked[blocked[col].str.lower() != col]

    # Safe column access
    blocked['app'] = blocked.get('app_safe', blocked.get('app', 'Unknown'))
    blocked['appcat'] = blocked.get('appcat', 'Uncategorized')
    blocked['apprisk'] = blocked.get('apprisk', 'unknown').str.lower()
    blocked['srcip'] = blocked.get('srcip', 'Unknown')
    blocked['hostname'] = blocked.get('hostname_safe', blocked.get('hostname', '-'))

    total_blocked = len(blocked)
    saved_mib = 0  # Not available from HTML, but we keep placeholder

    # TOP STATS
    top_blocked_apps = blocked['app'].value_counts().head(12)
    top_blocked_apps.index.name = None

    top_ips = blocked['srcip'].value_counts().head(10)
    top_ips.index.name = None

    # ---- FIX TABLE HEADERS ----
    app_table = top_blocked_apps.reset_index()
    app_table.columns = ["Application", "Blocks"]

    ip_table = top_ips.reset_index()
    ip_table.columns = ["IP Address", "Blocks"]

    # NEW LINE — REQUIRED
    top_cats = blocked['appcat'].value_counts().head(10)
    top_cats.index.name = None



    # Risk levels
    risk_order = ['critical', 'high', 'elevated', 'medium', 'low']
    risk_counts = blocked['apprisk'].value_counts().reindex(risk_order, fill_value=0)
    risk_counts['unknown'] = risk_counts.get('unknown', 0)

    # Pie charts (same as before)
    def make_pie(data, title):
        fig, ax = plt.subplots(figsize=(8,6))
        colors = plt.cm.Set3(range(len(data)))
        ax.pie(data.values, labels=None, autopct='%1.1f%%', startangle=90, colors=colors)
        ax.legend([f"{k} ({v:,})" for k,v in data.items()], title="Legend",
                  loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        ax.set_title(title, fontsize=16, pad=20)
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=180, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        return base64.b64encode(buffer.getvalue()).decode()

    pie_cat = make_pie(top_cats, f"Top Blocked Categories – {month_name}")
    pie_risk = make_pie(risk_counts, f"Risk Level of Blocked Apps – {month_name}")

    # HTML Report (your beautiful design unchanged)
    report_file = MONTHLY_OUTPUT / f"AppCtrl_Monthly_Report_{month_str}.html"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>AppCtrl Monthly Report – {month_name}</title>
<style>
    body{{font-family:'Segoe UI',sans-serif;background:#f5f6fa;margin:0;}}
    .wrap{{max-width:1500px;margin:30px auto;background:#fff;padding:40px;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,.12);}}
    h1{{color:#8e44ad;text-align:center;}}
    .stat{{text-align:center;background:linear-gradient(135deg,#9b59b6,#8e44ad);color:#fff;padding:30px;border-radius:14px;font-size:1.8em;}}
    .flex{{display:flex;gap:30px;flex-wrap:wrap;justify-content:center;margin:50px 0;}}
    .card{{flex:1;min-width:420px;background:#f8f9fa;padding:25px;border-radius:14px;}}
    table{{width:100%;border-collapse:collapse;margin:20px 0;font-size:0.95em;}}
    th,td{{padding:12px;border:1px solid #ddd;text-align:left;}}
    th{{background:#9b59b6;color:#fff;text-align:center !important;}}
    tr:nth-child(even){{background:#f0f0f0;}}
    .pie img{{max-width:100%;border-radius:12px;box-shadow:0 8px 25px rgba(0,0,0,.15);}}
    footer{{text-align:center;margin-top:60px;color:#888;font-size:0.9em;}}
</style>
</head><body>
<div class="wrap">
    <h1>FortiGate Application Control</h1>
    <h2 style="text-align:center;color:#2c3e50;margin-top:-10px;">Monthly Report – {month_name}</h2>

    <div class="stat">
        <div style="font-size:2.8em;font-weight:bold;">{total_blocked:,}</div>
        Applications <strong>BLOCKED</strong> this month<br>
        <div style="margin-top:15px;">Data from <strong>{len(daily_files)}</strong> daily reports</div>
    </div>

    <div class="flex">
        <div class="card">
            <h2>Top 12 Blocked Applications</h2>
            {app_table.to_html(index=False, border=0, classes='table')}

        </div>
        <div class="card">
            <h2>Top 10 Users/Devices (by blocks)</h2>
           {ip_table.to_html(index=False, border=0, classes='table')}

        </div>
    </div>

    <div class="flex">
        <div class="card pie">
            <h2 style="text-align:center;">Blocked by Category</h2>
            <img src="data:image/png;base64,{pie_cat}">
        </div>
        <div class="card pie">
            <h2 style="text-align:center;">Blocked by Risk Level</h2>
            <img src="data:image/png;base64,{pie_risk}">
        </div>
    </div>

    <footer>
        Generated on {datetime.now():%Y-%m-%d %H:%M} from {len(daily_files)} daily HTML reports
    </footer>
</div></body></html>"""

    report_file.write_text(html, encoding="utf-8")
    print("\n" + "═" * 80)
    print("MONTHLY REPORT SUCCESSFULLY CREATED!")
    print(f"→ {report_file.name}")
    print(f"→ {total_blocked:,} blocked events from {len(daily_files)} daily reports")
    print("═" * 80)
    try:
        if sys.stdin and sys.stdin.isatty():
            input("\nPress Enter to finish...")
    except Exception:
        pass

if __name__ == "__main__":
    main()