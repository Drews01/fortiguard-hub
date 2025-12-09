import { Shield, Activity, Clock } from 'lucide-react';
import { ReportCard } from '@/components/ReportCard';
import { ReportType } from '@/lib/types';

const reportTypes: ReportType[] = ['appctrl', 'webfilter', 'ips', 'dns'];

export default function Dashboard() {
  const now = new Date();
  const formattedTime = now.toLocaleString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="min-h-screen bg-background">
      <div className="container py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Security Dashboard</h1>
              <p className="mt-1 text-muted-foreground">
                Monitor and analyze your FortiGate security reports
              </p>
            </div>
            <div className="flex items-center gap-2 rounded-lg bg-muted/50 px-4 py-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>{formattedTime}</span>
            </div>
          </div>
        </div>

        {/* Stats Banner */}
        <div className="mb-8 grid gap-4 sm:grid-cols-3">
          <div className="flex items-center gap-4 rounded-lg border bg-card p-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
              <Shield className="h-6 w-6 text-primary" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Total Report Types</p>
              <p className="text-2xl font-bold">4</p>
            </div>
          </div>
          <div className="flex items-center gap-4 rounded-lg border bg-card p-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
              <Activity className="h-6 w-6 text-primary" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">System Status</p>
              <p className="text-2xl font-bold text-dns">Active</p>
            </div>
          </div>
          <div className="flex items-center gap-4 rounded-lg border bg-card p-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
              <Clock className="h-6 w-6 text-primary" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Last Update</p>
              <p className="text-2xl font-bold">Today</p>
            </div>
          </div>
        </div>

        {/* Report Cards */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {reportTypes.map((type) => (
            <ReportCard key={type} type={type} />
          ))}
        </div>

        {/* Info Banner */}
        <div className="mt-8 rounded-lg border border-primary/20 bg-primary/5 p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
            <div className="flex-1">
              <h3 className="font-semibold">Demo Mode Active</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                This dashboard is running in demo mode. Connect your FastAPI backend to view actual FortiGate reports.
              </p>
            </div>
            <div className="flex-shrink-0">
              <a
                href="#backend-setup"
                className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
              >
                View Setup Guide
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
