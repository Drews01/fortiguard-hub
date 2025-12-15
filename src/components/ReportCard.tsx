import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Shield, Globe, AlertTriangle, Server, FileText, Calendar, ArrowRight } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ReportType, REPORT_TYPES, ReportSummary } from '@/lib/types';
import { fetchReportSummary } from '@/lib/api';
import { cn } from '@/lib/utils';

const iconMap = {
  Shield,
  Globe,
  AlertTriangle,
  Server,
};

interface ReportCardProps {
  type: ReportType;
}

export function ReportCard({ type }: ReportCardProps) {
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [loading, setLoading] = useState(true);

  const metadata = REPORT_TYPES[type];
  const Icon = iconMap[metadata.icon as keyof typeof iconMap];

  useEffect(() => {
    fetchReportSummary(type).then(data => {
      setSummary(data);
      setLoading(false);
    });
  }, [type]);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'No reports';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const colorClasses = {
    appctrl: 'bg-appctrl text-appctrl-foreground hover:bg-appctrl/90',
    webfilter: 'bg-webfilter text-webfilter-foreground hover:bg-webfilter/90',
    ips: 'bg-ips text-ips-foreground hover:bg-ips/90',
    dns: 'bg-dns text-dns-foreground hover:bg-dns/90',
    antivirus: 'bg-antivirus text-antivirus-foreground hover:bg-antivirus/90',
  };

  const borderClasses = {
    appctrl: 'border-appctrl/30',
    webfilter: 'border-webfilter/30',
    ips: 'border-ips/30',
    dns: 'border-dns/30',
    antivirus: 'border-antivirus/30',
  };

  const iconBgClasses = {
    appctrl: 'bg-appctrl/10 text-appctrl',
    webfilter: 'bg-webfilter/10 text-webfilter',
    ips: 'bg-ips/10 text-ips',
    dns: 'bg-dns/10 text-dns',
    antivirus: 'bg-antivirus/10 text-antivirus',
  };

  return (
    <Card className={cn('relative overflow-hidden transition-all hover:shadow-lg flex flex-col', borderClasses[type])}>
      <div className={cn('absolute top-0 left-0 right-0 h-1', colorClasses[type].split(' ')[0])} />
      
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className={cn('flex h-12 w-12 items-center justify-center rounded-xl', iconBgClasses[type])}>
            <Icon className="h-6 w-6" />
          </div>
        </div>
        <CardTitle className="mt-4 text-xl">{metadata.label}</CardTitle>
        <CardDescription className="text-sm">{metadata.description}</CardDescription>
      </CardHeader>

      <CardContent className="space-y-4 flex flex-col flex-grow">
        {loading ? (
          <div className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <FileText className="h-4 w-4" />
                  <span className="text-xs font-medium uppercase tracking-wide">Daily</span>
                </div>
                <p className="text-2xl font-bold">{summary?.dailyCount || 0}</p>
                <p className="text-xs text-muted-foreground">
                  Latest: {formatDate(summary?.latestDailyDate || null)}
                </p>
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  <span className="text-xs font-medium uppercase tracking-wide">Monthly</span>
                </div>
                <p className="text-2xl font-bold">{summary?.monthlyCount || 0}</p>
                <p className="text-xs text-muted-foreground">
                  Latest: {summary?.latestMonthlyDate || 'N/A'}
                </p>
              </div>
            </div>

            <Link to={`/${type}`} className="block">
              <Button className={cn('w-full gap-2', colorClasses[type])}>
                View Reports
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </>
        )}
      </CardContent>
    </Card>
  );
}
