import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  Container, Box, Typography, Button, Paper, Alert,
  TextField, FormControl, InputLabel, Select, MenuItem,
  CircularProgress, Grid
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import AuthContext from '../../context/AuthContext';

const FileUpload = () => {
  const { token } = useContext(AuthContext);
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [payload, setPayload] = useState('');
  const [key, setKey] = useState('');
  const [keys, setKeys] = useState([]);
  const [operation, setOperation] = useState('embed');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [fileType, setFileType] = useState('');

  // Fetch user's keys on component mount
  React.useEffect(() => {
    const fetchKeys = async () => {
      try {
        const res = await axios.get('/api/keys/', {
          headers: { Authorization: `Token ${token}` }
        });
        setKeys(res.data);
        if (res.data.length > 0) {
          setKey(res.data[0].id);
        }
      } catch (err) {
        setError('Failed to fetch encryption keys');
      }
    };
    
    fetchKeys();
  }, [token]);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      
      // Determine file type
      const fileName = selectedFile.name.toLowerCase();
      if (fileName.endsWith('.jpg') || fileName.endsWith('.jpeg') || 
          fileName.endsWith('.png') || fileName.endsWith('.bmp')) {
        setFileType('image');
      } else if (fileName.endsWith('.mp3') || fileName.endsWith('.wav')) {
        setFileType('audio');
      } else if (fileName.endsWith('.mp4') || fileName.endsWith('.avi')) {
        setFileType('video');
      } else if (fileName.endsWith('.pdf') || fileName.endsWith('.docx')) {
        setFileType('document');
      } else {
        setFileType('unknown');
        setError('Unsupported file type. Please upload an image, audio, video, or document file.');
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    if (!file) {
      setError('Please select a file');
      setLoading(false);
      return;
    }

    if (operation === 'embed' && !payload) {
      setError('Please enter a payload to embed');
      setLoading(false);
      return;
    }

    if (!key) {
      setError('Please select an encryption key');
      setLoading(false);
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('operation', operation);
    
    if (operation === 'embed') {
      formData.append('payload', payload);
    }
    
    formData.append('key_id', key);

    try {
      const endpoint = operation === 'embed' ? '/api/files/embed/' : '/api/files/extract/';
      const res = await axios.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Token ${token}`
        }
      });

      if (operation === 'embed') {
        setSuccess('File processed successfully! Your steganographic file is ready for download.');
        // Navigate to file list to see the processed file
        setTimeout(() => navigate('/files'), 2000);
      } else {
        setSuccess(`Extracted payload: ${res.data.payload}`);
      }
    } catch (err) {
      setError(
        err.response && err.response.data.detail
          ? err.response.data.detail
          : 'An error occurred while processing your file'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography component="h1" variant="h5" gutterBottom>
            {operation === 'embed' ? 'Hide Data in File' : 'Extract Data from File'}
          </Typography>

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Operation</InputLabel>
                  <Select
                    value={operation}
                    label="Operation"
                    onChange={(e) => setOperation(e.target.value)}
                  >
                    <MenuItem value="embed">Embed Data</MenuItem>
                    <MenuItem value="extract">Extract Data</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <Button
                  variant="outlined"
                  component="label"
                  fullWidth
                  startIcon={<CloudUploadIcon />}
                  sx={{ py: 2 }}
                >
                  {file ? file.name : 'Select File'}
                  <input
                    type="file"
                    hidden
                    onChange={handleFileChange}
                  />
                </Button>
                {fileType && fileType !== 'unknown' && (
                  <Typography variant="caption" color="text.secondary">
                    Detected file type: {fileType}
                  </Typography>
                )}
              </Grid>

              {operation === 'embed' && (
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Data to Hide"
                    multiline
                    rows={4}
                    value={payload}
                    onChange={(e) => setPayload(e.target.value)}
                    placeholder="Enter the secret message you want to hide in the file"
                  />
                </Grid>
              )}

              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Encryption Key</InputLabel>
                  <Select
                    value={key}
                    label="Encryption Key"
                    onChange={(e) => setKey(e.target.value)}
                  >
                    {keys.map((k) => (
                      <MenuItem key={k.id} value={k.id}>
                        {k.name} ({k.key_type})
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  disabled={loading || !file || (operation === 'embed' && !payload) || !key}
                  sx={{ mt: 2 }}
                >
                  {loading ? (
                    <CircularProgress size={24} />
                  ) : operation === 'embed' ? (
                    'Hide Data'
                  ) : (
                    'Extract Data'
                  )}
                </Button>
              </Grid>
            </Grid>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default FileUpload;