# FortiGate_WebFilter_MONTHLY_REPORT_FULL_CONTROL.py
import pandas as pd
import re
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import os

# ================== CHANGE THESE PATHS ==================
BASE_FOLDER = Path(__file__).parent
DAILY_REPORTS_FOLDER = BASE_FOLDER / "daily_reports"          # ← CORRECT!
MONTHLY_OUTPUT_FOLDER = BASE_FOLDER / "monthly_reports"
MONTHLY_OUTPUT_FOLDER.mkdir(exist_ok=True)
# =======================================================

def get_month_from_user():
    print("\n" + "="*60)
    print("     FORTIGATE WEB FILTER - MONTHLY REPORT GENERATOR")
    print("="*60)
    print("\nOptions:")
    print("1. Generate report for CURRENT month (auto)")
    print("2. Generate report for SPECIFIC month (you choose)")
    print("3. Generate report for LAST month")
    
    while True:
        choice = input("\nEnter choice (1/2/3): ").strip()
        if choice == "1":
            return datetime.now().strftime("%Y_%m")
        elif choice == "3":
            # Last month
            today = datetime.now()
            year = today.year
            month = today.month - 1
            if month == 0:
                month = 12
                year -= 1
            return f"{year}_{month:02d}"
        elif choice == "2":
            while True:
                user_input = input("\nEnter year and month (example: 2025_12 or 202512): ").strip()
                user_input = user_input.replace("-", "_").replace("/", "_")
                if re.match(r"^\d{4}[-_]?\d{1,2}$", user_input):
                    if len(user_input) == 6:
                        return f"{user_input[:4]}_{user_input[4:]:0>2}"
                    elif "_" in user_input:
                        y, m = user_input.split("_")
                        return f"{y}_{m.zfill(2)}"
                    else:
                        return f"{user_input[:4]}_{user_input[4:]:0>2}"
                print("Invalid format! Use YYYY_MM or YYYYMM")
        else:
            print("Please enter 1, 2, or 3")

def extract_blocked_events(html_file):
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        tables = soup.find_all('table', class_='table')
        if len(tables) < 2:
            return pd.DataFrame()
        
        last_table = tables[-1]  # "All Blocked Events" table
        rows = last_table.find_all('tr')
        if len(rows) < 2:
            return pd.DataFrame()
        
        headers = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])]
        data = []
        for row in rows[1:]:
            cols = [td.get_text(strip=True) for td in row.find_all('td')]
            if len(cols) >= 5:
                data.append({
                    'datetime': cols[0],
                    'srcip': cols[1],
                    'hostname': cols[2],
                    'url': cols[3],
                    'catdesc': cols[4],
                    'msg': cols[5] if len(cols) > 5 else ''
                })
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

def generate_monthly_report():
    target_month = get_month_from_user()  # ← This is the magic line
    month_name = datetime.strptime(target_month, "%Y_%m").strftime("%B %Y")

    pattern = f"WebFilter_Blocked_{target_month.replace('_', '')}*.html"
    # CORRECT: matches your real daily filename format (20251208, not 2025_12)
    monthly_files = list(DAILY_REPORTS_FOLDER.glob(f"WebFilter_Blocked_{target_month.replace('_', '')}*.html"))
    
    if not monthly_files:
        print(f"\nNo daily reports found for {month_name}")
        print(f"Looking for files like: WebFilter_Blocked_{target_month}*.html")
        input("\nPress Enter to exit...")
        return

    print(f"\nFound {len(monthly_files)} daily reports for {month_name}")
    print("Compiling monthly summary...\n")

    all_blocked = []
    for file in monthly_files:
        df = extract_blocked_events(file)
        if not df.empty:
            all_blocked.append(df)

    if not all_blocked:
        print("No blocked events found in any daily report.")
        input("Press Enter...")
        return

    monthly_df = pd.concat(all_blocked, ignore_index=True)
    total_blocked = len(monthly_df)

    cat_counts = monthly_df['catdesc'].value_counts()
    top_cats = cat_counts.head(10)
    top_domains = monthly_df['hostname'].value_counts().head(10)

    # Pie chart
    plt.figure(figsize=(9, 7))
    colors = plt.cm.Set3(range(len(top_cats)))
    wedges, texts, autotexts = plt.pie(
        top_cats.values,
        labels=None,
        autopct=lambda p: f'{p:.1f}%' if p >= 1 else '',
        startangle=90,
        colors=colors
    )
    plt.legend(wedges, [f"{cat} ({count:,} - {count/total_blocked*100:.1f}%)" 
                       for cat, count in top_cats.items()],
               title="Categories", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    plt.title(f"Top Blocked Categories - {month_name}", fontsize=16, pad=20)
    chart_file = MONTHLY_OUTPUT_FOLDER / f"PieChart_{target_month}.png"
    plt.savefig(chart_file, dpi=150, bbox_inches='tight')
    plt.close()

    # Final report
    report_file = MONTHLY_OUTPUT_FOLDER / f"WebFilter_Monthly_Report_{target_month}.html"

    html = f"""
    <html><head><meta charset="utf-8">
    <title>Monthly Web Filter Report - {month_name}</title>
    <style>
        body {{ font-family: Arial; margin: 40px; background: #f9f9f9; }}
        .container {{ max-width: 1300px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; text-align: center; }}
        .stats {{ font-size: 1.5em; text-align: center; margin: 30px 0; color: #e74c3c; }}
        table {{ width: 100%; border-collapse: collapse; margin: 25px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background: #f4f4f4; font-weight: bold; }}
        .pie {{ text-align: center; margin: 40px 0; }}
    </style></head>
    <body>
    <div class="container">
    <h1>Web Filter Events - Monthly Report</h1>
    <h2 style="text-align:center">{month_name}</h2>
    <div class="stats">Total Blocked Requests: <strong>{total_blocked:,}</strong></div>
    <hr>

    <div style="display:flex; gap:30px; flex-wrap:wrap;">
        <div style="flex:1; min-width:380px;">
            <h2>Top 10 Web Filter Events by Category</h2>
            {top_cats.to_frame(name="Count").to_html()}
        </div>
        <div style="flex:1; min-width:380px;">
            <h2>Top 10 Blocked Domains</h2>
            {top_domains.to_frame(name="Count").to_html()}
        </div>
    </div>

    <div class="pie">
        <img src="{chart_file.name}" style="max-width:100%; height:auto; border: 1px solid #ddd; border-radius: 10px;">
    </div>
    </div>
    </body></html>
    """

    report_file.write_text(html, encoding='utf-8')
    print("="*70)
    print(f"SUCCESS! Monthly report for {month_name}")
    print(f"→ {report_file}")
    print(f"→ Total blocked: {total_blocked:,}")
    print("="*70)
    input("\nPress Enter to close...")

if __name__ == "__main__":
    generate_monthly_report()