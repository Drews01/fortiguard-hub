import { Link, useLocation } from 'react-router-dom';
import { Shield, Globe, AlertTriangle, Server, LayoutDashboard } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';
import { cn } from '@/lib/utils';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard, color: 'text-primary' },
  { path: '/appctrl', label: 'App Control', icon: Shield, color: 'text-appctrl' },
  { path: '/webfilter', label: 'Web Filter', icon: Globe, color: 'text-webfilter' },
  { path: '/ips', label: 'IPS', icon: AlertTriangle, color: 'text-ips' },
  { path: '/dns', label: 'DNS', icon: Server, color: 'text-dns' },
];

export function Navbar() {
  const location = useLocation();

  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex items-center gap-6">
          <Link to="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
              <Shield className="h-6 w-6 text-primary-foreground" />
            </div>
            <div className="hidden sm:block">
              <h1 className="text-lg font-bold tracking-tight">FortiGate</h1>
              <p className="text-xs text-muted-foreground">Security Portal</p>
            </div>
          </Link>
        </div>

        <div className="flex items-center gap-1">
          {navItems.map(({ path, label, icon: Icon, color }) => {
            const isActive = location.pathname === path;
            return (
              <Link
                key={path}
                to={path}
                className={cn(
                  'flex items-center gap-2 px-3 py-2 text-sm font-medium transition-colors rounded-lg',
                  isActive
                    ? 'bg-secondary text-foreground'
                    : 'text-muted-foreground hover:bg-secondary/50 hover:text-foreground'
                )}
              >
                <Icon className={cn('h-4 w-4', isActive && color)} />
                <span className="hidden md:inline">{label}</span>
              </Link>
            );
          })}
          <div className="ml-2 border-l pl-2">
            <ThemeToggle />
          </div>
        </div>
      </div>
    </nav>
  );
}
