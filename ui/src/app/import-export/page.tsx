'use client';

import { useState, useRef } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  Grid, 
  Alert, 
  CircularProgress, 
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Card,
  CardContent
} from '@mui/material';
import { 
  Upload as UploadIcon, 
  Description as DescriptionIcon,
  Download as DownloadIcon,
  CloudUpload as CloudUploadIcon
} from '@mui/icons-material';
import { processCsvFile } from '@/utils/api';
import { useSnackbar } from 'notistack';

export default function ImportExportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { enqueueSnackbar } = useSnackbar();

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      const selectedFile = files[0];
      if (selectedFile.type === 'text/csv' || selectedFile.name.endsWith('.csv')) {
        setFile(selectedFile);
        setResult(null);
      } else {
        setFile(null);
        enqueueSnackbar('Please select a CSV file', { variant: 'error' });
      }
    }
  };

  const handleUploadClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleSubmit = async () => {
    if (!file) return;

    try {
      setLoading(true);
      const response = await processCsvFile(file);
      setResult(response);
      
      if (response.success) {
        enqueueSnackbar('CSV file processed successfully', { variant: 'success' });
        setFile(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      } else {
        enqueueSnackbar('Failed to process CSV file', { variant: 'error' });
      }
    } catch (error) {
      console.error('Error processing CSV:', error);
      setResult({
        success: false,
        message: 'An error occurred while processing the file'
      });
      enqueueSnackbar('An error occurred while processing the file', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" sx={{ mb: 3 }}>
        Import/Export
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Import Leads from CSV
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <input
                type="file"
                accept=".csv"
                style={{ display: 'none' }}
                ref={fileInputRef}
                onChange={handleFileChange}
              />
              
              <Box 
                sx={{ 
                  border: '2px dashed #ccc', 
                  p: 3, 
                  mb: 2, 
                  textAlign: 'center',
                  borderRadius: 1,
                  backgroundColor: 'background.paper',
                  cursor: 'pointer',
                  '&:hover': {
                    borderColor: 'primary.main',
                    backgroundColor: 'rgba(0, 0, 0, 0.01)'
                  }
                }}
                onClick={handleUploadClick}
              >
                <CloudUploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                <Typography variant="body1" gutterBottom>
                  {file ? file.name : 'Click to select a CSV file or drag and drop'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  The CSV should contain lead information in the required format
                </Typography>
              </Box>
              
              <Button 
                variant="contained" 
                color="primary" 
                startIcon={<UploadIcon />}
                onClick={handleSubmit}
                disabled={!file || loading}
                fullWidth
              >
                {loading ? <CircularProgress size={24} /> : 'Upload and Process'}
              </Button>
              
              {result && (
                <Alert 
                  severity={result.success ? 'success' : 'error'} 
                  sx={{ mt: 2 }}
                >
                  {result.message}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Export Options
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <List>
                <ListItem>
                  <ListItemIcon>
                    <DownloadIcon />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Export All Leads" 
                    secondary="Download all leads data as CSV" 
                  />
                  <Button variant="outlined" startIcon={<DescriptionIcon />}>
                    Export
                  </Button>
                </ListItem>
                
                <ListItem>
                  <ListItemIcon>
                    <DownloadIcon />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Export Confirmed Leads" 
                    secondary="Download only confirmed leads as CSV" 
                  />
                  <Button variant="outlined" startIcon={<DescriptionIcon />}>
                    Export
                  </Button>
                </ListItem>
                
                <ListItem>
                  <ListItemIcon>
                    <DownloadIcon />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Export Failed Leads" 
                    secondary="Download leads that failed processing" 
                  />
                  <Button variant="outlined" startIcon={<DescriptionIcon />}>
                    Export
                  </Button>
                </ListItem>
              </List>
              
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2, p: 1 }}>
                Note: Exported files will include all relevant lead information in CSV format that can
                be imported into spreadsheet applications or CRM systems.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>CSV Format Requirements</Typography>
        <Divider sx={{ mb: 2 }} />
        
        <Typography variant="body2" paragraph>
          Your CSV file should have the following columns:
        </Typography>
        
        <List dense>
          <ListItem>
            <ListItemIcon>
              <DescriptionIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText 
              primary="first_name - First name of the lead (required)" 
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <DescriptionIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText 
              primary="last_name - Last name of the lead (required)" 
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <DescriptionIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText 
              primary="phone - Phone number (required, format: XXX-XXX-XXXX)" 
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <DescriptionIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText 
              primary="email - Email address (required)" 
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <DescriptionIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText 
              primary="address - Street address (optional)" 
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <DescriptionIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText 
              primary="city - City (optional)" 
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <DescriptionIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText 
              primary="state - State (optional)" 
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <DescriptionIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText 
              primary="zip_code - ZIP code (optional)" 
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <DescriptionIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText 
              primary="notes - Additional notes (optional)" 
            />
          </ListItem>
        </List>
        
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            Example format: 
            <code>first_name,last_name,phone,email,address,city,state,zip_code,notes</code>
          </Typography>
        </Alert>
      </Paper>
    </Box>
  );
} 