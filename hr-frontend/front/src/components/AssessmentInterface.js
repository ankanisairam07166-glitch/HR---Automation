import React, { useState, useEffect } from 'react';
import { Search, Filter, CheckCircle, XCircle, Clock, Calendar, Award, Send, ExternalLink, AlertCircle, RefreshCw, Download, BarChart, Eye, Activity, Target } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Navigation from './Navigation';
import ResultsManagement from './ResultsManagement'; // Import the new component

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:5000";

const AssessmentInterface = () => {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview'); // Updated to include overview
  const [message, setMessage] = useState('');
  const [selectedCandidates, setSelectedCandidates] = useState([]);
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [assessmentStats, setAssessmentStats] = useState({
    totalSent: 0,
    totalCompleted: 0,
    avgScore: 0,
    passRate: 0
  });

  useEffect(() => {
    fetchJobs();
  }, []);

  useEffect(() => {
    if (selectedJob) {
      fetchCandidates();
    }
  }, [selectedJob, activeTab]);

  const fetchJobs = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/jobs`);
      const data = await response.json();
      setJobs(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching jobs:', error);
      setJobs([]);
    }
  };

  const fetchCandidates = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/candidates?job_id=${selectedJob.id}`);
      const data = await response.json();
      
      // Calculate stats
      const assessmentCandidates = data.filter(c => c.exam_link_sent);
      const completed = assessmentCandidates.filter(c => c.exam_completed);
      const totalScore = completed.reduce((sum, c) => sum + (c.exam_percentage || 0), 0);
      const passed = completed.filter(c => c.exam_percentage >= 70);
      
      setAssessmentStats({
        totalSent: assessmentCandidates.length,
        totalCompleted: completed.length,
        avgScore: completed.length > 0 ? (totalScore / completed.length).toFixed(1) : 0,
        passRate: assessmentCandidates.length > 0 ? ((passed.length / assessmentCandidates.length) * 100).toFixed(1) : 0
      });
      
      setCandidates(data);
    } catch (error) {
      console.error('Error fetching candidates:', error);
      setCandidates([]);
    } finally {
      setLoading(false);
    }
  };

  const getFilteredCandidates = () => {
    return candidates.filter(candidate => {
      switch (activeTab) {
        case 'pending':
          return candidate.exam_link_sent && !candidate.exam_completed && !candidate.link_expired;
        case 'completed':
          return candidate.exam_completed;
        case 'expired':
          return candidate.exam_link_sent && !candidate.exam_completed && candidate.link_expired;
        case 'not_sent':
          return candidate.status === 'Shortlisted' && !candidate.exam_link_sent;
        case 'overview':
        case 'results':
          return true; // Show all for these tabs
        default:
          return false;
      }
    });
  };

  const sendAssessmentLink = async (candidateId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/send_assessment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_id: candidateId })
      });
      
      if (response.ok) {
        setMessage('Assessment link sent successfully!');
        fetchCandidates();
        setTimeout(() => setMessage(''), 3000);
      }
    } catch (error) {
      console.error('Error sending assessment:', error);
    }
  };

  const sendReminder = async (candidateId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/send_reminders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_ids: [candidateId] })
      });
      
      if (response.ok) {
        const data = await response.json();
        setMessage(`Reminder sent successfully to ${data.reminded_count} candidate(s)!`);
        setTimeout(() => setMessage(''), 3000);
      }
    } catch (error) {
      console.error('Error sending reminder:', error);
    }
  };

  const sendBulkReminders = async () => {
    const eligibleCandidates = getFilteredCandidates()
      .filter(c => c.exam_link_sent && !c.exam_completed && !c.link_expired)
      .map(c => c.id);
    
    if (eligibleCandidates.length === 0) {
      setMessage('No eligible candidates for reminders');
      setTimeout(() => setMessage(''), 3000);
      return;
    }
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/send_reminders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_ids: eligibleCandidates })
      });
      
      if (response.ok) {
        const data = await response.json();
        setMessage(`Sent reminders to ${data.reminded_count} candidates!`);
        setTimeout(() => setMessage(''), 3000);
      }
    } catch (error) {
      console.error('Error sending bulk reminders:', error);
    }
  };

  const exportResults = () => {
    const data = getFilteredCandidates().map(c => ({
      Name: c.name,
      Email: c.email,
      'Job Title': c.job_title,
      'Assessment Sent': c.exam_link_sent_date ? new Date(c.exam_link_sent_date).toLocaleDateString() : 'N/A',
      'Completed': c.exam_completed ? 'Yes' : 'No',
      'Score': c.exam_percentage ? `${c.exam_percentage}%` : 'N/A',
      'Status': c.exam_percentage >= 70 ? 'Passed' : c.exam_completed ? 'Failed' : 'Pending'
    }));
    
    // Convert to CSV
    const headers = Object.keys(data[0] || {});
    const csv = [
      headers.join(','),
      ...data.map(row => headers.map(h => `"${row[h]}"`).join(','))
    ].join('\n');
    
    // Download
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `assessment_results_${activeTab}_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  const getStatusDisplay = (candidate) => {
    if (candidate.exam_completed) {
      const passed = candidate.exam_percentage >= 70;
      return {
        text: passed ? 'Passed' : 'Failed',
        color: passed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800',
        icon: passed ? CheckCircle : XCircle
      };
    }
    
    if (candidate.link_expired) {
      return {
        text: 'Expired',
        color: 'bg-gray-100 text-gray-800',
        icon: Clock
      };
    }
    
    if (candidate.exam_started) {
      return {
        text: 'In Progress',
        color: 'bg-blue-100 text-blue-800',
        icon: Clock
      };
    }
    
    if (candidate.exam_link_sent) {
      return {
        text: 'Sent',
        color: 'bg-yellow-100 text-yellow-800',
        icon: Send
      };
    }
    
    return {
      text: 'Not Sent',
      color: 'bg-gray-100 text-gray-800',
      icon: AlertCircle
    };
  };

  const getTimeRemaining = (candidate) => {
    if (!candidate.exam_link_sent_date || candidate.exam_completed || candidate.link_expired) {
      return null;
    }
    
    const sentDate = new Date(candidate.exam_link_sent_date);
    const expiryDate = new Date(sentDate.getTime() + (48 * 60 * 60 * 1000)); // 48 hours
    const now = new Date();
    const hoursRemaining = Math.max(0, Math.floor((expiryDate - now) / (1000 * 60 * 60)));
    
    if (hoursRemaining <= 0) return 'Expired';
    if (hoursRemaining <= 6) return `${hoursRemaining}h remaining`;
    if (hoursRemaining <= 24) return `${hoursRemaining}h remaining`;
    return `${Math.floor(hoursRemaining / 24)}d remaining`;
  };

  const filteredCandidates = getFilteredCandidates();

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Navigation />
      
      <main className="flex-grow p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Assessment Management</h1>
            {selectedJob && (
              <p className="text-gray-600 mt-1">
                {selectedJob.title} • {selectedJob.location}
              </p>
            )}
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={fetchCandidates}
              className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            {filteredCandidates.length > 0 && activeTab !== 'overview' && activeTab !== 'results' && (
              <button
                onClick={exportResults}
                className="flex items-center px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                <Download className="w-4 h-4 mr-2" />
                Export
              </button>
            )}
          </div>
        </div>

        {/* Job Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Select Job Position</label>
          <select
            value={selectedJob?.id || ''}
            onChange={(e) => {
              const job = jobs.find(j => j.id == e.target.value);
              setSelectedJob(job || null);
            }}
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-full md:w-auto"
          >
            <option value="">Select a job...</option>
            {jobs.map(job => (
              <option key={job.id} value={job.id}>
                {job.title} - {job.location}
              </option>
            ))}
          </select>
        </div>

        {/* Success Message */}
        {message && (
          <div className="mb-4 p-4 bg-green-100 text-green-700 rounded-lg flex items-center">
            <CheckCircle className="w-5 h-5 mr-2" />
            {message}
          </div>
        )}

        {selectedJob && (
          <>
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Sent</p>
                    <p className="text-2xl font-bold text-gray-900">{assessmentStats.totalSent}</p>
                  </div>
                  <Send className="w-8 h-8 text-blue-600" />
                </div>
              </div>
              
              <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Completed</p>
                    <p className="text-2xl font-bold text-gray-900">{assessmentStats.totalCompleted}</p>
                  </div>
                  <CheckCircle className="w-8 h-8 text-green-600" />
                </div>
              </div>
              
              <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Average Score</p>
                    <p className="text-2xl font-bold text-gray-900">{assessmentStats.avgScore}%</p>
                  </div>
                  <BarChart className="w-8 h-8 text-purple-600" />
                </div>
              </div>
              
              <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Pass Rate</p>
                    <p className="text-2xl font-bold text-gray-900">{assessmentStats.passRate}%</p>
                  </div>
                  <Award className="w-8 h-8 text-yellow-600" />
                </div>
              </div>
            </div>

            {/* Tabs */}
            <div className="border-b border-gray-200 mb-6">
              <nav className="-mb-px flex space-x-8">
                <button
                  onClick={() => setActiveTab('overview')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'overview'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center">
                    <BarChart className="w-4 h-4 mr-2" />
                    Overview
                  </div>
                </button>
                <button
                  onClick={() => setActiveTab('results')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'results'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center">
                    <Activity className="w-4 h-4 mr-2" />
                    Results Management
                  </div>
                </button>
                <button
                  onClick={() => setActiveTab('pending')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'pending'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Pending ({candidates.filter(c => c.exam_link_sent && !c.exam_completed && !c.link_expired).length})
                </button>
                <button
                  onClick={() => setActiveTab('completed')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'completed'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Completed ({candidates.filter(c => c.exam_completed).length})
                </button>
                <button
                  onClick={() => setActiveTab('not_sent')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'not_sent'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Not Sent ({candidates.filter(c => c.status === 'Shortlisted' && !c.exam_link_sent).length})
                </button>
                <button
                  onClick={() => setActiveTab('expired')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'expired'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Expired ({candidates.filter(c => c.exam_link_sent && !c.exam_completed && c.link_expired).length})
                </button>
              </nav>
            </div>

            {/* Tab Content */}
            {activeTab === 'results' && (
              <ResultsManagement 
                selectedJob={selectedJob}
                candidates={candidates}
                onRefreshCandidates={fetchCandidates}
              />
            )}

            {activeTab === 'overview' && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Assessment Progress Chart */}
                <div className="bg-white rounded-lg shadow-sm border p-6">
                  <h3 className="text-lg font-semibold mb-4">Assessment Progress</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Sent</span>
                      <span className="font-medium">{assessmentStats.totalSent}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: '100%' }}
                      ></div>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Completed</span>
                      <span className="font-medium">{assessmentStats.totalCompleted}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-600 h-2 rounded-full" 
                        style={{ 
                          width: assessmentStats.totalSent > 0 
                            ? `${(assessmentStats.totalCompleted / assessmentStats.totalSent) * 100}%` 
                            : '0%' 
                        }}
                      ></div>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Passed (≥70%)</span>
                      <span className="font-medium">
                        {candidates.filter(c => c.exam_completed && c.exam_percentage >= 70).length}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-yellow-600 h-2 rounded-full" 
                        style={{ 
                          width: assessmentStats.totalSent > 0 
                            ? `${(candidates.filter(c => c.exam_completed && c.exam_percentage >= 70).length / assessmentStats.totalSent) * 100}%` 
                            : '0%' 
                        }}
                      ></div>
                    </div>
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="bg-white rounded-lg shadow-sm border p-6">
                  <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
                  <div className="space-y-3">
                    <button
                      onClick={() => setActiveTab('results')}
                      className="w-full flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex items-center">
                        <Activity className="w-5 h-5 text-blue-600 mr-3" />
                        <span className="font-medium">Check Results</span>
                      </div>
                      <span className="text-sm text-gray-500">
                        {candidates.filter(c => c.exam_link_sent && !c.exam_completed).length} pending
                      </span>
                    </button>
                    
                    <button
                      onClick={sendBulkReminders}
                      className="w-full flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex items-center">
                        <Send className="w-5 h-5 text-green-600 mr-3" />
                        <span className="font-medium">Send Reminders</span>
                      </div>
                      <span className="text-sm text-gray-500">Bulk action</span>
                    </button>
                    
                    <button
                      onClick={exportResults}
                      className="w-full flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex items-center">
                        <Download className="w-5 h-5 text-purple-600 mr-3" />
                        <span className="font-medium">Export Data</span>
                      </div>
                      <span className="text-sm text-gray-500">CSV format</span>
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Traditional Tabs Content */}
            {activeTab !== 'overview' && activeTab !== 'results' && (
              <>
                {/* Action Bar */}
                {activeTab === 'pending' && filteredCandidates.length > 0 && (
                  <div className="mb-4 flex justify-between items-center">
                    <p className="text-sm text-gray-600">
                      {filteredCandidates.length} candidates with pending assessments
                    </p>
                    <button
                      onClick={sendBulkReminders}
                      className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      <Send className="w-4 h-4 mr-2" />
                      Send Bulk Reminders
                    </button>
                  </div>
                )}

                {/* Candidates Table */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Candidate
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Status
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            ATS Score
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Sent Date
                          </th>
                          {activeTab === 'completed' && (
                            <>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Assessment Score
                              </th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Time Taken
                              </th>
                            </>
                          )}
                          {activeTab === 'pending' && (
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Time Remaining
                            </th>
                          )}
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {loading ? (
                          <tr>
                            <td colSpan={8} className="px-6 py-8 text-center">
                              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                              <p className="mt-2 text-gray-500">Loading...</p>
                            </td>
                          </tr>
                        ) : filteredCandidates.length === 0 ? (
                          <tr>
                            <td colSpan={8} className="px-6 py-8 text-center text-gray-500">
                              <Award className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                              <p className="text-lg font-medium">No assessments found</p>
                              <p className="mt-1">
                                {activeTab === 'not_sent' 
                                  ? 'Shortlist candidates to send assessments'
                                  : 'Select a different tab to view assessments'}
                              </p>
                            </td>
                          </tr>
                        ) : (
                          filteredCandidates.map((candidate) => {
                            const status = getStatusDisplay(candidate);
                            const StatusIcon = status.icon;
                            const timeRemaining = getTimeRemaining(candidate);
                            
                            return (
                              <tr key={candidate.id} className="hover:bg-gray-50">
                                <td className="px-6 py-4 whitespace-nowrap">
                                  <div>
                                    <div className="text-sm font-medium text-gray-900">{candidate.name}</div>
                                    <div className="text-sm text-gray-500">{candidate.email}</div>
                                  </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${status.color}`}>
                                    <StatusIcon className="w-3 h-3 mr-1" />
                                    {status.text}
                                  </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                  <span className={`text-sm font-medium ${
                                    candidate.ats_score >= 70 ? 'text-green-600' : 'text-red-600'
                                  }`}>
                                    {candidate.ats_score?.toFixed(0)}%
                                  </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                  {candidate.exam_link_sent_date 
                                    ? new Date(candidate.exam_link_sent_date).toLocaleDateString()
                                    : '—'}
                                </td>
                                {activeTab === 'completed' && (
                                  <>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                      <div className="flex items-center">
                                        <span className={`text-sm font-medium ${
                                          candidate.exam_percentage >= 70 ? 'text-green-600' : 'text-red-600'
                                        }`}>
                                          {candidate.exam_percentage?.toFixed(0)}%
                                        </span>
                                        <span className="ml-2 text-xs text-gray-500">
                                          ({candidate.exam_score}/{candidate.exam_total_questions})
                                        </span>
                                      </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                      {candidate.exam_time_taken ? `${candidate.exam_time_taken}m` : '—'}
                                    </td>
                                  </>
                                )}
                                {activeTab === 'pending' && (
                                  <td className="px-6 py-4 whitespace-nowrap">
                                    {timeRemaining && (
                                      <span className={`text-sm ${
                                        timeRemaining.includes('h') && parseInt(timeRemaining) <= 6
                                          ? 'text-red-600 font-medium'
                                          : 'text-gray-500'
                                      }`}>
                                        {timeRemaining}
                                      </span>
                                    )}
                                  </td>
                                )}
                                <td className="px-6 py-4 whitespace-nowrap text-sm">
                                  <div className="flex items-center space-x-2">
                                    {candidate.assessment_invite_link && (
                                      <a
                                        href={candidate.assessment_invite_link}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-600 hover:text-blue-900"
                                        title="View Assessment"
                                      >
                                        <ExternalLink className="w-4 h-4" />
                                      </a>
                                    )}
                                    
                                    {activeTab === 'not_sent' && (
                                      <button
                                        onClick={() => sendAssessmentLink(candidate.id)}
                                        className="text-blue-600 hover:text-blue-900"
                                        title="Send Assessment"
                                      >
                                        <Send className="w-4 h-4" />
                                      </button>
                                    )}
                                    
                                    {activeTab === 'pending' && !candidate.link_expired && (
                                      <button
                                        onClick={() => sendReminder(candidate.id)}
                                        className="text-yellow-600 hover:text-yellow-900"
                                        title="Send Reminder"
                                      >
                                        <AlertCircle className="w-4 h-4" />
                                      </button>
                                    )}
                                    
                                    {candidate.exam_completed && candidate.exam_percentage >= 70 && !candidate.interview_scheduled && (
                                      <button
                                        onClick={() => navigate(`/scheduler?candidate_id=${candidate.id}`)}
                                        className="text-green-600 hover:text-green-900"
                                        title="Schedule Interview"
                                      >
                                        <Calendar className="w-4 h-4" />
                                      </button>
                                    )}
                                  </div>
                                </td>
                              </tr>
                            );
                          })
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )}
          </>
        )}
        
        {!selectedJob && (
          <div className="bg-white rounded-lg p-8 shadow-sm border border-gray-200 text-center">
            <Award className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Job Position</h3>
            <p className="text-gray-500">Choose a job position from the dropdown above to manage assessments</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default AssessmentInterface;