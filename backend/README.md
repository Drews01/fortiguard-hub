# FortiGate Security Portal

A React + Vite frontend with a FastAPI backend to browse FortiGate HTML reports (Application Control, Web Filter, IPS, DNS).

## Quickstart — Dependencies & Run

Frontend
1. Install Node.js (v16+) and npm.
2. From project root:
   ```sh
   npm install
   npm run dev
   ```
   - Dev server defaults to port 8080 (see [vite.config.ts](vite.config.ts)).
   - Frontend scripts are in [package.json](package.json).

Backend
1. Install Python 3.9+ and pip.
2. From the `backend` folder:
   ```sh
   pip install -r requirements.txt
   uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```
   - API server runs on port 8000 (see [backend/main.py](backend/main.py)).
   - Backend README: [backend/README.md](backend/README.md).

Connecting Frontend ↔ Backend
- Frontend expects API at `http://127.0.0.1:8000/api` (see [`API_BASE`](src/lib/api.ts)).
- Demo mode: set [`DEMO_MODE`](src/lib/api.ts) to `false` to enable backend integration. See [`getReportFileUrl`](src/lib/api.ts) and [`downloadReport`](src/lib/api.ts).

## Ports

- Frontend dev server: 8080 — configured in [vite.config.ts](vite.config.ts).
- Backend API: 8000 — configured when running uvicorn and used by frontend via [`API_BASE`](src/lib/api.ts).
- CORS allowed origins configured in [backend/main.py](backend/main.py).

## Folder / File Overview

- [src/](src/) — React frontend source
  - [src/main.tsx](src/main.tsx) — app entry.
  - [src/App.tsx](src/App.tsx) — router and top-level providers.
  - [src/pages/](src/pages/) — page views
    - [src/pages/Dashboard.tsx](src/pages/Dashboard.tsx) — main dashboard.
    - [src/pages/ReportBrowser.tsx](src/pages/ReportBrowser.tsx) — list/select reports.
    - [src/pages/NotFound.tsx](src/pages/NotFound.tsx) — 404 page.
  - [src/components/](src/components/) — UI components
    - [src/components/ReportCard.tsx](src/components/ReportCard.tsx) — summary cards on dashboard.
    - [src/components/ReportViewer.tsx](src/components/ReportViewer.tsx) — iframe preview + download/fullscreen.
    - [src/components/DatePicker.tsx](src/components/DatePicker.tsx) — date picker used in report browser.
  - [src/lib/](src/lib/) — app utilities & API helpers
    - [src/lib/api.ts](src/lib/api.ts) — frontend API helpers: [`fetchDailyReports`](src/lib/api.ts), [`fetchMonthlyReports`](src/lib/api.ts), [`fetchReportSummary`](src/lib/api.ts), [`getReportFileUrl`](src/lib/api.ts), [`downloadReport`](src/lib/api.ts), and [`DEMO_MODE`](src/lib/api.ts).
    - [src/lib/types.ts](src/lib/types.ts) — shared TypeScript types like `ReportType`.
  - [src/components/ui/](src/components/ui/) — shared primitives (Radix wrappers, toaster, popover, etc.)
  - [src/index.css](src/index.css) — global styles and design tokens.
- [backend/](backend/) — FastAPI server
  - [backend/main.py](backend/main.py) — endpoints:
    - [`get_daily_reports`](backend/main.py) — lists daily files.
    - [`get_monthly_reports`](backend/main.py) — lists monthly files.
    - [`get_file`](backend/main.py) — serves HTML file securely.
    - [`get_report_summary`](backend/main.py) — aggregated counts.
    - Security helpers: [`get_allowed_paths`](backend/main.py), [`is_path_allowed`](backend/main.py).
  - [backend/requirements.txt](backend/requirements.txt) — Python dependencies.
  - [backend/README.md](backend/README.md) — backend setup docs.

Other
- [public/](public/) — static public assets.
- [index.html](index.html) — SPA HTML.
- [tailwind.config.ts](tailwind.config.ts) — Tailwind config.
- [vite.config.ts](vite.config.ts) — Vite config (port and alias).
- [eslint.config.js](eslint.config.js), [tsconfig.json](tsconfig.json) — tooling config.

## How it works (high level)

- Frontend fetches report lists via functions in [src/lib/api.ts](src/lib/api.ts) (e.g., [`fetchDailyReports`](src/lib/api.ts)).
- Report files are either served by the backend endpoint [`get_file`](backend/main.py) or demo HTML is shown when [`DEMO_MODE`](src/lib/api.ts) is `true`.
- Backend scans configured filesystem paths (see `REPORT_PATHS` in [backend/main.py](backend/main.py)) and enforces directory restrictions via [`get_allowed_paths`](backend/main.py) / [`is_path_allowed`](backend/main.py).

## Important Notes & Security

- Backend only serves `.html` files and validates file paths to avoid traversal (see security checks in [backend/main.py](backend/main.py)).
- Update `REPORT_PATHS` in [backend/main.py](backend/main.py) to match your local FortiGate export directories before running the backend.
- To enable real data in the frontend, set [`DEMO_MODE`](src/lib/api.ts) to `false` and run the backend.

## Build / Production

- Frontend: run `npm run build` (see [package.json](package.json)) and deploy the `dist` output to your static hosting.
- Backend: run `uvicorn main:app --host 0.0.0.0 --port 8000` (or configure a production ASGI server).

## Troubleshooting

- If frontend cannot reach API: ensure backend is running on 127.0.0.1:8000 and [`DEMO_MODE`](src/lib/api.ts) is `false`.
- Check backend startup logs for missing configured paths (printed by [backend/main.py](backend/main.py) on startup).

## References

- Frontend entry: [src/main.tsx](src/main.tsx)  
- Frontend router: [src/App.tsx](src/App.tsx)  
- API helpers: [src/lib/api.ts](src/lib/api.ts) — see [`DEMO_MODE`](src/lib/api.ts) and [`API_BASE`](src/lib/api.ts)  
- Backend: [backend/main.py](backend/main.py) and [backend/README.md](backend/README.md)