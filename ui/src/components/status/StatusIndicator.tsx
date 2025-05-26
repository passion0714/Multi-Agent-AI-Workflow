import { Box, Typography, Chip, CircularProgress, Paper } from '@mui/material';
import { CheckCircle, Cancel, Refresh } from '@mui/icons-material';
import { useAppContext } from '@/context/AppContext';

export default function StatusIndicator() {
  const { systemStatus, isLoading, refreshSystemStatus } = useAppContext();

  const handleRefresh = () => {
    refreshSystemStatus();
  };

  if (!systemStatus && isLoading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', p: 2 }}>
        <CircularProgress size={20} sx={{ mr: 1 }} />
        <Typography variant="body2">Loading status...</Typography>
      </Box>
    );
  }

  if (!systemStatus) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', p: 2 }}>
        <Typography variant="body2" color="error">Status unavailable</Typography>
        <Refresh 
          fontSize="small" 
          sx={{ ml: 1, cursor: 'pointer' }} 
          onClick={handleRefresh}
        />
      </Box>
    );
  }

  return (
    <Paper elevation={0} sx={{ p: 1, backgroundColor: 'background.paper' }}>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>System Status</Typography>
      
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5, alignItems: 'center' }}>
        <Typography variant="body2">Voice Agent:</Typography>
        <Chip 
          size="small"
          label={systemStatus.voice_agent_status}
          color={systemStatus.voice_agent_status === 'Active' ? 'success' : 'error'}
          icon={systemStatus.voice_agent_status === 'Active' ? <CheckCircle fontSize="small" /> : <Cancel fontSize="small" />}
        />
      </Box>
      
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5, alignItems: 'center' }}>
        <Typography variant="body2">Data Entry Agent:</Typography>
        <Chip 
          size="small"
          label={systemStatus.data_entry_agent_status}
          color={systemStatus.data_entry_agent_status === 'Active' ? 'success' : 'error'}
          icon={systemStatus.data_entry_agent_status === 'Active' ? <CheckCircle fontSize="small" /> : <Cancel fontSize="small" />}
        />
      </Box>
      
      <Box sx={{ mt: 1 }}>
        <Typography variant="caption" color="text.secondary" display="block">
          Pending: {systemStatus.pending_leads}
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block">
          Confirmed: {systemStatus.confirmed_leads}
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block">
          Entered: {systemStatus.entered_leads}
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block">
          Last Activity: {new Date(systemStatus.last_activity).toLocaleString()}
        </Typography>
      </Box>
    </Paper>
  );
} 