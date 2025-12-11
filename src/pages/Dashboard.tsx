import { Shield, Activity, Clock } from 'lucide-react';
import { ReportCard } from '@/components/ReportCard';
import { ReportType } from '@/lib/types';
import { useState, ChangeEvent } from 'react';
import { Upload, PlayCircle, RefreshCw } from 'lucide-react';
import { DatePicker } from '@/components/DatePicker';
import { MonthSelector } from '@/components/MonthSelector';
import { format } from 'date-fns';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from '@/hooks/use-toast';

// Helper: generate an array of past months in 'YYYY-MM' format
function generateAvailableMonths(count = 18, startOffset = 1) {
  const out: string[] = [];
  for (let i = 0; i < count; i++) {
    const d = new Date();
    // startOffset=1 means start from previous month
    d.setMonth(d.getMonth() - (i + startOffset));
    out.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`);
  }
  return out;
}

const API_BASE = 'http://127.0.0.1:8000/api';

const reportTypes: ReportType[] = ['appctrl', 'webfilter', 'ips', 'dns'];

function UploadCard() {
  const [type, setType] = useState<ReportType | undefined>('webfilter');
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(yesterday);
  const [selectedMonth, setSelectedMonth] = useState<string | undefined>(() => {
    const d = new Date(); d.setMonth(d.getMonth() - 1);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
  });
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    if (!f) return setFile(null);
    const ext = f.name.split('.').pop()?.toLowerCase() ?? '';
    if (!['log', 'txt'].includes(ext)) {
      setFile(null);
      toast({ title: 'Invalid file', description: 'Only .log and .txt files are allowed', variant: 'destructive' });
      return;
    }
    setFile(f);
  };

  const handleUpload = async () => {
    if (!type) return toast({ title: 'Select type', description: 'Choose a report type first', variant: 'destructive' });
    if (!file) return toast({ title: 'No file', description: 'Choose a .log or .txt file to upload', variant: 'destructive' });
    if (!selectedDate) return toast({ title: 'Select date', description: 'Pick a date for this log', variant: 'destructive' });
    // Prevent future dates
    const today = new Date();
    const picked = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate());
    const nowDate = new Date(today.getFullYear(), today.getMonth(), today.getDate());
    if (picked > nowDate) return toast({ title: 'Invalid date', description: 'Selected date cannot be in the future', variant: 'destructive' });

    setUploading(true);
    try {
      const form = new FormData();
      form.append('file', file, file.name);
      const formatted = format(selectedDate, 'yyyy_MM_dd');
      form.append('selectedDate', formatted);
      const res = await fetch(`${API_BASE}/upload/${type}`, { method: 'POST', body: form });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || res.statusText);
      }
      const data = await res.json();
      toast({ title: 'Upload complete', description: `Uploaded as ${data.filename}` });
      setFile(null);
      (document.getElementById('raw-upload-input') as HTMLInputElement | null)?.value && ((document.getElementById('raw-upload-input') as HTMLInputElement).value = '');
    } catch (e: any) {
      toast({ title: 'Upload failed', description: e?.message || 'Unknown error', variant: 'destructive' });
    } finally {
      setUploading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Upload className="h-5 w-5 text-primary" />
          <CardTitle>Upload Raw Logs</CardTitle>
        </div>
        <CardDescription>Upload .log or .txt raw logs into the selected report folder.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3">
          <Select value={type} onValueChange={(v) => setType(v as ReportType)}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select report type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="webfilter">Web Filter</SelectItem>
              <SelectItem value="dns">DNS</SelectItem>
              <SelectItem value="ips">IPS</SelectItem>
              <SelectItem value="appctrl">Application Control</SelectItem>
            </SelectContent>
          </Select>

          <div>
            <DatePicker date={selectedDate} onDateChange={setSelectedDate} />
          </div>

          <div className="text-sm text-muted-foreground">Will be saved as: <span className="font-mono">{type && selectedDate ? `${({appctrl:'disk-appctrl-',webfilter:'disk-webfilter-',ips:'disk-ips-',dns:'disk-dns-' } as any)[type]}${selectedDate ? format(selectedDate,'yyyy_MM_dd') : 'YYYY_MM_DD'}.log` : '—'}</span></div>

          <div className="flex items-center gap-3">
            <input id="raw-upload-input" type="file" accept=".log,.txt" onChange={handleFileChange} className="hidden" />
            <label htmlFor="raw-upload-input">
              <Button variant="outline" asChild>
                <span className="flex items-center gap-2"><Upload /> Choose File</span>
              </Button>
            </label>
            <div className="flex-1 text-sm text-muted-foreground">{file ? file.name : 'No file selected'}</div>
            <Button onClick={handleUpload} disabled={uploading}>
              {uploading ? 'Uploading…' : 'Upload'}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function GenerateCard() {
  const [mode, setMode] = useState<'daily' | 'monthly' | null>(null);
  const [type, setType] = useState<ReportType | undefined>('webfilter');
  const [running, setRunning] = useState(false);
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(yesterday);
  const availableMonths = generateAvailableMonths(18, 1);
  const [selectedMonth, setSelectedMonth] = useState<string | undefined>(availableMonths[0]);

  const startGeneration = async () => {
    if (!mode) return toast({ title: 'Select mode', description: 'Choose Daily or Monthly first', variant: 'destructive' });
    if (!type) return toast({ title: 'Select type', description: 'Choose a report type', variant: 'destructive' });
    if (mode === 'daily' && !selectedDate) return toast({ title: 'Select date', description: 'Pick a date for this report', variant: 'destructive' });
    if (mode === 'daily' && selectedDate) {
      const today = new Date();
      const picked = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate());
      const nowDate = new Date(today.getFullYear(), today.getMonth(), today.getDate());
      if (picked > nowDate) return toast({ title: 'Invalid date', description: 'Selected date cannot be in the future', variant: 'destructive' });
    }

    setRunning(true);
    try {
      let res;
      if (mode === 'daily') {
        const form = new FormData();
        form.append('selectedDate', format(selectedDate!, 'yyyy_MM_dd'));
        res = await fetch(`${API_BASE}/generate/daily/${type}`, { method: 'POST', body: form });
      } else {
        const form = new FormData();
        // MonthSelector returns YYYY-MM; backend accepts YYYYMM or YYYY_MM. Send compact YYYYMM.
        form.append('selectedDate', (selectedMonth || '').replace(/-/g, ''));
        res = await fetch(`${API_BASE}/generate/monthly/${type}`, { method: 'POST', body: form });
      }
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || res.statusText);
      }
      const data = await res.json();
      toast({ title: 'Generation started', description: `${mode.charAt(0).toUpperCase() + mode.slice(1)} ${type} generation started` });
    } catch (e: any) {
      toast({ title: 'Generation failed', description: e?.message || 'Unknown error', variant: 'destructive' });
    } finally {
      setRunning(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <PlayCircle className="h-5 w-5 text-primary" />
          <CardTitle>Generate Reports</CardTitle>
        </div>
        <CardDescription>Run report generation scripts (daily or monthly) in the correct folder.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2">
            <Button variant={mode === 'daily' ? 'default' : 'ghost'} onClick={() => setMode('daily')}>Daily Reports</Button>
            <Button variant={mode === 'monthly' ? 'default' : 'ghost'} onClick={() => setMode('monthly')}>Monthly Reports</Button>
            <div className="ml-auto text-sm text-muted-foreground">{mode ? `${mode.toUpperCase()} mode selected` : 'Select mode'}</div>
          </div>

          <Select value={type} onValueChange={(v) => setType(v as ReportType)}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select report type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="webfilter">Web Filter</SelectItem>
              <SelectItem value="dns">DNS</SelectItem>
              <SelectItem value="ips">IPS</SelectItem>
              <SelectItem value="appctrl">Application Control</SelectItem>
            </SelectContent>
          </Select>

          {mode === 'daily' && (
            <div>
              <DatePicker date={selectedDate} onDateChange={setSelectedDate} />
              <div className="text-sm text-muted-foreground mt-1">Generate report for: <span className="font-mono">{selectedDate ? format(selectedDate, 'yyyy_MM_dd') : 'YYYY_MM_DD'}</span></div>
            </div>
          )}
          {mode === 'monthly' && (
            <div>
              <MonthSelector value={selectedMonth} onValueChange={(v) => setSelectedMonth(v)} availableMonths={availableMonths} />
              <div className="text-sm text-muted-foreground mt-1">Generate month: <span className="font-mono">{selectedMonth ?? 'YYYY-MM'}</span></div>
            </div>
          )}

          <div className="flex items-center gap-2">
            <Button onClick={startGeneration} disabled={running || !mode}>
              <RefreshCw className="h-4 w-4 mr-2" /> {running ? 'Starting…' : 'Generate'}
            </Button>
            <div className="text-sm text-muted-foreground">This runs the generator script in the report folder asynchronously.</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

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

        {/* Action Cards */}
        <div className="mt-8 grid gap-6 sm:grid-cols-1 lg:grid-cols-2">
          <UploadCard />
          <GenerateCard />
        </div>

        {/* Coba */}
        
        {/* Coba End */}

      </div>
    </div>
  );
}
