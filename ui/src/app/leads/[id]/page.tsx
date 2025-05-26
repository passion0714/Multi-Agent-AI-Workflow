'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  Button, 
  Chip, 
  Divider, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableRow,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Card,
  CardContent,
  Alert,
  AlertTitle
} from '@mui/material';
import { 
  ArrowBack as ArrowBackIcon, 
  Save as SaveIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  LocationOn as LocationIcon,
  Person as PersonIcon,
  Notes as NotesIcon,
  AccessTime as AccessTimeIcon
} from '@mui/icons-material';
import { fetchLead, updateLeadStatus } from '@/utils/api';
import { Lead, LeadStatus } from '@/types';
import { useSnackbar } from 'notistack';
import Link from 'next/link';

export default function LeadDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { enqueueSnackbar } = useSnackbar();
  const leadId = params.id as string;
  
  const [lead, setLead] = useState<Lead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newStatus, setNewStatus] = useState<LeadStatus | ''>('');
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    async function loadLead() {
      try {
        setLoading(true);
        const data = await fetchLead(parseInt(leadId));
        setLead(data);
        setNewStatus(data.status);
        setError(null);
      } catch (err) {
        console.error('Failed to load lead:', err);
        setError('Failed to load lead information');
      } finally {
        setLoading(false);
      }
    }

    if (leadId) {
      loadLead();
    }
  }, [leadId]);

  const handleStatusChange = async () => {
    if (!lead || !newStatus || newStatus === lead.status) return;
    
    try {
      setUpdating(true);
      const updatedLead = await updateLeadStatus(lead.id, newStatus);
      setLead(updatedLead);
      enqueueSnackbar('Lead status updated successfully', { variant: 'success' });
    } catch (err) {
      console.error('Failed to update lead status:', err);
      enqueueSnackbar('Failed to update lead status', { variant: 'error' });
    } finally {
      setUpdating(false);
    }
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

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !lead) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 2 }}>
          <AlertTitle>Error</AlertTitle>
          {error || 'Lead not found'}
        </Alert>
        <Button 
          startIcon={<ArrowBackIcon />}
          onClick={() => router.push('/leads')}
        >
          Back to Leads
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Link href="/leads" passHref>
            <Button startIcon={<ArrowBackIcon />} sx={{ mr: 2 }}>
              Back
            </Button>
          </Link>
          <Typography variant="h4" component="h1">
            Lead: {lead.first_name} {lead.last_name}
          </Typography>
        </Box>
        <Chip 
          label={lead.status} 
          color={getStatusColor(lead.status)}
          size="medium"
        />
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <PersonIcon sx={{ mr: 1 }} /> Personal Information
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <TableContainer>
              <Table>
                <TableBody>
                  <TableRow>
                    <TableCell component="th" scope="row" width="30%">Full Name</TableCell>
                    <TableCell>{lead.first_name} {lead.last_name}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th" scope="row">
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <PhoneIcon fontSize="small" sx={{ mr: 1 }} /> Phone
                      </Box>
                    </TableCell>
                    <TableCell>{lead.phone}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th" scope="row">
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <EmailIcon fontSize="small" sx={{ mr: 1 }} /> Email
                      </Box>
                    </TableCell>
                    <TableCell>{lead.email}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th" scope="row">
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <LocationIcon fontSize="small" sx={{ mr: 1 }} /> Address
                      </Box>
                    </TableCell>
                    <TableCell>
                      {lead.address}<br />
                      {lead.city}, {lead.state} {lead.zip_code}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>

          {lead.notes && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <NotesIcon sx={{ mr: 1 }} /> Notes
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Typography variant="body1">{lead.notes}</Typography>
            </Paper>
          )}

          {lead.call_recording_url && (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>Call Recording</Typography>
              <Divider sx={{ mb: 2 }} />
              <audio controls style={{ width: '100%' }}>
                <source src={lead.call_recording_url} type="audio/mpeg" />
                Your browser does not support the audio element.
              </audio>
            </Paper>
          )}
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Update Status</Typography>
              <Divider sx={{ mb: 2 }} />
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel id="status-select-label">Status</InputLabel>
                <Select
                  labelId="status-select-label"
                  id="status-select"
                  value={newStatus}
                  label="Status"
                  onChange={(e) => setNewStatus(e.target.value as LeadStatus)}
                  disabled={updating}
                >
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
              
              <Button
                variant="contained"
                startIcon={<SaveIcon />}
                fullWidth
                onClick={handleStatusChange}
                disabled={updating || newStatus === lead.status || newStatus === ''}
              >
                {updating ? 'Updating...' : 'Update Status'}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <AccessTimeIcon sx={{ mr: 1 }} /> Timeline
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" color="text.secondary">Created</Typography>
                <Typography variant="body1">
                  {new Date(lead.created_at).toLocaleString()}
                </Typography>
              </Box>
              
              <Box>
                <Typography variant="body2" color="text.secondary">Last Updated</Typography>
                <Typography variant="body1">
                  {new Date(lead.updated_at).toLocaleString()}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
} 