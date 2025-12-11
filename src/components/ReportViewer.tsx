import { useState, useRef } from 'react';
import { Maximize2, Minimize2, Download, ExternalLink, FileX } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { getReportFileUrl, downloadReport } from '@/lib/api';
import { cn } from '@/lib/utils';

interface ReportViewerProps {
  path: string | null;
  filename: string;
  type: 'appctrl' | 'webfilter' | 'ips' | 'dns';
}

const DEMO_HTML = `
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: 'Segoe UI', sans-serif; padding: 40px; background: #f8f9fa; color: #333; }
    .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    h1 { color: #1a1a2e; margin-bottom: 8px; }
    .subtitle { color: #666; margin-bottom: 30px; }
    .stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }
    .stat-card { background: #f0f4f8; padding: 20px; border-radius: 8px; text-align: center; }
    .stat-value { font-size: 32px; font-weight: bold; color: #1a1a2e; }
    .stat-label { font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-top: 8px; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
    th { background: #f8f9fa; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: #666; }
    .badge { display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: 500; }
    .badge-blocked { background: #fee2e2; color: #dc2626; }
    .badge-allowed { background: #dcfce7; color: #16a34a; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Security Report Demo</h1>
    <p class="subtitle">This is a demo preview. Connect your FastAPI backend to view actual reports.</p>
    
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-value">1,247</div>
        <div class="stat-label">Total Events</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">892</div>
        <div class="stat-label">Blocked</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">355</div>
        <div class="stat-label">Allowed</div>
      </div>
    </div>

    <h3>Top Blocked Items</h3>
    <table>
      <thead>
        <tr>
          <th>Item</th>
          <th>Category</th>
          <th>Count</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>BitTorrent</td>
          <td>P2P</td>
          <td>234</td>
          <td><span class="badge badge-blocked">Blocked</span></td>
        </tr>
        <tr>
          <td>gaming-site.com</td>
          <td>Gaming</td>
          <td>156</td>
          <td><span class="badge badge-blocked">Blocked</span></td>
        </tr>
        <tr>
          <td>social-media.app</td>
          <td>Social</td>
          <td>89</td>
          <td><span class="badge badge-allowed">Allowed</span></td>
        </tr>
      </tbody>
    </table>
  </div>
</body>
</html>
`;

export function ReportViewer({ path, filename, type }: ReportViewerProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [loading, setLoading] = useState(true);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const reportUrl = path ? getReportFileUrl(path) : '';
  const isDemo = !reportUrl;

  const handleFullscreen = () => {
    if (iframeRef.current) {
      if (!isFullscreen) {
        iframeRef.current.requestFullscreen?.();
      } else {
        document.exitFullscreen?.();
      }
      setIsFullscreen(!isFullscreen);
    }
  };

  const handleDownload = () => {
    if (path) {
      downloadReport(path, filename);
    }
  };

  const colorClasses = {
    appctrl: 'border-appctrl/30',
    webfilter: 'border-webfilter/30',
    ips: 'border-ips/30',
    dns: 'border-dns/30',
  };

  if (!path) {
    return (
      <Card className="flex h-[600px] flex-col items-center justify-center gap-4 border-dashed">
        <FileX className="h-16 w-16 text-muted-foreground/50" />
        <div className="text-center">
          <h3 className="text-lg font-semibold">The report not generated</h3>
          <p className="text-sm text-muted-foreground">
            This report has not been generated yet. Please generate it first.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card className={cn('overflow-hidden', colorClasses[type])}>
      <div className="flex items-center justify-between border-b bg-muted/30 px-4 py-3">
        <div className="flex items-center gap-3">
          <span className="font-mono text-sm text-muted-foreground">{filename || 'Report Preview'}</span>
          {isDemo && (
            <span className="rounded bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
              Demo Mode
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={handleDownload} disabled={isDemo}>
            <Download className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" onClick={handleFullscreen}>
            {isFullscreen ? (
              <Minimize2 className="h-4 w-4" />
            ) : (
              <Maximize2 className="h-4 w-4" />
            )}
          </Button>
          {!isDemo && (
            <Button variant="ghost" size="sm" asChild>
              <a href={reportUrl} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4" />
              </a>
            </Button>
          )}
        </div>
      </div>

      <div className="relative">
        {loading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-background">
            <div className="space-y-4 text-center">
              <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <p className="text-sm text-muted-foreground">Loading report...</p>
            </div>
          </div>
        )}
        <iframe
          ref={iframeRef}
          srcDoc={isDemo ? DEMO_HTML : undefined}
          src={isDemo ? undefined : reportUrl}
          className="h-[600px] w-full border-0 bg-background"
          onLoad={() => setLoading(false)}
          title="Report Viewer"
          sandbox="allow-same-origin allow-scripts"
        />
      </div>
    </Card>
  );
}
