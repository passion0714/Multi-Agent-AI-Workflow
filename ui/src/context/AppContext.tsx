import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useSnackbar } from 'notistack';
import { SystemStatus, Lead, DashboardStats } from '@/types';
import { getSystemStatus, fetchLeads, getDashboardStats } from '@/utils/api';

interface AppContextProps {
  systemStatus: SystemStatus | null;
  leads: Lead[];
  dashboardStats: DashboardStats | null;
  isLoading: boolean;
  refreshSystemStatus: () => Promise<void>;
  refreshLeads: (filters?: { status?: string }) => Promise<void>;
  refreshDashboardStats: () => Promise<void>;
}

const AppContext = createContext<AppContextProps | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

  const refreshSystemStatus = async () => {
    try {
      setIsLoading(true);
      const status = await getSystemStatus();
      setSystemStatus(status);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
      enqueueSnackbar('Failed to fetch system status', { variant: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  const refreshLeads = async (filters?: { status?: string }) => {
    try {
      setIsLoading(true);
      const data = await fetchLeads(filters);
      setLeads(data);
    } catch (error) {
      console.error('Failed to fetch leads:', error);
      enqueueSnackbar('Failed to fetch leads', { variant: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  const refreshDashboardStats = async () => {
    try {
      setIsLoading(true);
      const stats = await getDashboardStats();
      setDashboardStats(stats);
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error);
      enqueueSnackbar('Failed to fetch dashboard statistics', { variant: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshSystemStatus();
    refreshLeads();
    refreshDashboardStats();

    // Set up periodic refresh
    const interval = setInterval(() => {
      refreshSystemStatus();
      refreshLeads();
      refreshDashboardStats();
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <AppContext.Provider
      value={{
        systemStatus,
        leads,
        dashboardStats,
        isLoading,
        refreshSystemStatus,
        refreshLeads,
        refreshDashboardStats,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
} 