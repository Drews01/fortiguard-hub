# generate_dns_monthly.py ← DNS Security Monthly Recap from Daily HTML Reports
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
## How to generate the
BASE_FOLDER = Path(__file__).parent
DAILY_REPORTS_FOLDER = BASE_FOLDER / "daily_reports"
MONTHLY_OUTPUT = BASE_FOLDER / "monthly_reports"
MONTHLY_OUTPUT.mkdir(parents=True, exist_ok=True)

def get_month_from_user():
    print("\n" + "═" * 80)
    print("   FORTIGATE DNS SECURITY – MONTHLY RECAP FROM DAILY HTML REPORTS")
    print("═" * 80)
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

def extract_dns_events(html_path):
    """Extract malicious/notable DNS events from daily HTML report"""
    try:
        soup = BeautifulSoup(open(html_path, encoding="utf-8"), "html.parser")
        tables = soup.find_all("table", class_="table")
        if len(tables) < 2:
            return pd.DataFrame()

        # Second table = "Top 10 Malicious Websites"
        domain_table = tables[1]
        rows = domain_table.find_all("tr")
        if len(rows) < 2:
            return pd.DataFrame()

        headers = ["fqdn", "action", "count"]
        data = []
        for row in rows[1:10]:  # Top 10 only
            cols = row.find_all("td")
            if len(cols) != 3: continue
            fqdn = cols[0].get_text(strip=True)
            action = cols[1].get_text(strip=True).lower()
            try:
                count = int(cols[2].get_text(strip=True).replace(",", ""))
            except:
                continue
            data.append({"fqdn": fqdn, "action": action, "count": count})

        return pd.DataFrame(data)

    except Exception as e:
        print(f"Error reading {html_path.name}: {e}")
        return pd.DataFrame()

