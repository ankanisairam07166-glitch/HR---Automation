// // 3. src/services/api.js (API Service with Interceptors)
// // =====================================
// import axios from 'axios';
// import config from '../config/config';

// class ApiService {
//   constructor() {
//     this.client = axios.create({
//       baseURL: config.api.baseURL,
//       timeout: config.api.timeout,
//       headers: {
//         'Content-Type': 'application/json',
//       },
//     });

//     this.setupInterceptors();
//   }

//   setupInterceptors() {
//     // Request interceptor
//     this.client.interceptors.request.use(
//       (config) => {
//         const token = this.getToken();
//         if (token) {
//           config.headers['Authorization'] = `Bearer ${token}`;
//         }
        
//         // Add CSRF token if available
//         const csrfToken = this.getCsrfToken();
//         if (csrfToken) {
//           config.headers['X-CSRF-Token'] = csrfToken;
//         }
        
//         return config;
//       },
//       (error) => {
//         return Promise.reject(error);
//       }
//     );

//     // Response interceptor
//     this.client.interceptors.response.use(
//       (response) => response,
//       async (error) => {
//         const originalRequest = error.config;

//         // Handle 401 - Unauthorized (token expired)
//         if (error.response?.status === 401 && !originalRequest._retry) {
//           originalRequest._retry = true;
          
//           try {
//             const refreshToken = this.getRefreshToken();
//             if (refreshToken) {
//               const response = await this.refreshAccessToken(refreshToken);
//               this.setToken(response.data.token);
//               originalRequest.headers['Authorization'] = `Bearer ${response.data.token}`;
//               return this.client(originalRequest);
//             }
//           } catch (refreshError) {
//             this.clearAuth();
//             window.location.href = '/login';
//             return Promise.reject(refreshError);
//           }
//         }

//         // Handle 429 - Too Many Requests
//         if (error.response?.status === 429) {
//           const retryAfter = error.response.headers['retry-after'];
//           error.message = `Too many requests. Please try again ${retryAfter ? `in ${retryAfter} seconds` : 'later'}.`;
//         }

//         // Handle network errors
//         if (!error.response) {
//           error.message = 'Network error. Please check your connection.';
//         }

//         return Promise.reject(error);
//       }
//     );
//   }

//   // Token management
//   getToken() {
//     return localStorage.getItem(config.security.tokenKey) || 
//            sessionStorage.getItem(config.security.tokenKey);
//   }

//   setToken(token, remember = false) {
//     if (remember) {
//       localStorage.setItem(config.security.tokenKey, token);
//     } else {
//       sessionStorage.setItem(config.security.tokenKey, token);
//     }
//   }

//   getRefreshToken() {
//     return localStorage.getItem(config.security.refreshTokenKey) || 
//            sessionStorage.getItem(config.security.refreshTokenKey);
//   }

//   getCsrfToken() {
//     return document.querySelector('meta[name="csrf-token"]')?.content;
//   }

//   clearAuth() {
//     localStorage.removeItem(config.security.tokenKey);
//     localStorage.removeItem(config.security.refreshTokenKey);
//     localStorage.removeItem(config.security.userKey);
//     sessionStorage.removeItem(config.security.tokenKey);
//     sessionStorage.removeItem(config.security.refreshTokenKey);
//     sessionStorage.removeItem(config.security.userKey);
//   }

//   async refreshAccessToken(refreshToken) {
//     return this.client.post('/auth/refresh', { refreshToken });
//   }

//   // API methods
//   async login(credentials) {
//     return this.client.post('/auth/login', credentials);
//   }

//   async register(userData) {
//     return this.client.post('/auth/register', userData);
//   }

//   async logout() {
//     const token = this.getToken();
//     if (token) {
//       await this.client.post('/auth/logout');
//     }
//     this.clearAuth();
//   }

//   async forgotPassword(email) {
//     return this.client.post('/auth/forgot-password', { email });
//   }

//   async resetPassword(token, password) {
//     return this.client.post('/auth/reset-password', { token, password });
//   }

//   async verifyEmail(token) {
//     return this.client.post('/auth/verify-email', { token });
//   }

//   async sendMfaCode(method) {
//     return this.client.post('/auth/mfa/send', { method });
//   }

//   async verifyMfaCode(code) {
//     return this.client.post('/auth/mfa/verify', { code });
//   }
// }

// export default new ApiService();