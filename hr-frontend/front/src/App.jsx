import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { AppProvider } from './context/AppContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import CandidateScreening from './components/CandidateScreening';
import SchedulerInterface from './components/SchedulerInterface';
import AssessmentInterface from './components/AssessmentInterface';
import InterviewSelection from './components/InterviewSelection';
import InterviewResults from './components/InterviewResults';
import './App.css';

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppProvider>
          <div className="App">
            <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<Login />} />
              
              {/* Protected Routes */}
              <Route path="/" element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              } />
              <Route path="/candidates" element={
                <ProtectedRoute>
                  <CandidateScreening />
                </ProtectedRoute>
              } />
              <Route path="/scheduler" element={
                <ProtectedRoute>
                  <SchedulerInterface />
                </ProtectedRoute>
              } />
              <Route path="/assessments" element={
                <ProtectedRoute>
                  <AssessmentInterface />
                </ProtectedRoute>
              } />
              <Route path="/interview/:candidateId" element={
                <ProtectedRoute>
                  <InterviewSelection />
                </ProtectedRoute>
              } />
              <Route path="/interview-results" element={
                <ProtectedRoute>
                  <InterviewResults />
                </ProtectedRoute>
              } />
              
              {/* Redirect any unknown routes to login */}
              <Route path="*" element={<Navigate to="/login" replace />} />
            </Routes>
          </div>
        </AppProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;