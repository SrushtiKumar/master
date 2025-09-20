import React, { useContext } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import {
  AppBar, Toolbar, Typography, Button, Box,
  Container, IconButton, Menu, MenuItem
} from '@mui/material';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import AuthContext from '../../context/AuthContext';

const Navbar = () => {
  const { isAuthenticated, logout, user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = React.useState(null);

  const handleMenu = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    handleClose();
    navigate('/login');
  };

  return (
    <AppBar position="static">
      <Container maxWidth="xl">
        <Toolbar disableGutters>
          <Typography
            variant="h6"
            noWrap
            component={RouterLink}
            to="/"
            sx={{
              mr: 2,
              display: 'flex',
              fontFamily: 'monospace',
              fontWeight: 700,
              letterSpacing: '.3rem',
              color: 'inherit',
              textDecoration: 'none',
            }}
          >
            STEGANO
          </Typography>

          <Box sx={{ flexGrow: 1, display: 'flex' }}>
            {isAuthenticated && (
              <>
                <Button
                  component={RouterLink}
                  to="/dashboard"
                  sx={{ my: 2, color: 'white', display: 'block' }}
                >
                  Dashboard
                </Button>
                <Button
                  component={RouterLink}
                  to="/upload"
                  sx={{ my: 2, color: 'white', display: 'block' }}
                >
                  Upload
                </Button>
                <Button
                  component={RouterLink}
                  to="/files"
                  sx={{ my: 2, color: 'white', display: 'block' }}
                >
                  Files
                </Button>
                <Button
                  component={RouterLink}
                  to="/keys"
                  sx={{ my: 2, color: 'white', display: 'block' }}
                >
                  Keys
                </Button>
              </>
            )}
          </Box>

          <Box sx={{ flexGrow: 0 }}>
            {isAuthenticated ? (
              <>
                <IconButton
                  size="large"
                  aria-label="account of current user"
                  aria-controls="menu-appbar"
                  aria-haspopup="true"
                  onClick={handleMenu}
                  color="inherit"
                >
                  <AccountCircleIcon />
                  <Typography variant="body1" sx={{ ml: 1 }}>
                    {user?.username}
                  </Typography>
                </IconButton>
                <Menu
                  id="menu-appbar"
                  anchorEl={anchorEl}
                  anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'right',
                  }}
                  keepMounted
                  transformOrigin={{
                    vertical: 'top',
                    horizontal: 'right',
                  }}
                  open={Boolean(anchorEl)}
                  onClose={handleClose}
                >
                  <MenuItem onClick={handleLogout}>Logout</MenuItem>
                </Menu>
              </>
            ) : (
              <>
                <Button
                  component={RouterLink}
                  to="/login"
                  sx={{ color: 'white' }}
                >
                  Login
                </Button>
                <Button
                  component={RouterLink}
                  to="/register"
                  sx={{ color: 'white' }}
                >
                  Register
                </Button>
              </>
            )}
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
};

export default Navbar;