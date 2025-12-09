import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { format } from 'date-fns';
import { ArrowLeft, FileText, Calendar, AlertCircle } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { DatePicker } from '@/components/DatePicker';
import { MonthSelector } from '@/components/MonthSelector';
import { ReportViewer } from '@/components/ReportViewer';
import { ReportType, REPORT_TYPES, DailyReport, MonthlyReport } from '@/lib/types';
import { fetchDailyReports, fetchMonthlyReports } from '@/lib/api';
import { cn } from '@/lib/utils';

export default function ReportBrowser() {
  const { type } = useParams<{ type: ReportType }>();
  const [activeTab, setActiveTab] = useState('daily');
  const [selectedDate, setSelectedDate] = useState<Date | undefined>();
  const [selectedMonth, setSelectedMonth] = useState<string | undefined>();
  const [dailyReports, setDailyReports] = useState<DailyReport[]>([]);
  const [monthlyReports, setMonthlyReports] = useState<MonthlyReport[]>([]);
  const [loading, setLoading] = useState(true);

  const metadata = type ? REPORT_TYPES[type] : null;

  useEffect(() => {
    if (type) {
      setLoading(true);
      Promise.all([fetchDailyReports(type), fetchMonthlyReports(type)]).then(
        ([daily, monthly]) => {
          setDailyReports(daily);
          setMonthlyReports(monthly);
          setLoading(false);
          
          // Auto-select latest
          if (daily.length > 0) {
            setSelectedDate(new Date(daily[0].date));
          }
          if (monthly.length > 0) {
            setSelectedMonth(monthly[0].month);
          }
        }
      );
    }
  }, [type]);

  if (!metadata || !type) {
    return (
      <div className="container py-8">
        <Card className="p-8 text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground" />
          <h2 className="mt-4 text-xl font-semibold">Report Type Not Found</h2>
          <p className="mt-2 text-muted-foreground">The requested report type does not exist.</p>
          <Link to="/" className="mt-4 inline-block">
            <Button>Return to Dashboard</Button>
          </Link>
        </Card>
      </div>
    );
  }

  const colorClasses = {
    appctrl: 'text-appctrl',
    webfilter: 'text-webfilter',
    ips: 'text-ips',
    dns: 'text-dns',
  };

  const bgClasses = {
    appctrl: 'bg-appctrl',
    webfilter: 'bg-webfilter',
    ips: 'bg-ips',
    dns: 'bg-dns',
  };

  const selectedDailyReport = selectedDate
    ? dailyReports.find((r) => r.date === format(selectedDate, 'yyyy-MM-dd'))
    : null;

  const selectedMonthlyReport = selectedMonth
    ? monthlyReports.find((r) => r.month === selectedMonth)
    : null;

  return (
    <div className="min-h-screen bg-background">
      <div className="container py-8">
        {/* Header */}
        <div className="mb-6 flex items-center gap-4">
          <Link to="/">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <div className={cn('h-2 w-2 rounded-full', bgClasses[type])} />
              <h1 className={cn('text-2xl font-bold', colorClasses[type])}>
                {metadata.label} Reports
              </h1>
            </div>
            <p className="mt-1 text-muted-foreground">{metadata.description}</p>
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full max-w-md grid-cols-2">
            <TabsTrigger value="daily" className="gap-2">
              <FileText className="h-4 w-4" />
              Daily Reports
            </TabsTrigger>
            <TabsTrigger value="monthly" className="gap-2">
              <Calendar className="h-4 w-4" />
              Monthly Reports
            </TabsTrigger>
          </TabsList>

          {/* Daily Reports Tab */}
          <TabsContent value="daily" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Select Report Date</CardTitle>
                <CardDescription>
                  Choose a date to view the daily security report. Dates with available reports are highlighted.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="max-w-sm">
                  <DatePicker
                    date={selectedDate}
                    onDateChange={setSelectedDate}
                    availableDates={dailyReports.map((r) => r.date)}
                  />
                </div>
                {selectedDate && !selectedDailyReport && (
                  <div className="mt-4 flex items-center gap-2 rounded-lg bg-destructive/10 p-4 text-sm text-destructive">
                    <AlertCircle className="h-4 w-4" />
                    <span>No report available for {format(selectedDate, 'MMMM d, yyyy')}</span>
                  </div>
                )}
              </CardContent>
            </Card>

            <ReportViewer
              path={selectedDailyReport?.path || null}
              filename={selectedDailyReport?.filename || ''}
              type={type}
            />
          </TabsContent>

          {/* Monthly Reports Tab */}
          <TabsContent value="monthly" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Select Report Month</CardTitle>
                <CardDescription>
                  Choose a month to view the consolidated monthly security report.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="max-w-sm">
                  <MonthSelector
                    value={selectedMonth}
                    onValueChange={setSelectedMonth}
                    availableMonths={monthlyReports.map((r) => r.month)}
                  />
                </div>
              </CardContent>
            </Card>

            <ReportViewer
              path={selectedMonthlyReport?.path || null}
              filename={selectedMonthlyReport?.filename || ''}
              type={type}
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
