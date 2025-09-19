// Authentication service for API calls
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

class AuthService {
  // Helper method to handle API responses
  async handleResponse(response) {
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.message || 'Something went wrong');
    }
    
    return data;
  }

  // Helper method to get auth headers
  getAuthHeaders() {
    const token = localStorage.getItem('authToken');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  // Login with email and password
  async login(email, password) {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      return this.handleResponse(response);
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  // Sign up new user
  async signup(userData) {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      return this.handleResponse(response);
    } catch (error) {
      console.error('Signup error:', error);
      throw error;
    }
  }

  // Logout
  async logout() {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
      });

      return this.handleResponse(response);
    } catch (error) {
      console.error('Logout error:', error);
      // Even if logout fails on server, we should clear local data
      return null;
    }
  }

  // Verify token
  async verifyToken(token) {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/verify`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      return this.handleResponse(response);
    } catch (error) {
      console.error('Token verification error:', error);
      throw error;
    }
  }

  // Google OAuth login
  async loginWithGoogle() {
    try {
      // In a real implementation, this would handle OAuth flow
      // For now, we'll simulate it
      window.open(`${API_BASE_URL}/auth/google`, 'googleAuth', 'width=500,height=600');
      
      // Listen for the OAuth callback
      return new Promise((resolve, reject) => {
        window.addEventListener('message', function handler(event) {
          if (event.origin !== window.location.origin) return;
          
          if (event.data.type === 'AUTH_SUCCESS') {
            window.removeEventListener('message', handler);
            resolve(event.data);
          } else if (event.data.type === 'AUTH_ERROR') {
            window.removeEventListener('message', handler);
            reject(new Error(event.data.error));
          }
        });
      });
    } catch (error) {
      console.error('Google login error:', error);
      throw error;
    }
  }

  // LinkedIn OAuth login
  async loginWithLinkedIn() {
    try {
      // Similar to Google OAuth
      window.open(`${API_BASE_URL}/auth/linkedin`, 'linkedinAuth', 'width=500,height=600');
      
      return new Promise((resolve, reject) => {
        window.addEventListener('message', function handler(event) {
          if (event.origin !== window.location.origin) return;
          
          if (event.data.type === 'AUTH_SUCCESS') {
            window.removeEventListener('message', handler);
            resolve(event.data);
          } else if (event.data.type === 'AUTH_ERROR') {
            window.removeEventListener('message', handler);
            reject(new Error(event.data.error));
          }
        });
      });
    } catch (error) {
      console.error('LinkedIn login error:', error);
      throw error;
    }
  }

  // Update user profile
  async updateProfile(profileData) {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/profile`, {
        method: 'PUT',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(profileData),
      });

      return this.handleResponse(response);
    } catch (error) {
      console.error('Profile update error:', error);
      throw error;
    }
  }

  // Forgot password - send reset email
  async forgotPassword(email) {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      return this.handleResponse(response);
    } catch (error) {
      console.error('Forgot password error:', error);
      throw error;
    }
  }

  // Reset password with token
  async resetPassword(token, newPassword) {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token, newPassword }),
      });

      return this.handleResponse(response);
    } catch (error) {
      console.error('Reset password error:', error);
      throw error;
    }
  }

  // Refresh authentication token
  async refreshToken() {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refreshToken }),
      });

      const data = await this.handleResponse(response);
      
      // Update stored tokens
      localStorage.setItem('authToken', data.token);
      if (data.refreshToken) {
        localStorage.setItem('refreshToken', data.refreshToken);
      }
      
      return data;
    } catch (error) {
      console.error('Token refresh error:', error);
      throw error;
    }
  }
}

// Create singleton instance
const authService = new AuthService();

// Add request interceptor to automatically refresh token if needed
const originalFetch = window.fetch;
window.fetch = async (...args) => {
  let response = await originalFetch(...args);
  
  if (response.status === 401 && args[0].includes(API_BASE_URL)) {
    try {
      // Try to refresh token
      await authService.refreshToken();
      
      // Retry original request with new token
      if (args[1] && args[1].headers) {
        args[1].headers.Authorization = `Bearer ${localStorage.getItem('authToken')}`;
      }
      
      response = await originalFetch(...args);
    } catch (error) {
      // Refresh failed, redirect to login
      window.location.href = '/login';
    }
  }
  
  return response;
};

export default authService;