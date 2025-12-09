export type ReportType = 'appctrl' | 'webfilter' | 'ips' | 'dns';

export interface ReportMetadata {
  type: ReportType;
  label: string;
  description: string;
  color: string;
  icon: string;
}

export interface ReportSummary {
  dailyCount: number;
  monthlyCount: number;
  latestDailyDate: string | null;
  latestMonthlyDate: string | null;
}

export interface DailyReport {
  date: string;
  filename: string;
  path: string;
}

export interface MonthlyReport {
  month: string;
  filename: string;
  path: string;
}

export const REPORT_TYPES: Record<ReportType, ReportMetadata> = {
  appctrl: {
    type: 'appctrl',
    label: 'Application Control',
    description: 'Monitor and control application usage across your network',
    color: 'appctrl',
    icon: 'Shield',
  },
  webfilter: {
    type: 'webfilter',
    label: 'Web Filter',
    description: 'Track web browsing patterns and blocked websites',
    color: 'webfilter',
    icon: 'Globe',
  },
  ips: {
    type: 'ips',
    label: 'IPS',
    description: 'Intrusion Prevention System alerts and blocked threats',
    color: 'ips',
    icon: 'AlertTriangle',
  },
  dns: {
    type: 'dns',
    label: 'DNS',
    description: 'DNS query logs and filtered domain requests',
    color: 'dns',
    icon: 'Server',
  },
};
