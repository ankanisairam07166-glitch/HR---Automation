import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { User, LogOut, Settings, ChevronDown } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Navigation = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSignOut = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <header className="bg-white border-b border-gray-200">
      <div className="flex items-center justify-between px-6 py-3">
        <div className="flex items-center">
          <div className="text-xl font-bold text-blue-600">TalentFlow AI</div>
          <nav className="ml-10 hidden md:flex space-x-8">
            <Link 
              to="/" 
              className={location.pathname === '/' ? "text-blue-600 font-medium" : "text-gray-500 hover:text-gray-900"}
            >
              Dashboard
            </Link>
            <Link 
              to="/candidates" 
              className={location.pathname === '/candidates' ? "text-blue-600 font-medium" : "text-gray-500 hover:text-gray-900"}
            >
              Candidates
            </Link>
            <Link 
              to="/scheduler" 
              className={location.pathname === '/scheduler' ? "text-blue-600 font-medium" : "text-gray-500 hover:text-gray-900"}
            >
              Scheduling
            </Link>
            <Link 
              to="/assessments" 
              className={location.pathname === '/assessments' ? "text-blue-600 font-medium" : "text-gray-500 hover:text-gray-900"}
            >
              Assessments
            </Link>
            <Link 
              to="/interview-results" 
              className={location.pathname === '/interview-results' ? "text-blue-600 font-medium" : "text-gray-500 hover:text-gray-900"}
            >
              Interview Results
            </Link>
          </nav>
        </div>
        
        {/* User Profile Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className="flex items-center space-x-2 p-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors duration-200"
          >
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
              {user?.firstName ? (
                <span className="text-white font-medium text-sm">
                  {user.firstName.charAt(0).toUpperCase()}
                </span>
              ) : (
                <User size={18} className="text-white" />
              )}
            </div>
            <ChevronDown size={16} className={`transition-transform duration-200 ${showDropdown ? 'rotate-180' : ''}`} />
          </button>

          {/* Dropdown Menu */}
          {showDropdown && (
            <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
              {/* User Info Section */}
              <div className="px-4 py-3 border-b border-gray-100">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                    {user?.firstName ? (
                      <span className="text-white font-medium">
                        {user.firstName.charAt(0).toUpperCase()}
                      </span>
                    ) : (
                      <User size={20} className="text-white" />
                    )}
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">
                      {user?.firstName && user?.lastName 
                        ? `${user.firstName} ${user.lastName}`
                        : 'User'
                      }
                    </div>
                    <div className="text-sm text-gray-500">{user?.email || 'user@example.com'}</div>
                  </div>
                </div>
              </div>

              {/* Menu Items */}
              <div className="py-1">
                <button
                  onClick={() => {
                    setShowDropdown(false);
                    // Navigate to profile/settings page when implemented
                    console.log('Navigate to settings');
                  }}
                  className="w-full flex items-center space-x-3 px-4 py-2 text-gray-700 hover:bg-gray-50 transition-colors duration-150"
                >
                  <Settings size={18} />
                  <span>Account Settings</span>
                </button>
                
                <div className="border-t border-gray-100 mt-1"></div>
                
                <button
                  onClick={handleSignOut}
                  className="w-full flex items-center space-x-3 px-4 py-2 text-red-600 hover:bg-red-50 transition-colors duration-150 mt-1"
                >
                  <LogOut size={18} />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Navigation;