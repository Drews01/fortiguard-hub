# generate_ips_monthly.py ← Monthly IPS Critical Events Recap (with Trend Chart!)
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from bs4 import BeautifulSoup
import os
import re

os.system("")  # Enable colors in Windows

BASE_FOLDER = Path(__file__).parent
DAILY_REPORTS_FOLDER = BASE_FOLDER / "daily_reports"
MONTHLY_OUTPUT = BASE_FOLDER / "monthly_reports"
MONTHLY_OUTPUT.mkdir(exist_ok=True)

def get_month_from_user():
    print("\n" + "═" * 82)
    print("   FORTIGATE IPS (Intrusion Prevention System) – MONTHLY RECAP")
    print("═" * 82)
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

def extract_ips_events(html_path):
    """Extract Top 10 Critical Attacks table from daily IPS HTML report"""
    try:
        soup = BeautifulSoup(open(html_path, encoding="utf-8"), "html.parser")
        tables = soup.find_all("table", class_="table")
        if len(tables) < 1:
            return pd.DataFrame(), 0

        # First table = Top 10 Critical Attacks
        table = tables[0]
        rows = table.find_all("tr")
        if len(rows) < 2:
            return pd.DataFrame(), 0

        headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]
        data = []
        total_count = 0

        for row in rows[1:]:
            cols = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cols) < 5: continue

            attack = cols[0].replace("**", "").strip()
            action = cols[1]
            count_str = cols[2].replace(",", "").strip()
            try:
                count = int(count_str)
            except:
                continue

            total_count += count
            srcip = cols[3] if len(cols) > 3 else "Unknown"
            country = cols[4] if len(cols) > 4 else "Unknown"
            dstip = cols[5] if len(cols) > 5 else "Unknown"
            service = cols[6] if len(cols) > 6 else "Unknown"

            data.append({
                "attack": attack,
                "action": action,
                "count": count,
                "srcip": srcip,
                "country": country,
                "dstip": dstip,
                "service": service
            })

        # Also get report date from filename
        date_match = re.search(r"IPS_Critical_Events_(\d{8})", html_path.name)
        report_date = datetime.strptime(date_match.group(1), "%Y%m%d").date() if date_match else None

        return pd.DataFrame(data), total_count, report_date
    except Exception as e:
        print(f"Error reading {html_path.name}: {e}")
        return pd.DataFrame(), 0, None

