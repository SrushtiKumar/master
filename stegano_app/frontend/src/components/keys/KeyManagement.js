import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import {
  Container, Box, Typography, Paper, Button, TextField,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Dialog, DialogActions, DialogContent, DialogTitle,
  FormControl, InputLabel, Select, MenuItem, CircularProgress, Alert
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DownloadIcon from '@mui/icons-material/Download';
import DeleteIcon from '@mui/icons-material/Delete';
import AuthContext from '../../context/AuthContext';

const KeyManagement = () => {
  const { token } = useContext(AuthContext);
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [newKey, setNewKey] = useState({
    name: '',
    key_type: 'AES-256',
    description: ''
  });

  const fetchKeys = async () => {
    try {
      const res = await axios.get('/api/keys/', {
        headers: { Authorization: `Token ${token}` }
      });
      setKeys(res.data);
      setError('');
    } catch (err) {
      setError('Failed to fetch keys');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, [token]);

  const handleOpenDialog = () => {
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setNewKey({
      name: '',
      key_type: 'AES-256',
      description: ''
    });
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewKey(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleCreateKey = async () => {
    try {
      await axios.post('/api/keys/generate/', newKey, {
        headers: { Authorization: `Token ${token}` }
      });
      setSuccess('Key created successfully');
      handleCloseDialog();
      fetchKeys();
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(
        err.response && err.response.data.detail
          ? err.response.data.detail
          : 'Failed to create key'
      );
    }
  };

  const handleDownloadKey = async (id) => {
    try {
      const res = await axios.get(`/api/keys/${id}/download/`, {
        headers: { Authorization: `Token ${token}` },
        responseType: 'blob'
      });
      
      // Create a download link
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Get key name from the keys array
      const keyObj = keys.find(k => k.id === id);
      const filename = keyObj ? `${keyObj.name}.key` : 'key.key';
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError('Failed to download key');
    }
  };

  const handleDeleteKey = async (id) => {
    if (window.confirm('Are you sure you want to delete this key? This action cannot be undone.')) {
      try {
        await axios.delete(`/api/keys/${id}/`, {
          headers: { Authorization: `Token ${token}` }
        });
        setSuccess('Key deleted successfully');
        fetchKeys();
        
        // Clear success message after 3 seconds
        setTimeout(() => setSuccess(''), 3000);
      } catch (err) {
        setError('Failed to delete key');
      }
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography component="h1" variant="h5">
              Encryption Keys
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleOpenDialog}
            >
              Generate New Key
            </Button>
          </Box>

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
              <CircularProgress />
            </Box>
          ) : keys.length === 0 ? (
            <Alert severity="info">
              You don't have any encryption keys yet. Generate a new key to get started.
            </Alert>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {keys.map((key) => (
                    <TableRow key={key.id}>
                      <TableCell>{key.name}</TableCell>
                      <TableCell>{key.key_type}</TableCell>
                      <TableCell>{key.description}</TableCell>
                      <TableCell>{new Date(key.created_at).toLocaleString()}</TableCell>
                      <TableCell>
                        <Button
                          startIcon={<DownloadIcon />}
                          onClick={() => handleDownloadKey(key.id)}
                          size="small"
                        >
                          Download
                        </Button>
                        <Button
                          startIcon={<DeleteIcon />}
                          color="error"
                          onClick={() => handleDeleteKey(key.id)}
                          size="small"
                        >
                          Delete
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>
      </Box>

      {/* New Key Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog}>
        <DialogTitle>Generate New Encryption Key</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            name="name"
            label="Key Name"
            type="text"
            fullWidth
            variant="outlined"
            value={newKey.name}
            onChange={handleInputChange}
            required
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Key Type</InputLabel>
            <Select
              name="key_type"
              value={newKey.key_type}
              label="Key Type"
              onChange={handleInputChange}
            >
              <MenuItem value="AES-256">AES-256</MenuItem>
              <MenuItem value="RSA-2048">RSA-2048</MenuItem>
              <MenuItem value="ChaCha20">ChaCha20</MenuItem>
            </Select>
          </FormControl>
          <TextField
            margin="dense"
            name="description"
            label="Description (Optional)"
            type="text"
            fullWidth
            variant="outlined"
            value={newKey.description}
            onChange={handleInputChange}
            multiline
            rows={2}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button 
            onClick={handleCreateKey} 
            variant="contained"
            disabled={!newKey.name || !newKey.key_type}
          >
            Generate
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default KeyManagement;