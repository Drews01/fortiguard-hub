# generate_ips_monthly.py ← Monthly IPS Critical Events Recap (Trend Chart Only)

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except Exception as e:
    print(f"Error importing matplotlib or setting backend: {e}")
    raise
import base64
from io import BytesIO
from bs4 import BeautifulSoup
import os
import re

os.system("")  # Enable colors in Windows terminal

BASE_FOLDER = Path(__file__).parent
DAILY_REPORTS_FOLDER = BASE_FOLDER / "daily_reports"
MONTHLY_OUTPUT = BASE_FOLDER / "monthly_reports"
MONTHLY_OUTPUT.mkdir(parents=True, exist_ok=True)

def get_month_from_user():
    print("\n" + "=" * 82)
    print("   FORTIGATE IPS - MONTHLY CRITICAL EVENTS RECAP")
    print("=" * 82)
    print("1. Current month    2. Specific month    3. Last month")
    while True:
        c = input("\nChoose (1/2/3) [Enter = current]: ").strip() or "1"
        if c == "1":
            return datetime.now().strftime("%Y%m")
        if c == "3":
            now = datetime.now()
            y, m = now.year, now.month - 1
            if m == 0:
                m, y = 12, y - 1
            return f"{y}{m:02d}"
        if c == "2":
            i = input("Enter YYYYMM (e.g. 202512): ").strip()
            if len(i) == 6 and i.isdigit():
                return i
        print("Invalid input. Try again.")

def extract_ips_events(html_path):
    """Extract Top 10 Critical Attacks table from daily IPS HTML report"""
    try:
        soup = BeautifulSoup(open(html_path, encoding="utf-8"), "html.parser")
        tables = soup.find_all("table")
        if not tables:
            return pd.DataFrame(), 0, None

        table = tables[0]  # First table = Top 10 attacks
        rows = table.find_all("tr")
        if len(rows) < 2:
            return pd.DataFrame(), 0, None

        data = []
        total_count = 0

        for row in rows[1:]:
            cols = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cols) < 3: continue

            attack = cols[0].replace("**", "").strip()
            try:
                count = int(cols[2].replace(",", ""))
            except:
                continue

            total_count += count
            srcip = cols[3] if len(cols) > 3 else "N/A"
            country = cols[4] if len(cols) > 4 else "N/A"
            dstip = cols[5] if len(cols) > 5 else "N/A"

            data.append({
                "attack": attack,
                "count": count,
                "srcip": srcip,
                "country": country,
                "dstip": dstip
            })

        # Extract date from filename
        date_match = re.search(r"IPS_Critical_Events_(\d{8})", html_path.name)
        report_date = datetime.strptime(date_match.group(1), "%Y%m%d").date() if date_match else None

        return pd.DataFrame(data), total_count, report_date
    except Exception as e:
        print(f"Error reading {html_path.name}: {e}")
        return pd.DataFrame(), 0, None

