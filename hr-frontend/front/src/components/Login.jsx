import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Eye, EyeOff, Mail, Lock, AlertCircle, Loader, CheckCircle, ArrowLeft, KeyRound } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:5000";
const USE_MOCK_AUTH = false; // Set to false for production

// Mock user storage (keep for development/testing)
const getMockUsers = () => {
  const users = localStorage.getItem('mockUsers');
  if (!users) {
    const defaultUsers = {
      'test@example.com': {
        password: 'password123',
        firstName: 'Test',
        lastName: 'User',
        id: 'user-123'
      }
    };
    localStorage.setItem('mockUsers', JSON.stringify(defaultUsers));
    return defaultUsers;
  }
  return JSON.parse(users);
};

const saveMockUser = (email, userData) => {
  const users = getMockUsers();
  users[email] = userData;
  localStorage.setItem('mockUsers', JSON.stringify(users));
};

// Mock OTP storage
const saveOTP = (email, otp) => {
  const otpData = {
    otp: otp,
    timestamp: Date.now(),
    email: email
  };
  localStorage.setItem('passwordResetOTP', JSON.stringify(otpData));
};

const getStoredOTP = () => {
  const otpData = localStorage.getItem('passwordResetOTP');
  if (!otpData) return null;
  
  const parsed = JSON.parse(otpData);
  if (Date.now() - parsed.timestamp > 10 * 60 * 1000) {
    localStorage.removeItem('passwordResetOTP');
    return null;
  }
  return parsed;
};

// Mock authentication services
const mockRegister = async (userData) => {
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  const users = getMockUsers();
  
  if (users[userData.email]) {
    throw new Error('An account with this email already exists.');
  }
  
  const newUser = {
    id: 'user-' + Date.now(),
    firstName: userData.first_name,
    lastName: userData.last_name,
    email: userData.email,
    password: userData.password,
    createdAt: new Date().toISOString()
  };
  
  saveMockUser(userData.email, newUser);
  
  return {
    token: 'mock-jwt-token-' + Date.now(),
    user: {
      id: newUser.id,
      firstName: newUser.firstName,
      lastName: newUser.lastName,
      email: newUser.email,
      createdAt: newUser.createdAt
    }
  };
};

const mockLogin = async (credentials) => {
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  const users = getMockUsers();
  const user = users[credentials.email];
  
  if (!user) {
    throw new Error('Invalid email or password');
  }
  
  if (user.password !== credentials.password) {
    throw new Error('Invalid email or password');
  }
  
  return {
    token: 'mock-jwt-token-' + Date.now(),
    user: {
      id: user.id,
      firstName: user.firstName,
      lastName: user.lastName,
      email: user.email
    }
  };
};

const mockSendOTP = async (email) => {
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  const users = getMockUsers();
  if (!users[email]) {
    throw new Error('No account found with this email address');
  }
  
  const otp = Math.floor(100000 + Math.random() * 900000).toString();
  saveOTP(email, otp);
  
  console.log('Mock OTP sent:', otp);
  return { success: true, message: `OTP sent to ${email}` };
};

const mockVerifyOTP = async (email, otp) => {
  await new Promise(resolve => setTimeout(resolve, 500));
  
  const storedOTPData = getStoredOTP();
  if (!storedOTPData) {
    throw new Error('OTP has expired. Please request a new one.');
  }
  
  if (storedOTPData.email !== email) {
    throw new Error('Invalid OTP');
  }
  
  if (storedOTPData.otp !== otp) {
    throw new Error('Invalid OTP');
  }
  
  return { success: true, reset_token: 'mock-reset-token' };
};

const mockResetPassword = async (email, newPassword) => {
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  const users = getMockUsers();
  const user = users[email];
  
  if (!user) {
    throw new Error('User not found');
  }
  
  user.password = newPassword;
  saveMockUser(email, user);
  
  localStorage.removeItem('passwordResetOTP');
  
  return { success: true };
};

