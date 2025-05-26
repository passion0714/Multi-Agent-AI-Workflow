import { Lead, SystemStatus, DashboardStats, LeadStatus } from '@/types';

// Sample lead data
export const mockLeads: Lead[] = [
  {
    id: 1,
    first_name: 'John',
    last_name: 'Doe',
    phone: '555-123-4567',
    email: 'john.doe@example.com',
    address: '123 Main St',
    city: 'Boston',
    state: 'MA',
    zip_code: '02108',
    status: 'Confirmed',
    notes: 'Interested in our services',
    created_at: '2023-06-15T10:30:00Z',
    updated_at: '2023-06-16T14:20:00Z',
    call_recording_url: 'https://example.com/recordings/call1.mp3'
  },
  {
    id: 2,
    first_name: 'Jane',
    last_name: 'Smith',
    phone: '555-987-6543',
    email: 'jane.smith@example.com',
    address: '456 Oak Ave',
    city: 'New York',
    state: 'NY',
    zip_code: '10001',
    status: 'Pending',
    notes: '',
    created_at: '2023-06-17T09:15:00Z',
    updated_at: '2023-06-17T09:15:00Z'
  },
  {
    id: 3,
    first_name: 'Robert',
    last_name: 'Johnson',
    phone: '555-456-7890',
    email: 'robert.johnson@example.com',
    address: '789 Pine Rd',
    city: 'Chicago',
    state: 'IL',
    zip_code: '60601',
    status: 'Entered',
    notes: 'Premium customer',
    created_at: '2023-06-14T16:45:00Z',
    updated_at: '2023-06-18T11:30:00Z'
  },
  {
    id: 4,
    first_name: 'Sarah',
    last_name: 'Williams',
    phone: '555-234-5678',
    email: 'sarah.williams@example.com',
    address: '321 Cedar Ln',
    city: 'Los Angeles',
    state: 'CA',
    zip_code: '90001',
    status: 'Call Failed',
    notes: 'No answer, try again',
    created_at: '2023-06-16T13:20:00Z',
    updated_at: '2023-06-16T13:25:00Z'
  },
  {
    id: 5,
    first_name: 'Michael',
    last_name: 'Brown',
    phone: '555-876-5432',
    email: 'michael.brown@example.com',
    address: '654 Maple Dr',
    city: 'Houston',
    state: 'TX',
    zip_code: '77001',
    status: 'Not Interested',
    notes: 'Customer declined offer',
    created_at: '2023-06-15T14:10:00Z',
    updated_at: '2023-06-15T14:30:00Z'
  }
];

// Sample system status
export const mockSystemStatus: SystemStatus = {
  voice_agent_status: 'Active',
  data_entry_agent_status: 'Active',
  total_leads: 42,
  pending_leads: 15,
  confirmed_leads: 18,
  entered_leads: 5,
  failed_leads: 4,
  last_activity: '2023-06-18T15:45:30Z'
};

// Sample dashboard stats
export const mockDashboardStats: DashboardStats = {
  total_leads: 42,
  by_status: {
    'Pending': 15,
    'Calling': 3,
    'Confirmed': 10,
    'Entry In Progress': 2,
    'Entered': 5,
    'Not Interested': 3,
    'Call Failed': 2,
    'Entry Failed': 2
  },
  conversion_rate: 35.7,
  daily_stats: [
    { date: '2023-06-12', confirmed: 2, entered: 1, failed: 1 },
    { date: '2023-06-13', confirmed: 3, entered: 2, failed: 0 },
    { date: '2023-06-14', confirmed: 1, entered: 0, failed: 2 },
    { date: '2023-06-15', confirmed: 4, entered: 3, failed: 1 },
    { date: '2023-06-16', confirmed: 5, entered: 2, failed: 2 },
    { date: '2023-06-17', confirmed: 3, entered: 1, failed: 0 },
    { date: '2023-06-18', confirmed: 2, entered: 1, failed: 0 }
  ]
};

export const mockApiResponses = {
  success: { success: true, message: 'Operation completed successfully' },
  error: { success: false, message: 'Operation failed' }
}; 