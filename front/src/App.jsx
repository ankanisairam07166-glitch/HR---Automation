import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import CandidateScreening from './components/CandidateScreening';
import SchedulerInterface from './components/SchedulerInterface';
import AssessmentInterface from './components/AssessmentInterface';
import InterviewSelection from './components/InterviewSelection';
import { AppProvider } from './context/AppContext';
import InterviewResults from './components/InterviewResults';
import './App.css';

function App() {
  return (
    <AppProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/candidates" element={<CandidateScreening />} />
            <Route path="/scheduler" element={<SchedulerInterface />} />
            <Route path="/assessments" element={<AssessmentInterface />} />
            <Route path="/interview/:candidateId" element={<InterviewSelection />} />
            <Route path="/interview-results" element={<InterviewResults />} />
          </Routes>
        </div>
      </Router>
    </AppProvider>
  );
}

export default App;