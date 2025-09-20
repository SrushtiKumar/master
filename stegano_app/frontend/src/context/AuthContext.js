import { createContext } from 'react';

const AuthContext = createContext({
  token: null,
  user: null,
  isAuthenticated: false,
  login: () => {},
  logout: () => {},
});

export default AuthContext;