def main():
    # Accept optional month argument
    if len(sys.argv) > 1:
        raw = sys.argv[1]
        month_str = raw.replace('_', '').replace('-', '')
    else:
        try:
            if sys.stdin and sys.stdin.isatty():
                month_str = get_month_from_user()
            else:
                now = datetime.now()
                y, m = now.year, now.month - 1
                if m == 0: m, y = 12, y - 1
                month_str = f"{y}{m:02d}"
        except:
            now = datetime.now()
            y, m = now.year, now.month - 1
            if m == 0: m, y = 12, y - 1
            month_str = f"{y}{m:02d}"

    month_name = datetime.strptime(month_str, "%Y%m").strftime("%B %Y")

    pattern = f"IPS_Critical_Events_{month_str}*.html"
    daily_files = sorted(DAILY_REPORTS_FOLDER.glob(pattern))

    if not daily_files:
        print(f"\nNo daily IPS reports found for {month_name}")
        print(f"Looking for: {pattern}")
        if sys.stdin.isatty():
            input("\nPress Enter to exit...")
        return

    print(f"\nFound {len(daily_files)} daily reports -> compiling {month_name}...\n")

    all_attacks = []
    daily_counts = {}
    total_events = 0

    for file in daily_files:
        df_day, day_count, day_date = extract_ips_events(file)
        if not df_day.empty:
            all_attacks.append(df_day)
            total_events += day_count
            if day_date:
                daily_counts[day_date.day] = day_count

    if not all_attacks:
        print("No IPS events found in any daily report.")
        if sys.stdin.isatty():
            input("\nPress Enter...")
        return

    monthly_df = pd.concat(all_attacks, ignore_index=True)
    monthly_summary = monthly_df.groupby(["attack", "srcip", "country", "dstip"], as_index=False)["count"].sum()
    monthly_summary = monthly_summary.sort_values("count", ascending=False)
    top_attacks = monthly_summary.head(15)

    # === Daily Trend Line Chart ===
    days_in_month = pd.date_range(f"{month_str}01", periods=31, freq='D')
    trend_data = pd.Series(0, index=range(1, 32))
    for day, count in daily_counts.items():
        trend_data[day] = count

    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.plot(trend_data.index, trend_data.values, marker='o', linewidth=3, markersize=8, color='#e74c3c')
    ax.fill_between(trend_data.index, trend_data.values, alpha=0.25, color='#e74c3c')
    ax.set_title(f"Daily Critical IPS Events – {month_name}", fontsize=20, pad=25, color='#2c3e50')
    ax.set_xlabel("Day of Month", fontsize=12)
    ax.set_ylabel("Number of Critical Events", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(range(1, 32, 2))
    ax.set_ylim(0)
    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    trend_chart = base64.b64encode(buffer.getvalue()).decode()

    report_file = MONTHLY_OUTPUT / f"IPS_Monthly_Report_{month_str}.html"

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>IPS Monthly Report – {month_name}</title>
    <style>
        body{{font-family:'Segoe UI',sans-serif;background:#f5f6fa;margin:0;}}
        .wrap{{max-width:1400px;margin:40px auto;background:#fff;padding:40px;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,.12);}}
        h1{{color:#e74c3c;text-align:center;margin-bottom:10px;}}
        h2{{color:#c0392b;text-align:center;margin:30px 0 10px;}}
        .stat{{text-align:center;background:linear-gradient(135deg,#e74c3c,#c0392b);color:#fff;padding:40px;border-radius:16px;font-size:1.9em;}}
        .stat span{{font-size:4em;font-weight:bold;display:block;margin:15px 0;}}
        table{{width:100%;border-collapse:collapse;margin:30px 0;font-size:0.98em;}}
        th,td{{padding:14px;border:1px solid #ddd;text-align:left;}}
        th{{background:#e74c3c;color:#fff;text-align:center !important;}}
        tr:nth-child(even){{background:#fdf2f2;}}
        .trend img{{max-width:100%;border-radius:14px;box-shadow:0 10px 30px rgba(0,0,0,.2);}}
        footer{{text-align:center;margin-top:70px;color:#888;font-size:0.95em;}}
    </style>
</head>
<body>
<div class="wrap">
    <h1>IPS Monthly Critical Events Report</h1>
    <h2>{month_name}</h2>

    <div class="stat">
        <span>{total_events:,}</span>
        Total Critical & Blocked Events This Month
        <div style="margin-top:15px;font-size:0.7em;">Compiled from <strong>{len(daily_files)}</strong> daily reports</div>
    </div>

    <h2>Daily Trend</h2>
    <div class="trend">
        <img src="data:image/png;base64,{trend_chart}" alt="Daily IPS Events Trend">
    </div>

    <h2>Top 15 Most Frequent Critical Attacks</h2>
    {top_attacks[['attack','count','srcip','country','dstip']].to_html(index=False, border=0, classes='table')}

    <footer>
        FortiGate IPS Monthly Report • Generated on {datetime.now():%Y-%m-%d %H:%M} 
        from {len(daily_files)} daily HTML reports
    </footer>
</div>
</body>
</html>"""

    report_file.write_text(html, encoding="utf-8")
    print("\n" + "=" * 85)
    print("IPS MONTHLY REPORT SUCCESSFULLY CREATED!")
    print(f"→ File           : {report_file.name}")
    print(f"→ Month          : {month_name}")
    print(f"→ Total Events   : {total_events:,}")
    print(f"→ Daily Reports  : {len(daily_files)}")
    print("=" * 85)
    if sys.stdin.isatty():
        input("\nPress Enter to finish...")

if __name__ == "__main__":
    main()
