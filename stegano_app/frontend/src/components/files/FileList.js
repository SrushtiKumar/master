import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import {
  Container, Box, Typography, Paper, Button, 
  Table, TableBody, TableCell, TableContainer, 
  TableHead, TableRow, CircularProgress, Alert
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import DeleteIcon from '@mui/icons-material/Delete';
import AuthContext from '../../context/AuthContext';

const FileList = () => {
  const { token } = useContext(AuthContext);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchFiles = async () => {
    try {
      const res = await axios.get('/api/files/', {
        headers: { Authorization: `Token ${token}` }
      });
      setFiles(res.data);
      setError('');
    } catch (err) {
      setError('Failed to fetch files');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, [token]);

  const handleDownload = async (id) => {
    try {
      const res = await axios.get(`/api/files/${id}/download/`, {
        headers: { Authorization: `Token ${token}` },
        responseType: 'blob'
      });
      
      // Create a download link
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Get filename from the response headers if available
      const contentDisposition = res.headers['content-disposition'];
      let filename = 'download';
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch.length === 2) {
          filename = filenameMatch[1];
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError('Failed to download file');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this file?')) {
      try {
        await axios.delete(`/api/files/${id}/`, {
          headers: { Authorization: `Token ${token}` }
        });
        // Refresh the file list
        fetchFiles();
      } catch (err) {
        setError('Failed to delete file');
      }
    }
  };

  const getFileTypeIcon = (fileType) => {
    switch (fileType) {
      case 'image':
        return '🖼️';
      case 'audio':
        return '🔊';
      case 'video':
        return '🎬';
      case 'document':
        return '📄';
      default:
        return '📁';
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography component="h1" variant="h5" gutterBottom>
            Your Files
          </Typography>

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
              <CircularProgress />
            </Box>
          ) : files.length === 0 ? (
            <Alert severity="info">
              You haven't uploaded any files yet. Go to the Upload page to get started.
            </Alert>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Type</TableCell>
                    <TableCell>Filename</TableCell>
                    <TableCell>Size</TableCell>
                    <TableCell>Uploaded</TableCell>
                    <TableCell>Has Payload</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {files.map((file) => (
                    <TableRow key={file.id}>
                      <TableCell>{getFileTypeIcon(file.file_type)}</TableCell>
                      <TableCell>{file.filename}</TableCell>
                      <TableCell>{Math.round(file.file_size / 1024)} KB</TableCell>
                      <TableCell>{new Date(file.created_at).toLocaleString()}</TableCell>
                      <TableCell>{file.has_payload ? 'Yes' : 'No'}</TableCell>
                      <TableCell>
                        <Button
                          startIcon={<DownloadIcon />}
                          onClick={() => handleDownload(file.id)}
                          size="small"
                        >
                          Download
                        </Button>
                        <Button
                          startIcon={<DeleteIcon />}
                          color="error"
                          onClick={() => handleDelete(file.id)}
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
    </Container>
  );
};

export default FileList;