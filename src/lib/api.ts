import { ReportType, DailyReport, MonthlyReport, ReportSummary } from './types';

const API_BASE = 'http://127.0.0.1:8000/api';

// Mock data for demo - replace with actual API calls when backend is running
const generateMockDates = (count: number): string[] => {
  const dates: string[] = [];
  const today = new Date();
  for (let i = 0; i < count; i++) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    dates.push(date.toISOString().split('T')[0]);
  }
  return dates;
};

const generateMockMonths = (count: number): string[] => {
  const months: string[] = [];
  const today = new Date();
  for (let i = 0; i < count; i++) {
    const date = new Date(today);
    date.setMonth(date.getMonth() - i);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    months.push(`${year}-${month}`);
  }
  return months;
};

const MOCK_DAILY_DATES = generateMockDates(30);
const MOCK_MONTHLY_MONTHS = generateMockMonths(6);

// Demo mode flag - set to false when backend is running
const DEMO_MODE = false;

export async function fetchDailyReports(type: ReportType): Promise<DailyReport[]> {
  if (DEMO_MODE) {
    return MOCK_DAILY_DATES.map(date => ({
      date,
      filename: `${type.toUpperCase()}_Blocked_${date.replace(/-/g, '')}.html`,
      path: `/${type}/daily_reports/${type.toUpperCase()}_Blocked_${date.replace(/-/g, '')}.html`,
    }));
  }

  try {
    const response = await fetch(`${API_BASE}/reports/${type}/daily`);
    if (!response.ok) throw new Error('Failed to fetch daily reports');
    return response.json();
  } catch (error) {
    console.error('Error fetching daily reports:', error);
    return [];
  }
}

export async function fetchMonthlyReports(type: ReportType): Promise<MonthlyReport[]> {
  if (DEMO_MODE) {
    return MOCK_MONTHLY_MONTHS.map(month => ({
      month,
      filename: `${type.toUpperCase()}_Monthly_Report_${month.replace('-', '')}.html`,
      path: `/${type}/monthly_reports/${type.toUpperCase()}_Monthly_Report_${month.replace('-', '')}.html`,
    }));
  }

  try {
    const response = await fetch(`${API_BASE}/reports/${type}/monthly`);
    if (!response.ok) throw new Error('Failed to fetch monthly reports');
    return response.json();
  } catch (error) {
    console.error('Error fetching monthly reports:', error);
    return [];
  }
}

export async function fetchReportSummary(type: ReportType): Promise<ReportSummary> {
  const [daily, monthly] = await Promise.all([
    fetchDailyReports(type),
    fetchMonthlyReports(type),
  ]);

  return {
    dailyCount: daily.length,
    monthlyCount: monthly.length,
    latestDailyDate: daily[0]?.date || null,
    latestMonthlyDate: monthly[0]?.month || null,
  };
}

export function getReportFileUrl(path: string): string {
  if (DEMO_MODE) {
    // In demo mode, return a placeholder
    return '';
  }
  // If the backend already returned an API serving path (e.g. "/api/serve/.."),
  // build a full URL using the same host as API_BASE. Otherwise fall back
  // to the legacy file endpoint format.
  try {
    if (path.startsWith('/api/')) {
      // API_BASE contains the trailing '/api' segment; replace it with host
      const host = API_BASE.replace(/\/api$/, '');
      return `${host}${path}`;
    }
  } catch (e) {
    // ignore and fall back
  }

  return `${API_BASE}/file?path=${encodeURIComponent(path)}`;
}

export async function downloadReport(path: string, filename: string): Promise<void> {
  if (DEMO_MODE) {
    alert('Download feature requires the FastAPI backend to be running.');
    return;
  }

  try {
    const response = await fetch(getReportFileUrl(path));
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    console.error('Error downloading report:', error);
  }
}