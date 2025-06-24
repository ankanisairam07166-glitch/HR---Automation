import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { User } from 'lucide-react';

const Navigation = () => {
  const location = useLocation();
  
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
          </nav>
        </div>
        <div className="flex items-center space-x-4">
          <button className="p-1 rounded-full text-gray-500 hover:text-gray-900 hover:bg-gray-100">
            <User size={20} />
          </button>
        </div>
      </div>
    </header>
  );
};

export default Navigation;