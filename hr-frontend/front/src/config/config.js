// // 2. src/config/config.js (Configuration Management)
// // =====================================
// const config = {
//   api: {
//     baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000/api',
//     timeout: 30000,
//     retryAttempts: 3,
//     retryDelay: 1000,
//   },
  
//   app: {
//     env: process.env.REACT_APP_ENV || 'development',
//     enableMock: process.env.REACT_APP_ENABLE_MOCK === 'true',
//     sessionTimeout: parseInt(process.env.REACT_APP_SESSION_TIMEOUT) || 1800000,
//   },
  
//   security: {
//     maxLoginAttempts: parseInt(process.env.REACT_APP_MAX_LOGIN_ATTEMPTS) || 5,
//     lockoutDuration: parseInt(process.env.REACT_APP_LOCKOUT_DURATION) || 900000,
//     tokenKey: 'auth_token',
//     refreshTokenKey: 'refresh_token',
//     userKey: 'user_data',
//   },
  
//   features: {
//     socialLogin: process.env.REACT_APP_ENABLE_SOCIAL_LOGIN === 'true',
//     mfa: process.env.REACT_APP_ENABLE_MFA === 'true',
//     rememberMe: process.env.REACT_APP_ENABLE_REMEMBER_ME === 'true',
//   },
  
//   isDevelopment: () => config.app.env === 'development',
//   isProduction: () => config.app.env === 'production',
// };

// export default config;