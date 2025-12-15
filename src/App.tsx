import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "@/hooks/use-theme";
import { Navbar } from "@/components/Navbar";
import Dashboard from "./pages/Dashboard";
import ReportBrowser from "./pages/ReportBrowser";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <div className="min-h-screen bg-background">
            <Navbar />
            <Routes>
              <Route path="/" element={<Dashboard />} />

              {/* New param route used by ReportBrowser (reads type from useParams) */}
              <Route path="/reports/:type" element={<ReportBrowser />} />

              {/* Keep convenient short paths but redirect to the canonical param route */}
              <Route path="/appctrl" element={<Navigate to="/reports/appctrl" replace />} />
              <Route path="/webfilter" element={<Navigate to="/reports/webfilter" replace />} />
              <Route path="/ips" element={<Navigate to="/reports/ips" replace />} />
              <Route path="/dns" element={<Navigate to="/reports/dns" replace />} />
              <Route path="/antivirus" element={<Navigate to="/reports/antivirus" replace />} />

              <Route path="*" element={<NotFound />} />
            </Routes>
          </div>
        </BrowserRouter>
      </TooltipProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;