def extract_category_counts(html_path):
    """Extract category counts from the first table in daily report"""
    try:
        soup = BeautifulSoup(open(html_path, encoding="utf-8"), "html.parser")
        tables = soup.find_all("table", class_="table")
        if not tables:
            return {}

        cat_table = tables[0]
        rows = cat_table.find_all("tr")
        counts = {}
        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) < 2: continue
            cat = cols[0].get_text(strip=True)
            try:
                count = int(cols[1].get_text(strip=True).replace(",", ""))
            except:
                continue
            counts[cat] = counts.get(cat, 0) + count
        return counts
    except:
        return {}

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

    # Find all daily DNS reports for this month
    pattern = f"DNS_Events_Report_{month_str}*.html"
    daily_files = sorted(DAILY_REPORTS_FOLDER.glob(pattern))

    if not daily_files:
        print(f"\nNo daily DNS reports found for {month_name}")
        print(f"Looking for: {pattern}")
        try:
            if sys.stdin and sys.stdin.isatty():
                input("\nPress Enter to exit...")
        except Exception:
            pass
        return

    print(f"\nFound {len(daily_files)} daily reports -> compiling {month_name}...\n")

    all_domains = []
    all_categories = {}
    total_events = 0

    for file in daily_files:
        df_day = extract_dns_events(file)
        if not df_day.empty:
            all_domains.append(df_day)
            total_events += df_day['count'].sum()

        cat_day = extract_category_counts(file)
        for cat, cnt in cat_day.items():
            all_categories[cat] = all_categories.get(cat, 0) + cnt

    if not all_domains:
        print("No malicious DNS events found in any daily report.")
        try:
            if sys.stdin and sys.stdin.isatty():
                input()
        except Exception:
            pass
        return

    monthly_domains = pd.concat(all_domains, ignore_index=True)
    monthly_domains = monthly_domains.groupby(["fqdn", "action"], as_index=False)["count"].sum()
    monthly_domains = monthly_domains.sort_values("count", ascending=False)

    # Top 15 malicious domains of the month
    top_domains = monthly_domains.head(15).copy()
    top_domains["count"] = top_domains["count"].astype(int)

    # Category totals
    cat_series = pd.Series(all_categories).sort_values(ascending=False)
    top_cats = cat_series.head(10)

    # Action breakdown
    action_counts = monthly_domains['action'].value_counts()

    # === Generate Pie Charts ===
    def make_pie(data, title, colors=None):
        fig, ax = plt.subplots(figsize=(8, 6))
        if colors is None:
            colors = plt.cm.Set3(range(len(data)))
        wedges, texts, autotexts = ax.pie(data.values, labels=None, autopct='%1.1f%%',
                                          startangle=90, colors=colors)
        ax.legend([f"{k} ({v:,})" for k, v in data.items()],
                  title="Legend", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        ax.set_title(title, fontsize=16, pad=20)
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=180, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        return base64.b64encode(buffer.getvalue()).decode()

    pie_cats = make_pie(top_cats, f"Top DNS Threat Categories – {month_name}")
    pie_actions = make_pie(action_counts, f"Actions Taken – {month_name}",
                           colors=['#e74c3c', '#e67e22', '#27ae60', '#95a5a6'])

    # === Generate HTML Report ===
    report_file = MONTHLY_OUTPUT / f"DNS_Monthly_Report_{month_str}.html"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>DNS Security Monthly Report – {month_name}</title>
<style>
    body{{font-family:'Segoe UI',sans-serif;background:#f5f6fa;margin:0;}}
    .wrap{{max-width:1500px;margin:30px auto;background:#fff;padding:40px;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,.12);}}
    h1{{color:#e74c3c;text-align:center;}}
    h2{{color:#c0392b;text-align:center;margin:10px 0;}}
    .stat{{text-align:center;background:linear-gradient(135deg,#e74c3c,#c0392b);color:#fff;padding:35px;border-radius:14px;font-size:1.8em;}}
    .flex{{display:flex;gap:30px;flex-wrap:wrap;justify-content:center;margin:50px 0;}}
    .card{{flex:1;min-width:420px;background:#f8f9fa;padding:25px;border-radius:14px;box-shadow:0 4px 15px rgba(0,0,0,.08);}}
    table{{width:100%;border-collapse:collapse;margin:20px 0;font-size:0.95em;}}
    th,td{{padding:12px;border:1px solid #ddd;text-align:left;}}
    th{{background:#e74c3c;color:#fff;text-align:center !important;}}
    tr:nth-child(even){{background:#f0f0f0;}}
    .pie img{{max-width:100%;border-radius:12px;box-shadow:0 8px 25px rgba(0,0,0,.15);}}
    footer{{text-align:center;margin-top:60px;color:#888;font-size:0.9em;}}
</style>
</head><body>
<div class="wrap">
    <h1>DNS (Domain Name System) Security</h1>
    <h2>Monthly Threat Recap – {month_name}</h2>

    <div class="stat">
        <div style="font-size:3.2em;font-weight:bold;">{total_events:,}</div>
        Malicious / Notable DNS Queries<br>
        <div style="margin-top:15px;font-size:0.7em;">From <strong>{len(daily_files)}</strong> daily reports</div>
    </div>

    <div class="flex">
        <div class="card">
            <h2 style="text-align:center;color:#c0392b;">Top 15 Malicious Domains of the Month</h2>
            {top_domains[['fqdn', 'action', 'count']].to_html(index=False, border=0, classes='table')}
        </div>
    </div>

    <div class="flex">
        <div class="card pie">
            <h2 style="text-align:center;color:#c0392b;">Threat Categories Distribution</h2>
            <img src="data:image/png;base64,{pie_cats}">
        </div>
        <div class="card pie">
            <h2 style="text-align:center;color:#c0392b;">Security Actions Taken</h2>
            <img src="data:image/png;base64,{pie_actions}">
        </div>
    </div>

    <footer>
        FortiGate DNS Security Monthly Report • Generated on {datetime.now():%Y-%m-%d %H:%M} 
        from {len(daily_files)} daily HTML reports
    </footer>
</div></body></html>"""

    report_file.write_text(html, encoding="utf-8")
    print("\n" + "=" * 80)
    print("DNS MONTHLY REPORT SUCCESSFULLY CREATED!")
    print(f"-> {report_file.name}")
    print(f"-> Total malicious DNS events: {total_events:,}")
    print(f"-> From {len(daily_files)} daily reports")
    print("=" * 80)
    try:
        if sys.stdin and sys.stdin.isatty():
            input("\nPress Enter to finish...")
    except Exception:
        pass

if __name__ == "__main__":
    main()