// Real backend authentication services
const sendOTPToEmail = async (email) => {
  const response = await fetch(`${BACKEND_URL}/api/forgot-password`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email })
  });
  
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.message || 'Failed to send OTP');
  }
  
  return data;
};

const verifyOTPCode = async (email, otp) => {
  const response = await fetch(`${BACKEND_URL}/api/verify-otp`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, otp })
  });
  
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.message || 'Invalid OTP');
  }
  
  return data;
};

const resetUserPassword = async (email, password, resetToken) => {
  const response = await fetch(`${BACKEND_URL}/api/reset-password`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ 
      email, 
      password,
      reset_token: resetToken 
    })
  });
  
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.message || 'Failed to reset password');
  }
  
  return data;
};

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated } = useAuth();
  const from = location.state?.from?.pathname || "/";

  const [isSignUp, setIsSignUp] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [formErrors, setFormErrors] = useState({});
  
  // Forgot Password states
  const [forgotPasswordMode, setForgotPasswordMode] = useState('');
  const [resetEmail, setResetEmail] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [resetToken, setResetToken] = useState('');
  
  // Sign In state
  const [signInData, setSignInData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });
  
  // Sign Up state
  const [signUpData, setSignUpData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    termsAccepted: false
  });

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  // Clear messages when switching forms
  useEffect(() => {
    setError('');
    setSuccess('');
    setFormErrors({});
  }, [isSignUp, forgotPasswordMode]);

  // Email validation
  const validateEmail = (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  };

  // Password validation
  const validatePassword = (password) => {
    return password.length >= 8;
  };

  // Handle OTP input
  const handleOtpChange = (value, index) => {
    if (value.length <= 1 && /^\d*$/.test(value)) {
      const newOtp = [...otp];
      newOtp[index] = value;
      setOtp(newOtp);
      
      if (value && index < 5) {
        const nextInput = document.getElementById(`otp-${index + 1}`);
        if (nextInput) nextInput.focus();
      }
    }
  };

  const handleOtpKeyDown = (e, index) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      const prevInput = document.getElementById(`otp-${index - 1}`);
      if (prevInput) prevInput.focus();
    }
  };

  const handleSendOTP = async (e) => {
    e.preventDefault();
    
    if (!resetEmail) {
      setError('Please enter your email address');
      return;
    }
    
    if (!validateEmail(resetEmail)) {
      setError('Please enter a valid email address');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const result = USE_MOCK_AUTH 
        ? await mockSendOTP(resetEmail)
        : await sendOTPToEmail(resetEmail);
        
      setSuccess(result.message || 'OTP sent successfully');
      setOtpSent(true);
      setForgotPasswordMode('otp');
      
      if (USE_MOCK_AUTH) {
        const storedOTP = getStoredOTP();
        alert(`Your OTP is: ${storedOTP.otp}\n(This is only shown in mock mode)`);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    
    const otpString = otp.join('');
    if (otpString.length !== 6) {
      setError('Please enter the complete 6-digit OTP');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const result = USE_MOCK_AUTH
        ? await mockVerifyOTP(resetEmail, otpString)
        : await verifyOTPCode(resetEmail, otpString);
        
      if (result.reset_token) {
        setResetToken(result.reset_token);
      }
      
      setSuccess('OTP verified successfully!');
      setForgotPasswordMode('reset');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    
    if (!newPassword) {
      setError('Please enter a new password');
      return;
    }
    
    if (!validatePassword(newPassword)) {
      setError('Password must be at least 8 characters');
      return;
    }
    
    if (newPassword !== confirmNewPassword) {
      setError('Passwords do not match');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const result = USE_MOCK_AUTH
        ? await mockResetPassword(resetEmail, newPassword)
        : await resetUserPassword(resetEmail, newPassword, resetToken);
        
      setSuccess('Password reset successfully! You can now sign in with your new password.');
      
      setTimeout(() => {
        setForgotPasswordMode('');
        setResetEmail('');
        setOtp(['', '', '', '', '', '']);
        setNewPassword('');
        setConfirmNewPassword('');
        setOtpSent(false);
        setResetToken('');
        setSignInData({...signInData, email: resetEmail});
      }, 2000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Validate sign in form
  const validateSignIn = () => {
    const errors = {};
    
    if (!signInData.email) {
      errors.email = 'Email is required';
    } else if (!validateEmail(signInData.email)) {
      errors.email = 'Invalid email format';
    }
    
    if (!signInData.password) {
      errors.password = 'Password is required';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Validate sign up form
  const validateSignUp = () => {
    const errors = {};
    
    if (!signUpData.firstName) {
      errors.firstName = 'First name is required';
    }
    
    if (!signUpData.lastName) {
      errors.lastName = 'Last name is required';
    }
    
    if (!signUpData.email) {
      errors.email = 'Email is required';
    } else if (!validateEmail(signUpData.email)) {
      errors.email = 'Invalid email format';
    }
    
    if (!signUpData.password) {
      errors.password = 'Password is required';
    } else if (!validatePassword(signUpData.password)) {
      errors.password = 'Password must be at least 8 characters';
    }
    
    if (!signUpData.confirmPassword) {
      errors.confirmPassword = 'Please confirm your password';
    } else if (signUpData.password !== signUpData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }
    
    if (!signUpData.termsAccepted) {
      errors.terms = 'You must accept the terms and conditions';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSignIn = async (e) => {
    e.preventDefault();
    
    if (!validateSignIn()) return;
    
    setLoading(true);
    setError('');
    
    try {
      let data;
      
      if (USE_MOCK_AUTH) {
        data = await mockLogin({
          email: signInData.email,
          password: signInData.password
        });
      } else {
        const response = await fetch(`${BACKEND_URL}/api/login`, {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify({
            email: signInData.email,
            password: signInData.password
          })
        });
        
        if (!response) {
          throw new Error('No response from server. Please check if the backend is running.');
        }
        
        data = await response.json();
        
        if (!response.ok) {
          if (response.status === 401) {
            throw new Error('Invalid email or password');
          } else if (response.status === 404) {
            throw new Error('Account not found. Please sign up first.');
          } else {
            throw new Error(data.message || 'Login failed. Please try again.');
          }
        }
      }
      
      setSuccess('Login successful! Redirecting...');
      await login(data.token, data.user, signInData.rememberMe);
      
    } catch (err) {
      console.error('Login error:', err);
      
      if (err.message.includes('fetch')) {
        setError(`Cannot connect to server. Please ensure the backend is running on ${BACKEND_URL}`);
      } else if (err.message.includes('JSON')) {
        setError('Invalid response from server. Please try again.');
      } else {
        setError(err.message || 'Unable to sign in. Please try again later.');
      }
      setLoading(false);
    }
  };

  const handleSignUp = async (e) => {
    e.preventDefault();
    
    if (!validateSignUp()) return;
    
    setLoading(true);
    setError('');
    
    try {
      let data;
      
      if (USE_MOCK_AUTH) {
        data = await mockRegister({
          first_name: signUpData.firstName,
          last_name: signUpData.lastName,
          email: signUpData.email,
          password: signUpData.password
        });
        
        setSuccess('Account created successfully! Redirecting...');
        await login(data.token, data.user, true);
        
      } else {
        const response = await fetch(`${BACKEND_URL}/api/register`, {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify({
            first_name: signUpData.firstName,
            last_name: signUpData.lastName,
            email: signUpData.email,
            password: signUpData.password
          })
        });
        
        if (!response) {
          throw new Error('No response from server. Please check if the backend is running.');
        }
        
        data = await response.json();
        
        if (response.ok) {
          setSuccess('Account created successfully! Redirecting...');
          
          await login(data.token || 'temp-token', data.user || {
            email: signUpData.email,
            firstName: signUpData.firstName,
            lastName: signUpData.lastName
          }, true);
          
        } else {
          if (response.status === 409) {
            throw new Error('An account with this email already exists.');
          } else if (response.status === 400) {
            throw new Error(data.message || 'Invalid data provided. Please check your inputs.');
          } else {
            throw new Error(data.message || 'Registration failed. Please try again.');
          }
        }
      }
    } catch (err) {
      console.error('Registration error:', err);
      
      if (err.message.includes('fetch')) {
        setError(`Cannot connect to server. Please ensure the backend is running on ${BACKEND_URL}`);
      } else if (err.message.includes('JSON')) {
        setError('Invalid response from server. Please try again.');
      } else if (err.message.includes('already exists')) {
        setError(err.message);
      } else {
        setError(err.message || 'An unexpected error occurred. Please try again.');
      }
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0">
        <div className="absolute top-0 -left-4 w-72 h-72 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
        <div className="absolute top-0 -right-4 w-72 h-72 bg-yellow-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-20 w-72 h-72 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      {/* Login Card */}
      <div className="relative bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 w-full max-w-md mx-4 border border-white/20">
        {/* Logo/Title */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">TalentFlow AI</h1>
          <p className="text-gray-300">
            {forgotPasswordMode === 'email' ? 'Reset your password' :
             forgotPasswordMode === 'otp' ? 'Enter verification code' :
             forgotPasswordMode === 'reset' ? 'Create new password' :
             isSignUp ? 'Create your account' : 'Sign in to continue'}
          </p>
          {USE_MOCK_AUTH && !forgotPasswordMode && (
            <p className="text-yellow-400 text-xs mt-2">
              (Using mock authentication - backend not connected)
            </p>
          )}
        </div>

        {/* Error/Success Messages */}
        {error && (
          <div className="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg flex items-start">
            <AlertCircle className="w-5 h-5 text-red-400 mr-2 flex-shrink-0 mt-0.5" />
            <span className="text-red-300 text-sm">{error}</span>
          </div>
        )}
        
        {success && (
          <div className="mb-4 p-3 bg-green-500/20 border border-green-500/50 rounded-lg flex items-start">
            <CheckCircle className="w-5 h-5 text-green-400 mr-2 flex-shrink-0 mt-0.5" />
            <span className="text-green-300 text-sm">{success}</span>
          </div>
        )}

        {/* Forgot Password Flow */}
        {forgotPasswordMode === 'email' && (
          <form onSubmit={handleSendOTP} className="space-y-4">
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  value={resetEmail}
                  onChange={(e) => setResetEmail(e.target.value)}
                  className="w-full pl-10 pr-3 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your email address"
                  disabled={loading}
                  autoFocus
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-medium rounded-lg hover:from-blue-600 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center"
            >
              {loading ? (
                <>
                  <Loader className="animate-spin w-5 h-5 mr-2" />
                  Sending OTP...
                </>
              ) : (
                'Send OTP'
              )}
            </button>

            <button
              type="button"
              onClick={() => setForgotPasswordMode('')}
              className="w-full text-center text-sm text-gray-300 hover:text-white flex items-center justify-center"
            >
              <ArrowLeft className="w-4 h-4 mr-1" />
              Back to sign in
            </button>
          </form>
        )}

        {forgotPasswordMode === 'otp' && (
          <form onSubmit={handleVerifyOTP} className="space-y-4">
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">
                Enter 6-digit OTP
              </label>
              <p className="text-gray-400 text-xs mb-4">
                We've sent a verification code to {resetEmail}
              </p>
              <div className="flex justify-between gap-2">
                {otp.map((digit, index) => (
                  <input
                    key={index}
                    id={`otp-${index}`}
                    type="text"
                    value={digit}
                    onChange={(e) => handleOtpChange(e.target.value, index)}
                    onKeyDown={(e) => handleOtpKeyDown(e, index)}
                    className="w-12 h-12 text-center bg-white/10 border border-white/20 rounded-lg text-white text-lg font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    maxLength="1"
                    disabled={loading}
                  />
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-medium rounded-lg hover:from-blue-600 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center"
            >
              {loading ? (
                <>
                  <Loader className="animate-spin w-5 h-5 mr-2" />
                  Verifying...
                </>
              ) : (
                'Verify OTP'
              )}
            </button>

            <button
              type="button"
              onClick={() => {
                setForgotPasswordMode('email');
                setOtp(['', '', '', '', '', '']);
              }}
              className="w-full text-center text-sm text-gray-300 hover:text-white"
            >
              Didn't receive OTP? Send again
            </button>
          </form>
        )}

        {forgotPasswordMode === 'reset' && (
          <form onSubmit={handleResetPassword} className="space-y-4">
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">
                New Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full pl-10 pr-10 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Minimum 8 characters"
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">
                Confirm New Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="password"
                  value={confirmNewPassword}
                  onChange={(e) => setConfirmNewPassword(e.target.value)}
                  className="w-full pl-10 pr-3 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Re-enter your new password"
                  disabled={loading}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-medium rounded-lg hover:from-blue-600 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center"
            >
              {loading ? (
                <>
                  <Loader className="animate-spin w-5 h-5 mr-2" />
                  Resetting password...
                </>
              ) : (
                'Reset Password'
              )}
            </button>
          </form>
        )}

        {/* Sign In and Sign Up forms remain the same */}
        {!isSignUp && !forgotPasswordMode && (
          <form onSubmit={handleSignIn} className="space-y-4">
            {/* Sign in form code stays the same */}
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  value={signInData.email}
                  onChange={(e) => setSignInData({...signInData, email: e.target.value})}
                  className={`w-full pl-10 pr-3 py-3 bg-white/10 border rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    formErrors.email ? 'border-red-500' : 'border-white/20'
                  }`}
                  placeholder="Enter your email"
                  disabled={loading}
                />
              </div>
              {formErrors.email && (
                <p className="mt-1 text-xs text-red-400">{formErrors.email}</p>
              )}
            </div>

            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={signInData.password}
                  onChange={(e) => setSignInData({...signInData, password: e.target.value})}
                  className={`w-full pl-10 pr-10 py-3 bg-white/10 border rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    formErrors.password ? 'border-red-500' : 'border-white/20'
                  }`}
                  placeholder="Enter your password"
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {formErrors.password && (
                <p className="mt-1 text-xs text-red-400">{formErrors.password}</p>
              )}
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={signInData.rememberMe}
                  onChange={(e) => setSignInData({...signInData, rememberMe: e.target.checked})}
                  className="w-4 h-4 bg-white/10 border-white/20 rounded text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-300">Remember me</span>
              </label>
              <button
                type="button"
                onClick={() => setForgotPasswordMode('email')}
                className="text-sm text-blue-400 hover:text-blue-300"
              >
                Forgot password?
              </button>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-medium rounded-lg hover:from-blue-600 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center"
            >
              {loading ? (
                <>
                  <Loader className="animate-spin w-5 h-5 mr-2" />
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </button>

            <p className="text-center text-gray-300 text-sm mt-6">
              Don't have an account?{' '}
              <button
                type="button"
                onClick={() => setIsSignUp(true)}
                className="text-blue-400 hover:text-blue-300 font-medium"
              >
                Create one
              </button>
            </p>
          </form>
        )}

        {isSignUp && !forgotPasswordMode && (
          <form onSubmit={handleSignUp} className="space-y-4">
            {/* Sign up form code stays the same */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-gray-300 text-sm font-medium mb-2">
                  First Name
                </label>
                <input
                  type="text"
                  value={signUpData.firstName}
                  onChange={(e) => setSignUpData({...signUpData, firstName: e.target.value})}
                  className={`w-full px-3 py-3 bg-white/10 border rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    formErrors.firstName ? 'border-red-500' : 'border-white/20'
                  }`}
                  placeholder="John"
                  disabled={loading}
                />
                {formErrors.firstName && (
                  <p className="mt-1 text-xs text-red-400">{formErrors.firstName}</p>
                )}
              </div>
              
              <div>
                <label className="block text-gray-300 text-sm font-medium mb-2">
                  Last Name
                </label>
                <input
                  type="text"
                  value={signUpData.lastName}
                  onChange={(e) => setSignUpData({...signUpData, lastName: e.target.value})}
                  className={`w-full px-3 py-3 bg-white/10 border rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    formErrors.lastName ? 'border-red-500' : 'border-white/20'
                  }`}
                  placeholder="Doe"
                  disabled={loading}
                />
                {formErrors.lastName && (
                  <p className="mt-1 text-xs text-red-400">{formErrors.lastName}</p>
                )}
              </div>
            </div>

            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  value={signUpData.email}
                  onChange={(e) => setSignUpData({...signUpData, email: e.target.value})}
                  className={`w-full pl-10 pr-3 py-3 bg-white/10 border rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    formErrors.email ? 'border-red-500' : 'border-white/20'
                  }`}
                  placeholder="john.doe@example.com"
                  disabled={loading}
                />
              </div>
              {formErrors.email && (
                <p className="mt-1 text-xs text-red-400">{formErrors.email}</p>
              )}
            </div>

            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={signUpData.password}
                  onChange={(e) => setSignUpData({...signUpData, password: e.target.value})}
                  className={`w-full pl-10 pr-10 py-3 bg-white/10 border rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    formErrors.password ? 'border-red-500' : 'border-white/20'
                  }`}
                  placeholder="Minimum 8 characters"
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {formErrors.password && (
                <p className="mt-1 text-xs text-red-400">{formErrors.password}</p>
              )}
            </div>

            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="password"
                  value={signUpData.confirmPassword}
                  onChange={(e) => setSignUpData({...signUpData, confirmPassword: e.target.value})}
                  className={`w-full pl-10 pr-3 py-3 bg-white/10 border rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    formErrors.confirmPassword ? 'border-red-500' : 'border-white/20'
                  }`}
                  placeholder="Re-enter your password"
                  disabled={loading}
                />
              </div>
              {formErrors.confirmPassword && (
                <p className="mt-1 text-xs text-red-400">{formErrors.confirmPassword}</p>
              )}
            </div>

            <div>
              <label className="flex items-start">
                <input
                  type="checkbox"
                  checked={signUpData.termsAccepted}
                  onChange={(e) => setSignUpData({...signUpData, termsAccepted: e.target.checked})}
                  className="w-4 h-4 bg-white/10 border-white/20 rounded text-blue-600 focus:ring-blue-500 mt-0.5"
                />
                <span className="ml-2 text-sm text-gray-300">
                  I agree to the{' '}
                  <a href="#" className="text-blue-400 hover:text-blue-300">Terms of Service</a>
                  {' '}and{' '}
                  <a href="#" className="text-blue-400 hover:text-blue-300">Privacy Policy</a>
                </span>
              </label>
              {formErrors.terms && (
                <p className="mt-1 text-xs text-red-400">{formErrors.terms}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-medium rounded-lg hover:from-blue-600 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center"
            >
              {loading ? (
                <>
                  <Loader className="animate-spin w-5 h-5 mr-2" />
                  Creating account...
                </>
              ) : (
                'Create Account'
              )}
            </button>

            <p className="text-center text-gray-300 text-sm mt-4">
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => setIsSignUp(false)}
                className="text-blue-400 hover:text-blue-300 font-medium"
              >
                Sign in
              </button>
            </p>
          </form>
        )}
      </div>
    </div>
  );
};

export default Login;