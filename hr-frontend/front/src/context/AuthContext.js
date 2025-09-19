// AuthContext.js
import React, { createContext, useState, useContext, useEffect } from 'react';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  // Initialize auth state from storage on mount
  useEffect(() => {
    const initializeAuth = () => {
      try {
        const storedToken = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
        const storedUser = localStorage.getItem('user') || sessionStorage.getItem('user');

        if (storedToken && storedUser) {
          setToken(storedToken);
          setUser(JSON.parse(storedUser));
          setIsAuthenticated(true);
        }
      } catch (error) {
        console.error('Error initializing auth:', error);
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (authToken, userData, rememberMe = false) => {
    try {
      // Store token and user data
      if (rememberMe) {
        localStorage.setItem('authToken', authToken);
        localStorage.setItem('user', JSON.stringify(userData));
      } else {
        sessionStorage.setItem('authToken', authToken);
        sessionStorage.setItem('user', JSON.stringify(userData));
      }

      setToken(authToken);
      setUser(userData);
      setIsAuthenticated(true);
      
      return true;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      // Clear all auth data from storage
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      sessionStorage.removeItem('authToken');
      sessionStorage.removeItem('user');

      // If you have a backend logout endpoint, call it here
      // const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:5000";
      // if (token) {
      //   try {
      //     await fetch(`${BACKEND_URL}/api/logout`, {
      //       method: 'POST',
      //       headers: {
      //         'Authorization': `Bearer ${token}`,
      //         'Content-Type': 'application/json'
      //       }
      //     });
      //   } catch (error) {
      //     console.error('Backend logout error:', error);
      //   }
      // }

      // Clear state
      setToken(null);
      setUser(null);
      setIsAuthenticated(false);

    } catch (error) {
      console.error('Logout error:', error);
      // Even if there's an error, still clear local state
      setToken(null);
      setUser(null);
      setIsAuthenticated(false);
      throw error;
    }
  };

  const updateUser = (userData) => {
    setUser(userData);
    
    // Update stored user data
    const storedInLocal = localStorage.getItem('authToken');
    if (storedInLocal) {
      localStorage.setItem('user', JSON.stringify(userData));
    } else {
      sessionStorage.setItem('user', JSON.stringify(userData));
    }
  };

  const value = {
    user,
    token,
    isAuthenticated,
    loading,
    login,
    logout,
    updateUser
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};