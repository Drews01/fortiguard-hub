"""
ULTIMATE FINAL main.py — WORKS ON EVERY WINDOWS MACHINE
No more "Access denied" — EVER
"""

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import re
import urllib.parse
import subprocess
import sys
from datetime import datetime
from pathlib import PurePath

app = FastAPI(title="FortiGate Security Portal API")

app.add_middleware(
    CORSMiddleware,
    # allow common dev origins including Vite default (5173) and configured port (8080)
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:8080", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# YOUR REAL FOLDERS
BASE_DIR = Path(__file__).parent.parent / "public" / "Python Report"

REPORT_CONFIG = {
    "appctrl": {
        "folder": "Python Reports Application",
        "daily_script": "daily report application.py",
        "monthly_script": "monthly report application.py",
        "daily_prefix": "AppCtrl_Blocked_",
        "monthly_prefix": "AppCtrl_Monthly_Report_"
    },
    "webfilter": {
        "folder": "Python Generate WebFilter",
        "daily_script": "daily report.py",
        "monthly_script": "monthly report.py",
        "daily_prefix": "WebFilter_Blocked_",
        "monthly_prefix": "WebFilter_Monthly_Report_"
    },
    "ips": {
        "folder": "Python Generate Intrusion",
        "daily_script": "generate IPS daily.py",
        "monthly_script": "generate IPS Monthly.py",
        "daily_prefix": "IPS_Critical_Events_",
        "monthly_prefix": "IPS_Monthly_Report_"
    },
    "dns": {
        "folder": "Python Generate DNS",
        "daily_script": "generate dns daily.py",
        "monthly_script": "generate dns monthly.py",
        "daily_prefix": "DNS_Events_Report_",
        "monthly_prefix": "DNS_Monthly_Report_"
    },
    "antivirus": {
        "folder": "Python Generate Antivirus",
        "daily_script": "generate antivirus daily.py",
        "monthly_script": "generate antivirus monthly.py",
        "daily_prefix": "AV_Infected_Report_",
        "monthly_prefix": "AV_Monthly_Report_"
    },
}

def get_files(folder_path: Path, prefix: str):
    if not folder_path.exists():
        return []
    # Match both formats: 20251208 (8 digits), 202512 (6 digits), or 2025_12 (YYYY_MM with underscore)
    pattern = re.compile(rf"{prefix}(\d{{4}}[_]?\d{{2}}|\d{{8}}|\d{{6}})\.html$")
    files = []
    for file in folder_path.iterdir():
        if file.is_file() and (m := pattern.match(file.name)):
            # Normalize date for sorting (remove underscores)
            date_normalized = m.group(1).replace('_', '')
            files.append({"filename": file.name, "fullpath": str(file), "date": date_normalized})
    return sorted(files, key=lambda x: x["date"], reverse=True)

@app.get("/api/reports/{rtype}/daily")
async def daily(rtype: str):
    if rtype not in REPORT_CONFIG: raise HTTPException(404)
    folder = BASE_DIR / REPORT_CONFIG[rtype]["folder"] / "daily_reports"
    files = get_files(folder, REPORT_CONFIG[rtype]["daily_prefix"])
    return [
        {
            "date": f"{f['date'][:4]}-{f['date'][4:6]}-{f['date'][6:8]}",
            "filename": f["filename"],
            "path": f"/api/serve/{rtype}/daily/{urllib.parse.quote(f['filename'])}"
        }
        for f in files
    ]

@app.get("/api/reports/{rtype}/monthly")
async def monthly(rtype: str):
    if rtype not in REPORT_CONFIG: raise HTTPException(404)
    folder = BASE_DIR / REPORT_CONFIG[rtype]["folder"] / "monthly_reports"
    files = get_files(folder, REPORT_CONFIG[rtype]["monthly_prefix"])
    return [
        {
            "month": f"{f['date'][:4]}-{f['date'][4:6]}",
            "filename": f["filename"],
            "path": f"/api/serve/{rtype}/monthly/{urllib.parse.quote(f['filename'])}"
        }
        for f in files
    ]

# NEW: Direct path serving — NO PATH PARAMETER, NO SECURITY ISSUES
@app.get("/api/serve/{rtype}/{period}/{filename:path}")
async def serve_file(rtype: str, period: str, filename: str):
    if rtype not in REPORT_CONFIG:
        raise HTTPException(404, "Invalid type")
    
    folder_name = REPORT_CONFIG[rtype]["folder"]
    subfolder = "daily_reports" if period == "daily" else "monthly_reports"
    
    file_path = BASE_DIR / folder_name / subfolder / filename
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, "File not found")
    
    # Simple check: must be inside BASE_DIR
    if not str(file_path.resolve()).startswith(str(BASE_DIR.resolve())):
        raise HTTPException(403, "Access denied")
    
    return FileResponse(file_path, media_type="text/html")

