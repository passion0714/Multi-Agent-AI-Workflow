import axios from 'axios';
import { Lead, SystemStatus, DashboardStats } from '@/types';
import { mockLeads, mockSystemStatus, mockDashboardStats, mockApiResponses } from './mockData';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Flag to use mock data instead of actual API calls
const USE_MOCK_DATA = true; // Set to false when backend is available

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const fetchLeads = async (filters?: { status?: string }): Promise<Lead[]> => {
  if (USE_MOCK_DATA) {
    // Return mock data
    if (filters?.status) {
      return mockLeads.filter(lead => lead.status === filters.status);
    }
    return mockLeads;
  }

  // Actual API call
  const params = new URLSearchParams();
  if (filters?.status) {
    params.append('status', filters.status);
  }
  
  const response = await api.get(`/leads?${params.toString()}`);
  return response.data;
};

export const fetchLead = async (id: number): Promise<Lead> => {
  if (USE_MOCK_DATA) {
    // Return mock data
    const lead = mockLeads.find(lead => lead.id === id);
    if (lead) return lead;
    throw new Error('Lead not found');
  }

  // Actual API call
  const response = await api.get(`/leads/${id}`);
  return response.data;
};

export const updateLeadStatus = async (id: number, status: string): Promise<Lead> => {
  if (USE_MOCK_DATA) {
    // Simulate updating a lead's status
    const leadIndex = mockLeads.findIndex(lead => lead.id === id);
    if (leadIndex === -1) throw new Error('Lead not found');
    
    const updatedLead = {
      ...mockLeads[leadIndex],
      status: status as any,
      updated_at: new Date().toISOString()
    };
    
    // This doesn't actually update the mock data permanently since it's imported
    // but it returns what would be returned by the API
    return updatedLead;
  }

  // Actual API call
  const response = await api.put(`/leads/${id}/status`, { status });
  return response.data;
};

export const processCsvFile = async (file: File): Promise<{ success: boolean; message: string }> => {
  if (USE_MOCK_DATA) {
    // Simulate CSV processing
    return mockApiResponses.success;
  }

  // Actual API call
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/csv/process', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

export const getSystemStatus = async (): Promise<SystemStatus> => {
  if (USE_MOCK_DATA) {
    // Return mock data
    return mockSystemStatus;
  }

  // Actual API call
  const response = await api.get('/status');
  return response.data;
};

export const resetSystem = async (): Promise<{ success: boolean; message: string }> => {
  if (USE_MOCK_DATA) {
    // Simulate system reset
    return mockApiResponses.success;
  }

  // Actual API call
  const response = await api.post('/reset');
  return response.data;
};

export const getDashboardStats = async (): Promise<DashboardStats> => {
  if (USE_MOCK_DATA) {
    // Return mock data
    return mockDashboardStats;
  }

  // Actual API call
  const response = await api.get('/dashboard/stats');
  return response.data;
}; 