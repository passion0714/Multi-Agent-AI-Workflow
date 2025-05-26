'use client';

import { useState } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  Divider, 
  Switch, 
  FormControlLabel,
  TextField,
  Grid,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Alert
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  Warning as WarningIcon,
  Settings as SettingsIcon,
  CloudUpload as CloudUploadIcon,
  PlayArrow as PlayArrowIcon,
  Stop as StopIcon
} from '@mui/icons-material';
import { resetSystem } from '@/utils/api';
import { useSnackbar } from 'notistack';

export default function SettingsPage() {
  const { enqueueSnackbar } = useSnackbar();
  const [openResetDialog, setOpenResetDialog] = useState(false);
  const [resetting, setResetting] = useState(false);
  
  // Settings state
  const [voiceAgentActive, setVoiceAgentActive] = useState(true);
  const [dataEntryAgentActive, setDataEntryAgentActive] = useState(true);
  const [voiceBatchSize, setVoiceBatchSize] = useState(5);
  const [dataEntryBatchSize, setDataEntryBatchSize] = useState(3);
  const [csvInterval, setCsvInterval] = useState(60);
  
  // AWS Settings
  const [awsAccessKey, setAwsAccessKey] = useState('');
  const [awsSecretKey, setAwsSecretKey] = useState('');
  const [awsRegion, setAwsRegion] = useState('us-east-1');
  const [s3BucketName, setS3BucketName] = useState('');
  
  // Assistable.AI Settings
  const [assistableApiKey, setAssistableApiKey] = useState('');
  
  // LeadHoop Settings
  const [leadHoopUsername, setLeadHoopUsername] = useState('');
  const [leadHoopPassword, setLeadHoopPassword] = useState('');
  
  const handleOpenResetDialog = () => {
    setOpenResetDialog(true);
  };
  
  const handleCloseResetDialog = () => {
    setOpenResetDialog(false);
  };
  
  const handleResetSystem = async () => {
    try {
      setResetting(true);
      const result = await resetSystem();
      if (result.success) {
        enqueueSnackbar('System reset successfully', { variant: 'success' });
      } else {
        enqueueSnackbar(result.message || 'Failed to reset system', { variant: 'error' });
      }
    } catch (error) {
      console.error('Error resetting system:', error);
      enqueueSnackbar('An error occurred while resetting the system', { variant: 'error' });
    } finally {
      setResetting(false);
      setOpenResetDialog(false);
    }
  };
  
  const handleSaveSettings = () => {
    // In a real application, this would save settings to the backend
    enqueueSnackbar('Settings saved successfully', { variant: 'success' });
  };
  
  return (
    <Box>
      <Typography variant="h4" component="h1" sx={{ mb: 3 }}>
        Settings
      </Typography>
      
      <Grid container spacing={3}>
        {/* Agent Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <SettingsIcon sx={{ mr: 1 }} /> Agent Settings
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={voiceAgentActive}
                    onChange={(e) => setVoiceAgentActive(e.target.checked)}
                    color="primary"
                  />
                }
                label="Voice Agent Active"
                sx={{ mb: 1, display: 'block' }}
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={dataEntryAgentActive}
                    onChange={(e) => setDataEntryAgentActive(e.target.checked)}
                    color="primary"
                  />
                }
                label="Data Entry Agent Active"
                sx={{ mb: 2, display: 'block' }}
              />
              
              <TextField
                fullWidth
                label="Voice Agent Batch Size"
                type="number"
                value={voiceBatchSize}
                onChange={(e) => setVoiceBatchSize(Number(e.target.value))}
                inputProps={{ min: 1, max: 20 }}
                sx={{ mb: 2 }}
                size="small"
              />
              
              <TextField
                fullWidth
                label="Data Entry Agent Batch Size"
                type="number"
                value={dataEntryBatchSize}
                onChange={(e) => setDataEntryBatchSize(Number(e.target.value))}
                inputProps={{ min: 1, max: 10 }}
                sx={{ mb: 2 }}
                size="small"
              />
              
              <TextField
                fullWidth
                label="CSV Processing Interval (seconds)"
                type="number"
                value={csvInterval}
                onChange={(e) => setCsvInterval(Number(e.target.value))}
                inputProps={{ min: 30, max: 3600 }}
                size="small"
              />
            </CardContent>
          </Card>
        </Grid>
        
        {/* AWS Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <CloudUploadIcon sx={{ mr: 1 }} /> AWS S3 Settings
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <TextField
                fullWidth
                label="AWS Access Key"
                value={awsAccessKey}
                onChange={(e) => setAwsAccessKey(e.target.value)}
                sx={{ mb: 2 }}
                size="small"
              />
              
              <TextField
                fullWidth
                label="AWS Secret Key"
                value={awsSecretKey}
                onChange={(e) => setAwsSecretKey(e.target.value)}
                type="password"
                sx={{ mb: 2 }}
                size="small"
              />
              
              <TextField
                fullWidth
                label="AWS Region"
                value={awsRegion}
                onChange={(e) => setAwsRegion(e.target.value)}
                sx={{ mb: 2 }}
                size="small"
              />
              
              <TextField
                fullWidth
                label="S3 Bucket Name"
                value={s3BucketName}
                onChange={(e) => setS3BucketName(e.target.value)}
                size="small"
              />
            </CardContent>
          </Card>
        </Grid>
        
        {/* Assistable.AI Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Assistable.AI Settings</Typography>
              <Divider sx={{ mb: 2 }} />
              
              <TextField
                fullWidth
                label="API Key"
                value={assistableApiKey}
                onChange={(e) => setAssistableApiKey(e.target.value)}
                type="password"
                size="small"
              />
              
              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  Assistable.AI is used for outbound calling to leads.
                </Typography>
              </Alert>
            </CardContent>
          </Card>
        </Grid>
        
        {/* LeadHoop Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>LeadHoop Portal Settings</Typography>
              <Divider sx={{ mb: 2 }} />
              
              <TextField
                fullWidth
                label="Username"
                value={leadHoopUsername}
                onChange={(e) => setLeadHoopUsername(e.target.value)}
                sx={{ mb: 2 }}
                size="small"
              />
              
              <TextField
                fullWidth
                label="Password"
                value={leadHoopPassword}
                onChange={(e) => setLeadHoopPassword(e.target.value)}
                type="password"
                size="small"
              />
              
              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  These credentials are used to submit lead data to the LeadHoop portal.
                </Typography>
              </Alert>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* System Control */}
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>System Control</Typography>
        <Divider sx={{ mb: 2 }} />
        
        <Grid container spacing={2}>
          <Grid item>
            <Button 
              variant="contained" 
              color="primary" 
              startIcon={<SaveIcon />}
              onClick={handleSaveSettings}
            >
              Save Settings
            </Button>
          </Grid>
          
          <Grid item>
            <Button 
              variant="outlined" 
              color="secondary" 
              startIcon={<RefreshIcon />}
            >
              Restart System
            </Button>
          </Grid>
          
          <Grid item>
            <Button 
              variant="contained" 
              color="success" 
              startIcon={<PlayArrowIcon />}
            >
              Start All Agents
            </Button>
          </Grid>
          
          <Grid item>
            <Button 
              variant="outlined" 
              color="error" 
              startIcon={<StopIcon />}
            >
              Stop All Agents
            </Button>
          </Grid>
          
          <Grid item>
            <Button 
              variant="outlined" 
              color="error" 
              startIcon={<DeleteIcon />}
              onClick={handleOpenResetDialog}
            >
              Reset System
            </Button>
          </Grid>
        </Grid>
        
        <Alert severity="warning" sx={{ mt: 3 }}>
          <Typography variant="body2">
            <strong>Warning:</strong> Resetting the system will clear all pending leads. This action cannot be undone.
          </Typography>
        </Alert>
      </Paper>
      
      {/* Reset Dialog */}
      <Dialog
        open={openResetDialog}
        onClose={handleCloseResetDialog}
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center' }}>
          <WarningIcon color="warning" sx={{ mr: 1 }} />
          Confirm System Reset
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to reset the system? This will clear all pending leads and reset agent states. 
            This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseResetDialog} disabled={resetting}>
            Cancel
          </Button>
          <Button 
            onClick={handleResetSystem} 
            color="error" 
            variant="contained"
            disabled={resetting}
            startIcon={resetting ? <RefreshIcon /> : <DeleteIcon />}
          >
            {resetting ? 'Resetting...' : 'Reset System'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
} 