'use client';

import { useState } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  TextField,
  InputAdornment,
  Chip,
  Grid
} from '@mui/material';
import { 
  Refresh as RefreshIcon, 
  Search as SearchIcon,
  FilterList as FilterIcon
} from '@mui/icons-material';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import { useAppContext } from '@/context/AppContext';
import { Lead, LeadStatus } from '@/types';
import Link from 'next/link';

export default function LeadsPage() {
  const { leads, isLoading, refreshLeads } = useAppContext();
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');
  
  const handleRefresh = () => {
    refreshLeads(statusFilter ? { status: statusFilter } : undefined);
  };

  const handleStatusFilterChange = (event: any) => {
    const status = event.target.value;
    setStatusFilter(status);
    refreshLeads(status ? { status } : undefined);
  };

  const getStatusColor = (status: LeadStatus) => {
    switch (status) {
      case 'Pending':
        return 'default';
      case 'Calling':
        return 'primary';
      case 'Confirmed':
        return 'success';
      case 'Entry In Progress':
        return 'secondary';
      case 'Entered':
        return 'success';
      case 'Not Interested':
        return 'warning';
      case 'Call Failed':
        return 'error';
      case 'Entry Failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const filteredLeads = leads.filter(lead => {
    const searchMatch = searchTerm === '' || 
      lead.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      lead.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      lead.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      lead.phone.includes(searchTerm);
    
    return searchMatch;
  });

  const columns: GridColDef[] = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'first_name', headerName: 'First Name', width: 130 },
    { field: 'last_name', headerName: 'Last Name', width: 130 },
    { field: 'phone', headerName: 'Phone', width: 150 },
    { field: 'email', headerName: 'Email', width: 200 },
    { 
      field: 'status', 
      headerName: 'Status', 
      width: 150,
      renderCell: (params: GridRenderCellParams<Lead>) => (
        <Chip 
          label={params.value} 
          size="small"
          color={getStatusColor(params.value as LeadStatus)}
        />
      )
    },
    { 
      field: 'created_at', 
      headerName: 'Created', 
      width: 180,
      valueFormatter: (params) => new Date(params.value as string).toLocaleString()
    },
    { 
      field: 'updated_at', 
      headerName: 'Updated', 
      width: 180,
      valueFormatter: (params) => new Date(params.value as string).toLocaleString()
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      sortable: false,
      renderCell: (params: GridRenderCellParams<Lead>) => (
        <Link href={`/leads/${params.row.id}`} passHref>
          <Button size="small" variant="outlined">
            View
          </Button>
        </Link>
      )
    }
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">Leads</Typography>
        <Button 
          startIcon={<RefreshIcon />} 
          onClick={handleRefresh}
          disabled={isLoading}
          variant="outlined"
        >
          Refresh
        </Button>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              label="Search"
              variant="outlined"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              placeholder="Name, email, phone..."
              size="small"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <FormControl fullWidth size="small">
              <InputLabel id="status-filter-label">Status</InputLabel>
              <Select
                labelId="status-filter-label"
                id="status-filter"
                value={statusFilter}
                label="Status"
                onChange={handleStatusFilterChange}
                startAdornment={
                  <InputAdornment position="start">
                    <FilterIcon />
                  </InputAdornment>
                }
              >
                <MenuItem value="">All Statuses</MenuItem>
                <MenuItem value="Pending">Pending</MenuItem>
                <MenuItem value="Calling">Calling</MenuItem>
                <MenuItem value="Confirmed">Confirmed</MenuItem>
                <MenuItem value="Entry In Progress">Entry In Progress</MenuItem>
                <MenuItem value="Entered">Entered</MenuItem>
                <MenuItem value="Not Interested">Not Interested</MenuItem>
                <MenuItem value="Call Failed">Call Failed</MenuItem>
                <MenuItem value="Entry Failed">Entry Failed</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={4} sx={{ textAlign: 'right' }}>
            <Typography variant="body2" color="text.secondary">
              {filteredLeads.length} leads found
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Data Grid */}
      <Paper sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={filteredLeads}
          columns={columns}
          initialState={{
            pagination: {
              paginationModel: { page: 0, pageSize: 25 },
            },
            sorting: {
              sortModel: [{ field: 'updated_at', sort: 'desc' }],
            },
          }}
          pageSizeOptions={[25, 50, 100]}
          checkboxSelection
          disableRowSelectionOnClick
          loading={isLoading}
        />
      </Paper>
    </Box>
  );
} 