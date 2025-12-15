# generate_monthly.py  ← FINAL VERSION (NO PNG + OVERWRITE + PERFECT HEADERS)
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
from bs4 import BeautifulSoup
import re
import base64
from io import BytesIO

# SMART PATHS — AUTO DETECTS YOUR FOLDER
BASE_FOLDER = Path(__file__).parent
DAILY_REPORTS_FOLDER = BASE_FOLDER / "daily_reports"
MONTHLY_OUTPUT_FOLDER = BASE_FOLDER / "monthly_reports"
MONTHLY_OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

def get_month_from_user():
    print("\n" + "="*60)
    print("     FORTIGATE WEB FILTER - MONTHLY REPORT GENERATOR")
    print("="*60)
    print("1. Current month   2. Specific month   3. Last month")
    while True:
        c = input("\nChoose (1/2/3): ").strip()
        if c == "1": return datetime.now().strftime("%Y_%m")
        if c == "3":
            d = datetime.now(); y, m = d.year, d.month-1
            if m == 0: m, y = 12, y-1
            return f"{y}_{m:02d}"
        if c == "2":
            i = input("Enter YYYY_MM or YYYYMM: ").strip().replace("-", "_")
            if re.match(r"^\d{4}[-_]?\d{1,2}$", i):
                return f"{i[:4]}_{i[-2:].zfill(2)}"
        print("Invalid!")

def extract_blocked_events(html_file):
    try:
        soup = BeautifulSoup(open(html_file, encoding='utf-8'), 'html.parser')
        table = soup.find_all("table", class_="table")[-1]
        rows = table.find_all("tr")
        data = []
        for r in rows[1:]:
            cols = [c.get_text(strip=True) for c in r.find_all("td")]
            if len(cols) >= 5:
                data.append({"srcip":cols[1], "hostname":cols[2], "url":cols[3], "catdesc":cols[4]})
        return pd.DataFrame(data)
    except: return pd.DataFrame()

def clean_table(series, title, col1_name, col2_name="Count", top_n=10):
    if series.empty: return f"<h2>{title}</h2><p>No data</p>"
    df = series.head(top_n).to_frame(name=col2_name)
    df.index.name = col1_name
    df = df.reset_index()
    return f"<h2>{title}</h2>" + df.to_html(index=False, border=0, classes="table")

def generate_monthly_report():
    # Accept optional month argument (YYYYMM or YYYY_MM or YYYY-MM)
    if len(sys.argv) > 1:
        raw = sys.argv[1]
        target_month = raw.replace('-', '_') if '_' in raw or '-' in raw else f"{raw[:4]}_{raw[-2:]}"
    else:
        try:
            if sys.stdin and sys.stdin.isatty():
                target_month = get_month_from_user()
            else:
                d = datetime.now(); y, m = d.year, d.month - 1
                if m == 0: m, y = 12, y-1
                target_month = f"{y}_{m:02d}"
        except Exception:
            d = datetime.now(); y, m = d.year, d.month - 1
            if m == 0: m, y = 12, y-1
            target_month = f"{y}_{m:02d}"

    month_name = datetime.strptime(target_month, "%Y_%m").strftime("%B %Y")

    files = list(DAILY_REPORTS_FOLDER.glob(f"WebFilter_Blocked_{target_month.replace('_', '')}*.html"))
    if not files:
        print(f"\nNo daily reports found for {month_name}")
        print(f"Looking for: WebFilter_Blocked_{target_month.replace('_', '')}*.html")
        try:
            if sys.stdin and sys.stdin.isatty():
                input("\nPress Enter...")
        except Exception:
            pass
        return

    print(f"Found {len(files)} daily reports -> compiling {month_name}...")

    dfs = [extract_blocked_events(f) for f in files]
    df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    if df.empty:
        print("No blocked events found.")
        try:
            if sys.stdin and sys.stdin.isatty():
                input()
        except Exception:
            pass
        return

    total = len(df)
    top_cats = df['catdesc'].value_counts().head(10)
    top_domains = df['hostname'].value_counts().head(10)

    # PIE CHART → EMBEDDED IN HTML (NO PNG FILE!)
    plt.figure(figsize=(8,6))
    plt.pie(top_cats, labels=None, autopct=lambda p: f'{p:.1f}%' if p>=2 else '', startangle=90)
    plt.legend([f"{c} ({v:,})" for c,v in top_cats.items()], loc="center left", bbox_to_anchor=(1,0.5))
    plt.title(f"Top Blocked Categories - {month_name}")

    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    # ONE AND ONLY ONE HTML FILE PER MONTH — OVERWRITES AUTOMATICALLY
    report_file = MONTHLY_OUTPUT_FOLDER / f"WebFilter_Monthly_Report_{target_month}.html"

    html = f"""
    <html><head><meta charset="utf-8">
    <title>Web Filter Monthly Report - {month_name}</title>
    <style>
    body{{font-family:Arial;margin:40px;background:#f9f9f9;}}
    .c{{max-width:1300px;margin:auto;background:white;padding:30px;border-radius:12px;box-shadow:0 0 20px rgba(0,0,0,0.1);}}
    h1,h2{{color:#2c3e50;text-align:center;}}
    .stats{{font-size:1.5em;text-align:center;margin:30px;color:#e74c3c;}}
    table{{width:100%;border-collapse:collapse;margin:25px 0;}}
    th,td{{border:1px solid #ddd;padding:12px;}}
    th{{background:#f4f4f4;font-weight:bold;}}
    .table th {{ text-align: center; }}   /* ← THIS LINE CENTERS HEADER TEXT */
    .pie{{text-align:center;margin:50px 0;}}
    img{{max-width:100%;border:1px solid #ddd;border-radius:10px;}}
    </style>
    </head><body>
    <div class="c">
    <h1>Web Filter Events - Monthly Report</h1>
    <h2>{month_name}</h2>
    <div class="stats">Total Blocked Requests: <strong>{total:,}</strong></div><hr>

    <div style="display:flex;gap:30px;flex-wrap:wrap;">
        <div style="flex:1;min-width:380px;">
            {clean_table(top_cats, "Top 10 Web Filter Events by Category", "Category")}
        </div>
        <div style="flex:1;min-width:380px;">
            {clean_table(top_domains, "Top 10 Blocked Domains", "Domain")}
        </div>
    </div>

    <div class="pie">
        <h2>Top Blocked Categories Distribution</h2>
        <img src="data:image/png;base64,{img_base64}">
    </div>
    </div></body></html>
    """

    report_file.write_text(html, encoding='utf-8')
    print("\n" + "="*70)
    print(f"SUCCESS! Monthly report updated")
    print(f"-> {report_file}")
    print(f"-> Total blocked: {total:,}")
    print("   (Old report overwritten, no PNG file created)")
    print("="*70)
    try:
        if sys.stdin and sys.stdin.isatty():
            input("\nPress Enter to close...")
    except Exception:
        pass

if __name__ == "__main__":
    generate_monthly_report()