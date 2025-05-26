'use client';

import { Box, Grid, Paper, Typography, Button, Card, CardContent, CardHeader } from '@mui/material';
import { Refresh, People, CheckCircle, Error, Pending } from '@mui/icons-material';
import { useAppContext } from '@/context/AppContext';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { LeadStatus } from '@/types';

const COLORS = {
  'Pending': '#FFB74D',
  'Calling': '#42A5F5',
  'Confirmed': '#66BB6A',
  'Entry In Progress': '#AB47BC',
  'Entered': '#00C853',
  'Not Interested': '#FF5252',
  'Call Failed': '#F44336',
  'Entry Failed': '#FF7043'
};

const STATUS_ICONS = {
  'Pending': <Pending color="action" />,
  'Confirmed': <CheckCircle color="success" />,
  'Entered': <CheckCircle color="success" />,
  'Failed': <Error color="error" />
};

export default function Dashboard() {
  const { dashboardStats, systemStatus, isLoading, refreshDashboardStats } = useAppContext();

  const handleRefresh = () => {
    refreshDashboardStats();
  };

  const getPieChartData = () => {
    if (!dashboardStats) return [];
    return Object.entries(dashboardStats.by_status).map(([status, count]) => ({
      name: status,
      value: count
    }));
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">Dashboard</Typography>
        <Button 
          startIcon={<Refresh />} 
          onClick={handleRefresh}
          disabled={isLoading}
        >
          Refresh
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Total Leads
                  </Typography>
                  <Typography variant="h4" component="div">
                    {dashboardStats?.total_leads || 0}
                  </Typography>
                </Box>
                <People sx={{ fontSize: 40, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Pending
                  </Typography>
                  <Typography variant="h4" component="div">
                    {dashboardStats?.by_status?.Pending || 0}
                  </Typography>
                </Box>
                {STATUS_ICONS['Pending']}
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Confirmed
                  </Typography>
                  <Typography variant="h4" component="div">
                    {dashboardStats?.by_status?.Confirmed || 0}
                  </Typography>
                </Box>
                {STATUS_ICONS['Confirmed']}
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Entered
                  </Typography>
                  <Typography variant="h4" component="div">
                    {dashboardStats?.by_status?.Entered || 0}
                  </Typography>
                </Box>
                {STATUS_ICONS['Entered']}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Daily Activity
            </Typography>
            <Box sx={{ height: 300, pt: 1 }}>
              {dashboardStats && (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={dashboardStats.daily_stats}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="confirmed" 
                      stroke="#8884d8" 
                      activeDot={{ r: 8 }} 
                      name="Confirmed" 
                    />
                    <Line 
                      type="monotone" 
                      dataKey="entered" 
                      stroke="#82ca9d" 
                      name="Entered" 
                    />
                    <Line 
                      type="monotone" 
                      dataKey="failed" 
                      stroke="#ff8a80" 
                      name="Failed" 
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Lead Status Distribution
            </Typography>
            <Box sx={{ height: 300, display: 'flex', justifyContent: 'center', pt: 1 }}>
              {dashboardStats && (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={getPieChartData()}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {getPieChartData().map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={COLORS[entry.name as LeadStatus] || '#999999'} 
                        />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
} 