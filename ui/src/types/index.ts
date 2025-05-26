export type LeadStatus = 
  | 'Pending'
  | 'Calling'
  | 'Confirmed'
  | 'Entry In Progress'
  | 'Entered'
  | 'Not Interested'
  | 'Call Failed'
  | 'Entry Failed';

export interface Lead {
  id: number;
  first_name: string;
  last_name: string;
  phone: string;
  email: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  status: LeadStatus;
  notes: string;
  created_at: string;
  updated_at: string;
  call_recording_url?: string;
}

export interface SystemStatus {
  voice_agent_status: 'Active' | 'Inactive';
  data_entry_agent_status: 'Active' | 'Inactive';
  total_leads: number;
  pending_leads: number;
  confirmed_leads: number;
  entered_leads: number;
  failed_leads: number;
  last_activity: string;
}

export interface DashboardStats {
  total_leads: number;
  by_status: Record<LeadStatus, number>;
  conversion_rate: number;
  daily_stats: {
    date: string;
    confirmed: number;
    entered: number;
    failed: number;
  }[];
} 