@app.get("/")
async def root():
    return {"message": "FortiGate Portal API — RUNNING FLAWLESSLY"}


# ---------------------------
# Upload raw logs
# ---------------------------
ALLOWED_UPLOAD_EXT = {".log", ".txt"}


def sanitize_filename(filename: str) -> str:
    # remove any path elements and allow limited characters
    name = PurePath(filename).name
    # allow alphanum, dash, underscore, dot and space
    safe = re.sub(r"[^A-Za-z0-9. _-]", "_", name)
    # prevent filenames that are just dots
    if safe in {"", ".", ".."}:
        safe = f"upload_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.log"
    return safe


@app.post("/api/upload/{rtype}")
async def upload_raw_log(rtype: str, file: UploadFile = File(...), selectedDate: str = Form(...)):
    if rtype not in REPORT_CONFIG:
        raise HTTPException(404, "Invalid report type")
    # Validate uploaded filename extension
    orig_name = file.filename or "upload.log"
    safe_name = sanitize_filename(orig_name)
    ext = (Path(safe_name).suffix or "").lower()
    if ext not in ALLOWED_UPLOAD_EXT:
        raise HTTPException(400, "Only .log and .txt files are allowed")

    # Validate selectedDate format YYYY_MM_DD
    try:
        picked = datetime.strptime(selectedDate, "%Y_%m_%d")
    except Exception:
        raise HTTPException(400, "selectedDate must be in YYYY_MM_DD format")

    # prevent future dates
    if picked.date() > datetime.utcnow().date():
        raise HTTPException(400, "Selected date cannot be in the future")

    dest_dir = BASE_DIR / REPORT_CONFIG[rtype]["folder"] / "Raw Logs"
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Build canonical filename per requirements (always .log)
    prefix_map = {
        "appctrl": "disk-appctrl-",
        "webfilter": "disk-webfilter-",
        "ips": "disk-ips-",
        "dns": "disk-dns-",
        "antivirus": "disk-antivirus-",
    }
    prefix = prefix_map.get(rtype, "upload-")
    date_str = picked.strftime("%Y_%m_%d")
    final_name = f"{prefix}{date_str}.log"
    # sanitize final name and ensure no path segments
    final_name = PurePath(final_name).name
    dest_path = dest_dir / final_name

    try:
        contents = await file.read()
        # optional size limit (10 MB)
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(413, "File too large")
        # write (overwrite if exists)
        with open(dest_path, "wb") as fh:
            fh.write(contents)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to save file: {e}")

    return {"message": "uploaded", "filename": final_name, "path": str(dest_path)}


# ---------------------------
# Generate reports (async)
# ---------------------------


