# FortiGuard Hub — FortiGate Security Portal

This repository contains a React + Vite + Tailwind + shadcn/ui frontend and a FastAPI backend
for viewing FortiGate-generated HTML reports. It supports four report types: Application Control,
Web Filter, IPS, and DNS. The frontend serves static report files from `public/Python Report/...`
and the backend provides secure upload and asynchronous report generation endpoints.

## Repository layout (relevant)

- `public/Python Report/` — contains the per-report-type folders and generated HTML files
	- `Python Generate WebFilter/`
	- `Python Generate DNS/`
	- `Python Generate Intrusion/`
	- `Python Reports Application/`
	Each of those folders should contain:
	- `generate_daily.py` (generator script)
	- `generate_monthly.py`
	- `Raw Logs/` (where uploaded raw logs are stored)
	- `daily_reports/` (generated daily HTML files)
	- `monthly_reports/` (generated monthly HTML files)

## New features added

1. Upload Raw Logs
	 - Frontend: Dashboard card `Upload Raw Logs` (shadcn/ui)
	 - Endpoint: `POST /api/upload/{type}`
		 - Accepts `multipart/form-data` file field named `file`.
		 - Allowed extensions: `.log`, `.txt`.
		 - Server sanitizes filename, prefixes with UTC timestamp, enforces size limit (10 MB),
			 and saves to `public/Python Report/<folder>/Raw Logs/`.
		 - Returns JSON `{ message: 'uploaded', filename, path }` on success.

2. Generate Reports
	 - Frontend: Dashboard card `Generate Reports` with Daily/Monthly mode and type selector.
	 - Endpoint: `POST /api/generate/{mode}/{type}` where `mode` is `daily` or `monthly`.
		 - The server schedules an asynchronous background task that executes the matching
			 script (`generate_daily.py` or `generate_monthly.py`) using the same Python interpreter
			 that runs FastAPI (no shell execution), with `cwd` set to the report folder.
		 - The process stdout/stderr and return code are captured and written to
			 `public/Python Report/<folder>/error_logs/generate_{mode}_{timestamp}.log`.
		 - The endpoint returns quickly with `{ message: 'started', mode, type }`.

## Running locally

1. Install backend dependencies and start FastAPI (from project root `backend/`):

```pwsh
# inside c:\Users\Andrew\Desktop\Python Dashboard\fortiguard-hub\backend
pip install fastapi uvicorn
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

2. Install frontend deps and run Vite (project root):

```pwsh
npm install
npm run dev
```

3. Open the frontend in your browser (default Vite port 5173) and navigate to the Dashboard.

## Endpoints

- `GET /api/reports/{type}/daily` — lists available daily reports (JSON)
- `GET /api/reports/{type}/monthly` — lists available monthly reports (JSON)
- `GET /api/serve/{type}/{period}/{filename}` — serves an HTML report file (safe path)
- `POST /api/upload/{type}` — upload raw log (`multipart/form-data` `file`)
- `POST /api/generate/{mode}/{type}` — start generation (`mode`=`daily`|`monthly`)

Example: upload a webfilter log

```pwsh
curl -F "file=@C:\path\to\my.log" http://127.0.0.1:8000/api/upload/webfilter
```

Start a daily generation for DNS:

```pwsh
curl -X POST http://127.0.0.1:8000/api/generate/daily/dns
```

## Security notes

- Filename sanitization: server strips path components and unsafe characters.
- Extension whitelist: only `.log` and `.txt` uploads are accepted.
- Size limits: uploads are capped (default 10 MB).
- Script execution: generators are executed without a shell using `subprocess.run([sys.executable, script])` and with `cwd` set to the report folder to prevent command injection.
- The backend writes generator output to `error_logs/` for audit and troubleshooting.

## Troubleshooting

- If the frontend shows `{"detail":"Not Found"}` when opening a report, ensure the backend is running and that generator-created HTML files exist in the expected `daily_reports/` or `monthly_reports/` folders.
- Check backend logs printed on startup — the server will report which report folders were found or missing.
- Inspect `public/Python Report/<folder>/error_logs/` for generator stdout/stderr logs.

## Next steps / optional improvements

- Add an authenticated admin UI to view and download `error_logs` and recent uploads.
- Implement a job queue (Redis + RQ or Celery) for better generation reliability, retries, and visibility.
- Add rate limiting and authentication to the upload/generate endpoints for production use.

---

If you want, I can also add README examples for CI/deployment, or wire up a small admin panel to view generator logs directly in the UI.
