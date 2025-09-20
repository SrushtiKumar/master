import React, { useContext, useState, useEffect } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import axios from 'axios';
import {
  Container, Grid, Paper, Typography, Box, Button,
  Card, CardContent, CardActions, CircularProgress
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import KeyIcon from '@mui/icons-material/Key';
import FolderIcon from '@mui/icons-material/Folder';
import AuthContext from '../../context/AuthContext';

const Dashboard = () => {
  const { token, user } = useContext(AuthContext);
  const [stats, setStats] = useState({
    fileCount: 0,
    keyCount: 0,
    loading: true
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        // Get file count
        const filesRes = await axios.get('/api/files/', {
          headers: { Authorization: `Token ${token}` }
        });
        
        // Get key count
        const keysRes = await axios.get('/api/keys/', {
          headers: { Authorization: `Token ${token}` }
        });
        
        setStats({
          fileCount: filesRes.data.length,
          keyCount: keysRes.data.length,
          loading: false
        });
      } catch (err) {
        console.error('Error fetching stats:', err);
        setStats(prev => ({ ...prev, loading: false }));
      }
    };
    
    fetchStats();
  }, [token]);

  const DashboardCard = ({ title, count, icon, description, linkTo, linkText, color }) => (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Box sx={{ display: 'flex', mb: 2 }}>
          <Box sx={{ 
            backgroundColor: `${color}.light`, 
            borderRadius: '50%', 
            p: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mr: 2
          }}>
            {icon}
          </Box>
          <Typography variant="h5" component="div">
            {title}
          </Typography>
        </Box>
        
        <Typography variant="h3" color="text.primary" gutterBottom>
          {stats.loading ? <CircularProgress size={24} /> : count}
        </Typography>
        
        <Typography variant="body2" color="text.secondary">
          {description}
        </Typography>
      </CardContent>
      <CardActions>
        <Button 
          size="small" 
          component={RouterLink} 
          to={linkTo}
          variant="contained"
          fullWidth
        >
          {linkText}
        </Button>
      </CardActions>
    </Card>
  );

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>
              Welcome, {user?.username}!
            </Typography>
            <Typography variant="body1">
              This is your steganography dashboard. From here, you can manage your files, 
              encryption keys, and perform steganographic operations.
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <DashboardCard
            title="Files"
            count={stats.fileCount}
            icon={<FolderIcon sx={{ color: 'primary.main' }} />}
            description="Total files you've processed with steganography"
            linkTo="/files"
            linkText="Manage Files"
            color="primary"
          />
        </Grid>
        
        <Grid item xs={12} md={4}>
          <DashboardCard
            title="Encryption Keys"
            count={stats.keyCount}
            icon={<KeyIcon sx={{ color: 'secondary.main' }} />}
            description="Your encryption keys for secure steganography"
            linkTo="/keys"
            linkText="Manage Keys"
            color="secondary"
          />
        </Grid>
        
        <Grid item xs={12} md={4}>
          <DashboardCard
            title="Upload"
            count="New"
            icon={<UploadFileIcon sx={{ color: 'success.main' }} />}
            description="Upload files to hide or extract data"
            linkTo="/upload"
            linkText="Upload Now"
            color="success"
          />
        </Grid>
        
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              Quick Guide
            </Typography>
            <Typography variant="body1" paragraph>
              1. Generate encryption keys in the Keys section
            </Typography>
            <Typography variant="body1" paragraph>
              2. Upload a file and choose to embed or extract data
            </Typography>
            <Typography variant="body1" paragraph>
              3. Download your processed files from the Files section
            </Typography>
            <Typography variant="body1">
              All operations are performed securely with end-to-end encryption.
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;