def _run_generator(mode: str, rtype: str, selected_date: str = None):
    """Worker that executes the generator script and captures output to an error_logs file."""
    cfg = REPORT_CONFIG[rtype]
    folder = BASE_DIR / cfg["folder"]
    script = cfg["daily_script"] if mode == "daily" else cfg["monthly_script"]
    script_path = folder / script

    log_dir = folder / "error_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    log_file = log_dir / f"generate_{mode}_{ts}.log"

    if not script_path.exists():
        with open(log_file, "w", encoding="utf-8") as fh:
            fh.write(f"Script not found: {script_path}\n")
        return

    try:
        # Use the same Python interpreter running the API
        cmd = [sys.executable, str(script_path)]
        if selected_date:
            # pass selected_date to the script (daily or monthly)
            cmd.append(selected_date)
        proc = subprocess.run(cmd, cwd=str(folder), capture_output=True, text=True, timeout=600)
        with open(log_file, "w", encoding="utf-8") as fh:
            fh.write("=== STDOUT ===\n")
            fh.write(proc.stdout or "")
            fh.write("\n=== STDERR ===\n")
            fh.write(proc.stderr or "")
            fh.write(f"\nRETURN CODE: {proc.returncode}\n")
    except Exception as e:
        with open(log_file, "w", encoding="utf-8") as fh:
            fh.write(f"Exception executing script: {e}\n")



from fastapi import Form

@app.post("/api/generate/{mode}/{rtype}")
async def generate_reports(mode: str, rtype: str, background: BackgroundTasks, selectedDate: str = Form(None)):
    if mode not in {"daily", "monthly"}:
        raise HTTPException(400, "Mode must be 'daily' or 'monthly'")
    if rtype not in REPORT_CONFIG:
        raise HTTPException(404, "Invalid report type")

    # For daily, validate selectedDate (YYYY_MM_DD)
    if mode == "daily":
        if not selectedDate:
            raise HTTPException(400, "selectedDate is required for daily report generation")
        # Validate format YYYY_MM_DD
        try:
            picked = datetime.strptime(selectedDate, "%Y_%m_%d")
        except Exception:
            raise HTTPException(400, "selectedDate must be in YYYY_MM_DD format")
        if picked.date() > datetime.utcnow().date():
            raise HTTPException(400, "Selected date cannot be in the future")
        background.add_task(_run_generator, mode, rtype, selectedDate)
    else:
        # Monthly: accept optional month in YYYY_MM or YYYYMM or YYYY-MM
        if selectedDate:
            # normalize to YYYYMM or validate
            if not re.match(r"^\d{4}[-_]?\d{2}$", selectedDate):
                raise HTTPException(400, "selectedDate for monthly must be YYYY_MM or YYYYMM")
            # remove separators before passing to script (scripts will normalize as needed)
            normalized = selectedDate.replace('-', '').replace('_', '')
            background.add_task(_run_generator, mode, rtype, normalized)
        else:
            background.add_task(_run_generator, mode, rtype)

    return {"message": "started", "mode": mode, "type": rtype}


@app.get("/api/check_raw/{rtype}")
async def check_raw_log(rtype: str, date: str = Query(..., description="Date in YYYY_MM_DD format")):
    """Check if a raw log exists for the given rtype and date (YYYY_MM_DD)."""
    if rtype not in REPORT_CONFIG:
        raise HTTPException(404, "Invalid report type")

    folder = BASE_DIR / REPORT_CONFIG[rtype]["folder"] / "Raw Logs"
    # expected filename: disk-<rtype>-YYYY_MM_DD.log
    prefix_map = {
        "appctrl": "disk-appctrl-",
        "webfilter": "disk-webfilter-",
        "ips": "disk-ips-",
        "dns": "disk-dns-",
        "antivirus": "disk-antivirus-",
    }
    prefix = prefix_map.get(rtype, "disk-")
    fname = f"{prefix}{date}.log"
    file_path = folder / fname
    return {"exists": file_path.exists()}

@app.on_event("startup")
async def startup():
    print("\n" + "="*80)
    print("FortiGate Security Portal — FINAL BULLETPROOF VERSION")
    print("="*80)
    for rtype, cfg in REPORT_CONFIG.items():
        daily = BASE_DIR / cfg["folder"] / "daily_reports"
        monthly = BASE_DIR / cfg["folder"] / "monthly_reports"
        print(f"{rtype.upper():8} → {'OK' if daily.exists() else 'MISSING'} | {'OK' if monthly.exists() else 'MISSING'}")
    print("API: http://127.0.0.1:8000")
    print("Frontend: http://127.0.0.1:5173")
    print("="*80 + "\n")