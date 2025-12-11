# FortiGate Security Portal - Backend

This is the Python FastAPI backend for the FortiGate Security Portal.

## Quick Start

1. **Install Python dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure your report paths:**
   
   Edit `main.py` and update the `REPORT_PATHS` dictionary with your actual folder paths:
   
   ```python
   REPORT_PATHS = {
       "appctrl": {
           "base": r"C:\Your\Actual\Path\AppControl",
           ...
       },
       # ... other report types
   }
   ```

3. **Run the server:**
   ```bash
   uvicorn main:app --reload --host 127.0.0.1 --port 8000 ## For BackEnd
   python -m uvicorn main:app --reload --port 8000 ##For Backend
   npm run dev ## For FrontEnd
   ```

4. **Enable the frontend connection:**
   
   In `src/lib/api.ts`, change:
   ```typescript
   const DEMO_MODE = false;  // Was true
   ```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Health check |
| `GET /api/reports/{type}/daily` | List daily reports |
| `GET /api/reports/{type}/monthly` | List monthly reports |
| `GET /api/file?path=...` | Serve HTML file |
| `GET /api/summary/{type}` | Get report summary |

Where `{type}` is one of: `appctrl`, `webfilter`, `ips`, `dns`

## API Documentation

Once running, visit: http://127.0.0.1:8000/docs

## Security

- Only serves files from configured directories
- Prevents directory traversal attacks
- Only allows .html files
- Runs on localhost only (127.0.0.1)

## Expected File Structure

```
C:\FortiGate\
├── AppControl\
│   ├── daily_reports\
│   │   └── AppCtrl_Blocked_20251208.html
│   └── monthly_reports\
│       └── AppCtrl_Monthly_Report_202512.html
├── WebFilter\
│   ├── daily_reports\
│   └── monthly_reports\
├── IPS\
│   ├── daily_reports\
│   └── monthly_reports\
└── DNS\
    ├── daily_reports\
    └── monthly_reports\
```