# ═══════════════════════════════════════════════════════════════════
def main():
    # Accept optional month argument (YYYYMM or YYYY_MM or YYYY-MM)
    if len(sys.argv) > 1:
        raw = sys.argv[1]
        month_str = raw.replace('_', '').replace('-', '')
    else:
        try:
            if sys.stdin and sys.stdin.isatty():
                month_str = get_month_from_user()
            else:
                now = datetime.now(); y, m = now.year, now.month - 1
                if m == 0: m, y = 12, y - 1
                month_str = f"{y}{m:02d}"
        except Exception:
            now = datetime.now(); y, m = now.year, now.month - 1
            if m == 0: m, y = 12, y - 1
            month_str = f"{y}{m:02d}"

    month_name = datetime.strptime(month_str, "%Y%m").strftime("%B %Y")

    pattern = f"IPS_Critical_Events_{month_str}*.html"
    daily_files = sorted(DAILY_REPORTS_FOLDER.glob(pattern))

    if not daily_files:
        print(f"\nNo daily IPS reports found for {month_name}")
        print(f"Looking for: {pattern}")
        try:
            if sys.stdin and sys.stdin.isatty():
                input("\nPress Enter to exit...")
        except Exception:
            pass
        return

    print(f"\nFound {len(daily_files)} daily reports → compiling {month_name}...\n")

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
        try:
            if sys.stdin and sys.stdin.isatty():
                input()
        except Exception:
            pass
        return

    monthly_df = pd.concat(all_attacks, ignore_index=True)
    monthly_summary = monthly_df.groupby(["attack", "action", "srcip", "country", "dstip"], as_index=False)["count"].sum()
    monthly_summary = monthly_summary.sort_values("count", ascending=False)

    top_attacks = monthly_summary.head(15)

    # === Daily Trend Chart ===
    days_in_month = pd.date_range(f"{month_str}01", periods=31, freq='D')
    trend_data = pd.Series(0, index=range(1, 32))
    for day, count in daily_counts.items():
        trend_data[day] = count

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(trend_data.index, trend_data.values, marker='o', linewidth=2.5, color='#9b59b6')
    ax.fill_between(trend_data.index, trend_data.values, alpha=0.3, color='#9b59b6')
    ax.set_title(f"Daily Critical IPS Events – {month_name}", fontsize=18, pad=20)
    ax.set_xlabel("Date (mday)")
    ax.set_ylabel("Count")
    ax.grid(True, alpha=0.3)
    ax.set_xticks(range(1, 32, 2))
    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    trend_chart = base64.b64encode(buffer.getvalue()).decode()

    # === Pie Charts ===
    def make_pie(data, title):
        fig, ax = plt.subplots(figsize=(8,6))
        colors = plt.cm.Set3(range(len(data)))
        wedges, texts, autotexts = ax.pie(data.values, autopct='%1.1f%%', startangle=90, colors=colors)
        ax.legend([f"{k} ({v:,})" for k,v in data.items()], title="Legend",
                  loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        ax.set_title(title, fontsize=16, pad=20)
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=180, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        return base64.b64encode(buffer.getvalue()).decode()

    action_pie = make_pie(monthly_df['action'].value_counts(), f"Actions Taken – {month_name}")

    report_file = MONTHLY_OUTPUT / f"IPS_Monthly_Report_{month_str}.html"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>IPS Monthly Report – {month_name}</title>
<style>
    body{{font-family:'Segoe UI',sans-serif;background:#f5f6fa;margin:0;}}
    .wrap{{max-width:1600px;margin:30px auto;background:#fff;padding:40px;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,.12);}}
    h1{{color:#e74c3c;text-align:center;}}
    h2{{color:#c0392b;text-align:center;margin:10px 0;}}
    .stat{{text-align:center;background:linear-gradient(135deg,#e74c3c,#c0392b);color:#fff;padding:35px;border-radius:14px;font-size:1.8em;}}
    .stat span{{font-size:3.5em;font-weight:bold;display:block;margin:10px 0;}}
    .flex{{display:flex;gap:30px;flex-wrap:wrap;justify-content:center;margin:50px 0;}}
    .card{{flex:1;min-width:450px;background:#f8f9fa;padding:25px;border-radius:14px;box-shadow:0 4px 15px rgba(0,0,0,.08);}}
    table{{width:100%;border-collapse:collapse;margin:20px 0;font-size:0.95em;}}
    th,td{{padding:12px;border:1px solid #ddd;text-align:left;}}
    th{{background:#e74c3c;color:#fff;text-align:center !important;}}
    tr:nth-child(even){{background:#f0f0f0;}}
    .trend img, .pie img{{max-width:100%;border-radius:12px;box-shadow:0 8px 25px rgba(0,0,0,.15);}}
    footer{{text-align:center;margin-top:60px;color:#888;font-size:0.9em;}}
</style>
</head><body>
<div class="wrap">
    <h1>IPS (Intrusion Prevention System)</h1>
    <h2>Monthly Critical Threat Recap – {month_name}</h2>

    <div class="stat">
        <span>{total_events:,}</span>
        Critical IPS Events Detected & Blocked
        <div style="margin-top:15px;font-size:0.7em;">From <strong>{len(daily_files)}</strong> daily reports</div>
    </div>

    <div class="flex">
        <div class="card trend">
            <h2 style="text-align:center;color:#c0392b;">Daily Critical IPS Events Trend</h2>
            <img src="data:image/png;base64,{trend_chart}">
        </div>
    </div>

    <div class="flex">
        <div class="card">
            <h2 style="text-align:center;color:#c0392b;">Top 15 Critical Attacks of the Month</h2>
            {top_attacks[['attack','action','count','srcip','country','dstip']].to_html(index=False, border=0, classes='table')}
        </div>
    </div>

    <div class="flex">
        <div class="card pie">
            <h2 style="text-align:center;color:#c0392b;">Security Actions Taken</h2>
            <img src="data:image/png;base64,{action_pie}">
        </div>
    </div>

    <footer>
        FortiGate IPS Monthly Report • Generated on {datetime.now():%Y-%m-%d %H:%M} 
        from {len(daily_files)} daily HTML reports
    </footer>
</div></body></html>"""

    report_file.write_text(html, encoding="utf-8")
    print("\n" + "═" * 85)
    print("IPS MONTHLY REPORT SUCCESSFULLY CREATED!")
    print(f"→ {report_file.name}")
    print(f"→ Total critical events: {total_events:,}")
    print(f"→ From {len(daily_files)} daily reports")
    print("═" * 85)
    try:
        if sys.stdin and sys.stdin.isatty():
            input("\nPress Enter to finish...")
    except Exception:
        pass

if __name__ == "__main__":
    main()