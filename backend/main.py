"""
FortiGate Security Portal - FastAPI Backend

This is the Python FastAPI backend for the FortiGate Security Portal.
It serves HTML report files from your local file system.

SETUP:
1. Install dependencies:
   pip install fastapi uvicorn

2. Configure your report paths below (REPORT_PATHS)

3. Run the server:
   uvicorn main:app --reload --host 127.0.0.1 --port 8000

4. Update the React frontend's DEMO_MODE to False in src/lib/api.ts
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import os
import re
from typing import List, Dict, Optional
from datetime import datetime

app = FastAPI(
    title="FortiGate Security Portal API",
    description="API for serving FortiGate security reports",
    version="1.0.0"
)

# CORS configuration - allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080", "http://127.0.0.1:5173", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# CONFIGURE YOUR REPORT PATHS HERE
# ============================================================================
# Update these paths to match your actual folder structure

REPORT_PATHS = {
    "appctrl": {
        "base": r"C:\FortiGate\AppControl",  # Change this to your actual path
        "daily": "daily_reports",
        "monthly": "monthly_reports",
        "daily_pattern": r"AppCtrl_Blocked_(\d{8})\.html",
        "monthly_pattern": r"AppCtrl_Monthly_Report_(\d{6})\.html",
    },
    "webfilter": {
        "base": r"C:\FortiGate\WebFilter",
        "daily": "daily_reports",
        "monthly": "monthly_reports",
        "daily_pattern": r"WebFilter_Blocked_(\d{8})\.html",
        "monthly_pattern": r"WebFilter_Monthly_Report_(\d{6})\.html",
    },
    "ips": {
        "base": r"C:\FortiGate\IPS",
        "daily": "daily_reports",
        "monthly": "monthly_reports",
        "daily_pattern": r"IPS_Blocked_(\d{8})\.html",
        "monthly_pattern": r"IPS_Monthly_Report_(\d{6})\.html",
    },
    "dns": {
        "base": r"C:\FortiGate\DNS",
        "daily": "daily_reports",
        "monthly": "monthly_reports",
        "daily_pattern": r"DNS_Blocked_(\d{8})\.html",
        "monthly_pattern": r"DNS_Monthly_Report_(\d{6})\.html",
    },
}

# ============================================================================
# SECURITY: Validate paths to prevent directory traversal
# ============================================================================

def get_allowed_paths() -> List[Path]:
    """Get list of all allowed base paths"""
    paths = []
    for config in REPORT_PATHS.values():
        base = Path(config["base"])
        paths.append(base / config["daily"])
        paths.append(base / config["monthly"])
    return paths

def is_path_allowed(file_path: Path) -> bool:
    """Check if a file path is within allowed directories"""
    try:
        file_path = file_path.resolve()
        for allowed in get_allowed_paths():
            try:
                allowed = allowed.resolve()
                file_path.relative_to(allowed)
                return True
            except ValueError:
                continue
        return False
    except Exception:
        return False

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "FortiGate Security Portal API"}


@app.get("/api/reports/{report_type}/daily")
async def get_daily_reports(report_type: str) -> List[Dict]:
    """Get list of available daily reports for a report type"""
    if report_type not in REPORT_PATHS:
        raise HTTPException(status_code=404, detail=f"Unknown report type: {report_type}")
    
    config = REPORT_PATHS[report_type]
    daily_path = Path(config["base"]) / config["daily"]
    
    if not daily_path.exists():
        return []
    
    pattern = re.compile(config["daily_pattern"])
    reports = []
    
    for file in daily_path.glob("*.html"):
        match = pattern.match(file.name)
        if match:
            date_str = match.group(1)
            # Convert YYYYMMDD to YYYY-MM-DD
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            reports.append({
                "date": formatted_date,
                "filename": file.name,
                "path": str(file.resolve()),
            })
    
    # Sort by date descending
    reports.sort(key=lambda x: x["date"], reverse=True)
    return reports


@app.get("/api/reports/{report_type}/monthly")
async def get_monthly_reports(report_type: str) -> List[Dict]:
    """Get list of available monthly reports for a report type"""
    if report_type not in REPORT_PATHS:
        raise HTTPException(status_code=404, detail=f"Unknown report type: {report_type}")
    
    config = REPORT_PATHS[report_type]
    monthly_path = Path(config["base"]) / config["monthly"]
    
    if not monthly_path.exists():
        return []
    
    pattern = re.compile(config["monthly_pattern"])
    reports = []
    
    for file in monthly_path.glob("*.html"):
        match = pattern.match(file.name)
        if match:
            month_str = match.group(1)
            # Convert YYYYMM to YYYY-MM
            formatted_month = f"{month_str[:4]}-{month_str[4:6]}"
            reports.append({
                "month": formatted_month,
                "filename": file.name,
                "path": str(file.resolve()),
            })
    
    # Sort by month descending
    reports.sort(key=lambda x: x["month"], reverse=True)
    return reports


@app.get("/api/file")
async def get_file(path: str = Query(..., description="Full path to the HTML file")):
    """Serve an HTML report file securely"""
    file_path = Path(path)
    
    # Security check
    if not is_path_allowed(file_path):
        raise HTTPException(
            status_code=403,
            detail="Access denied: File is not in an allowed directory"
        )
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not file_path.suffix.lower() == ".html":
        raise HTTPException(status_code=400, detail="Only HTML files are allowed")
    
    return FileResponse(
        path=str(file_path),
        media_type="text/html",
        filename=file_path.name
    )


@app.get("/api/summary/{report_type}")
async def get_report_summary(report_type: str) -> Dict:
    """Get a summary of available reports for a report type"""
    daily = await get_daily_reports(report_type)
    monthly = await get_monthly_reports(report_type)
    
    return {
        "type": report_type,
        "daily_count": len(daily),
        "monthly_count": len(monthly),
        "latest_daily": daily[0]["date"] if daily else None,
        "latest_monthly": monthly[0]["month"] if monthly else None,
    }


# ============================================================================
# STARTUP INFO
# ============================================================================

@app.on_event("startup")
async def startup_event():
    print("\n" + "=" * 60)
    print("FortiGate Security Portal API")
    print("=" * 60)
    print("\nConfigured report paths:")
    for name, config in REPORT_PATHS.items():
        base = Path(config["base"])
        daily = base / config["daily"]
        monthly = base / config["monthly"]
        print(f"\n  {name.upper()}:")
        print(f"    Daily:   {daily} {'✓' if daily.exists() else '✗ (not found)'}")
        print(f"    Monthly: {monthly} {'✓' if monthly.exists() else '✗ (not found)'}")
    print("\n" + "=" * 60)
    print("API running at: http://127.0.0.1:8000")
    print("API docs at:    http://127.0.0.1:8000/docs")
    print("=" * 60 + "\n")
