import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// Components
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import Dashboard from './components/dashboard/Dashboard';
import KeyManagement from './components/keys/KeyManagement';
import FileUpload from './components/files/FileUpload';
import FileList from './components/files/FileList';
import Navbar from './components/layout/Navbar';
import AuthContext from './context/AuthContext';

// Create theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
});

function App() {
  const [auth, setAuth] = useState({
    token: localStorage.getItem('token'),
    user: JSON.parse(localStorage.getItem('user')),
    isAuthenticated: !!localStorage.getItem('token'),
  });

  // Check if token is valid on app load
  useEffect(() => {
    if (auth.token) {
      // You could add a token validation API call here
    }
  }, [auth.token]);

  // Login function
  const login = (token, user) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    setAuth({
      token,
      user,
      isAuthenticated: true,
    });
  };

  // Logout function
  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setAuth({
      token: null,
      user: null,
      isAuthenticated: false,
    });
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthContext.Provider value={{ ...auth, login, logout }}>
        <Router>
          <Navbar />
          <Routes>
            <Route path="/login" element={!auth.isAuthenticated ? <Login /> : <Navigate to="/dashboard" />} />
            <Route path="/register" element={!auth.isAuthenticated ? <Register /> : <Navigate to="/dashboard" />} />
            <Route path="/dashboard" element={auth.isAuthenticated ? <Dashboard /> : <Navigate to="/login" />} />
            <Route path="/keys" element={auth.isAuthenticated ? <KeyManagement /> : <Navigate to="/login" />} />
            <Route path="/upload" element={auth.isAuthenticated ? <FileUpload /> : <Navigate to="/login" />} />
            <Route path="/files" element={auth.isAuthenticated ? <FileList /> : <Navigate to="/login" />} />
            <Route path="/" element={<Navigate to={auth.isAuthenticated ? "/dashboard" : "/login"} />} />
          </Routes>
        </Router>
      </AuthContext.Provider>
    </ThemeProvider>
  );
}

export default App;