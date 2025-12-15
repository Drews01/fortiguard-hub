export type ReportType = 'appctrl' | 'webfilter' | 'ips' | 'dns' | 'antivirus';

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
    description: 'Monitor and control application',
    color: 'appctrl',
    icon: 'Shield',
  },
  webfilter: {
    type: 'webfilter',
    label: 'Web Filter',
    description: 'Track web browsing and blocked websites',
    color: 'webfilter',
    icon: 'Globe',
  },
  ips: {
    type: 'ips',
    label: 'IPS',
    description: 'Intrusion Prevention System',
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
  antivirus: {
    type: 'antivirus',
    label: 'Antivirus',
    description: 'Antivirus events and detections',
    color: 'antivirus',
    icon: 'Shield',
  },
};
