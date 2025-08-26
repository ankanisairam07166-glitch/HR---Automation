// InterviewResults.jsx - Production Ready with Real-time Updates
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  Video, Calendar, Clock, Award, BarChart, Download, 
  Eye, TrendingUp, AlertCircle, CheckCircle, XCircle,
  Mic, FileText, Target, Users, Search, Filter,
  MessageSquare, X, ChevronRight, PlayCircle, RefreshCw,
  Activity, Wifi, WifiOff, CircleDot, Home, FileSpreadsheet, 
  UserPlus, AlertTriangle, Loader, User, Mail, Briefcase,
  Phone, MapPin, ChevronDown, ChevronUp, ExternalLink
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Navigation from './Navigation';
import { BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Legend, RadialBarChart, RadialBar } from 'recharts';

// Configuration
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:5000";
const POLLING_INTERVAL = 5000;
const SCORE_CHECK_INTERVAL = 10000;
const AUTO_REFRESH_INTERVAL = 30000;
const API_TIMEOUT = 15000;
const REALTIME_UPDATE_INTERVAL = 5000; // Real-time polling interval

const InterviewResults = () => {
  const navigate = useNavigate();
  
  // State Management
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [selectedCandidateId, setSelectedCandidateId] = useState(null);
  const [selectedCandidateDetails, setSelectedCandidateDetails] = useState(null);
  const [showCandidateModal, setShowCandidateModal] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [liveStatuses, setLiveStatuses] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedRows, setExpandedRows] = useState({});
  const [activeTab, setActiveTab] = useState('overview');
  
  // Real-time update states
  const [realtimeUpdates, setRealtimeUpdates] = useState([]);
  const [isPollingActive, setIsPollingActive] = useState(true);
  const [processingCandidates, setProcessingCandidates] = useState(new Set());
  
  // Refs for interval management
  const pollingIntervalRef = useRef(null);
  const scoreCheckIntervalRef = useRef(null);
  const autoRefreshIntervalRef = useRef(null);
  const realtimePollingRef = useRef(null);
  const retryCountRef = useRef(0);
  const maxRetries = 5;

  // Fetch with timeout utility
  const fetchWithTimeout = async (url, options = {}, timeout = API_TIMEOUT) => {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    
    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });
      clearTimeout(id);
      return response;
    } catch (error) {
      clearTimeout(id);
      if (error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      throw error;
    }
  };

  // Parse candidate data safely
  const safeParseCandidate = (candidate) => {
    if (!candidate || typeof candidate !== 'object') return null;
    
    return {
      id: candidate.id || null,
      name: candidate.name || 'Unknown',
      email: candidate.email || '',
      phone: candidate.phone || '',
      location: candidate.location || '',
      job_title: candidate.job_title || candidate.role || 'Position Not Specified',
      experience: candidate.experience || '',
      skills: candidate.skills || [],
      resume_url: candidate.resume_url || '',
      interview_date: candidate.interview_date || null,
      interview_scheduled: Boolean(candidate.interview_scheduled),
      interview_started_at: candidate.interview_started_at || null,
      interview_completed_at: candidate.interview_completed_at || null,
      interview_duration: candidate.interview_duration || 0,
      interview_ai_score: candidate.interview_ai_score !== null && candidate.interview_ai_score !== undefined 
            ? parseFloat(candidate.interview_ai_score) : null,
      interview_ai_technical_score: candidate.interview_ai_technical_score !== null && candidate.interview_ai_technical_score !== undefined
            ? parseFloat(candidate.interview_ai_technical_score) : null,
      interview_ai_communication_score: candidate.interview_ai_communication_score !== null && candidate.interview_ai_communication_score !== undefined
            ? parseFloat(candidate.interview_ai_communication_score) : null,
      interview_ai_problem_solving_score: candidate.interview_ai_problem_solving_score !== null && candidate.interview_ai_problem_solving_score !== undefined
            ? parseFloat(candidate.interview_ai_problem_solving_score) : null,
      interview_ai_cultural_fit_score: candidate.interview_ai_cultural_fit_score !== null && candidate.interview_ai_cultural_fit_score !== undefined
            ? parseFloat(candidate.interview_ai_cultural_fit_score) : null,
      interview_ai_overall_feedback: candidate.interview_ai_overall_feedback || '',
      interview_ai_analysis_status: candidate.interview_ai_analysis_status || null,
      interview_final_status: candidate.interview_final_status || null,
      interview_recording_url: candidate.interview_recording_url || null,
      interview_token: candidate.interview_token || null,
      interview_progress: parseFloat(candidate.interview_progress) || 0,
      interview_questions_answered: parseInt(candidate.interview_questions_answered) || 0,
      interview_total_questions: parseInt(candidate.interview_total_questions) || 0,
      strengths: tryParseJSON(candidate.interview_ai_strengths) || candidate.strengths || [],
      weaknesses: tryParseJSON(candidate.interview_ai_weaknesses) || candidate.weaknesses || [],
      recommendations: tryParseJSON(candidate.interview_recommendations) || candidate.recommendations || []
    };
  };

  const tryParseJSON = (jsonString) => {
    try {
        return JSON.parse(jsonString);
    } catch (e) {
        return null;
    }
  };

  // Real-time update handler
  const handleRealtimeUpdate = useCallback((update) => {
    // Update candidate in state with animation flag
    setCandidates(prev => prev.map(candidate => {
      if (candidate.id === update.candidate_id) {
        // Remove from processing set
        setProcessingCandidates(prev => {
          const newSet = new Set(prev);
          newSet.delete(candidate.id);
          return newSet;
        });
        
        return {
          ...candidate,
          interview_ai_score: update.scores?.overall || candidate.interview_ai_score,
          interview_ai_technical_score: update.scores?.technical || candidate.interview_ai_technical_score,
          interview_ai_communication_score: update.scores?.communication || candidate.interview_ai_communication_score,
          interview_ai_problem_solving_score: update.scores?.problem_solving || candidate.interview_ai_problem_solving_score,
          interview_ai_cultural_fit_score: update.scores?.cultural_fit || candidate.interview_ai_cultural_fit_score,
          interview_ai_analysis_status: 'completed',
          interview_final_status: update.final_status || candidate.interview_final_status,
          _updated: true, // Mark for animation
          _updateTime: new Date().getTime()
        };
      }
      return candidate;
    }));
    
    // Show notification
    showAnalysisCompleteNotification(update);
  }, []);

  // Poll for real-time updates
  const pollForRealtimeUpdates = useCallback(async () => {
    if (!isPollingActive) return;
    
    try {
      const response = await fetchWithTimeout(`${BACKEND_URL}/api/interview/poll-updates`, {
        headers: {
          'Cache-Control': 'no-cache'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.updates && data.updates.length > 0) {
          setRealtimeUpdates(prev => [...prev, ...data.updates]);
          
          // Process each update
          data.updates.forEach(update => {
            handleRealtimeUpdate(update);
          });
        }
        
        // Reset retry count on success
        retryCountRef.current = 0;
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error('Real-time polling error:', error);
      
      // Exponential backoff
      retryCountRef.current++;
      if (retryCountRef.current >= maxRetries) {
        setIsPollingActive(false);
        console.error('Max retries reached for real-time updates, stopping polling');
      }
    }
  }, [isPollingActive, handleRealtimeUpdate]);

  // Show notification for completed analysis
  const showAnalysisCompleteNotification = (update) => {
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-green-600 text-white px-6 py-4 rounded-lg shadow-lg transform transition-all duration-500 translate-x-full z-50';
    notification.innerHTML = `
      <div class="flex items-center">
        <svg class="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        <div>
          <p class="font-semibold">Analysis Complete!</p>
          <p class="text-sm">Candidate ${update.candidate_id} - Score: ${update.scores?.overall || 0}%</p>
        </div>
      </div>
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
      notification.classList.remove('translate-x-full');
    }, 100);
    
    // Remove after 5 seconds
    setTimeout(() => {
      notification.classList.add('translate-x-full');
      setTimeout(() => {
        if (document.body.contains(notification)) {
          document.body.removeChild(notification);
        }
      }, 500);
    }, 5000);
  };

  // Fetch all interview results
  const fetchInterviewResults = useCallback(async (silent = false) => {
    if (!silent) {
      setLoading(true);
      setError(null);
    }
    
    try {
      const response = await fetchWithTimeout(`${BACKEND_URL}/api/candidates`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (!Array.isArray(data)) {
        throw new Error('Invalid data format received');
      }
      
      const parsedCandidates = data
        .map(safeParseCandidate)
        .filter(c => c !== null)
        .filter(c => 
          c.interview_scheduled || 
          c.interview_started_at || 
          c.interview_completed_at || 
          c.interview_ai_score ||
          c.interview_token
        );
      
      // Track candidates in processing state
      const newProcessingCandidates = new Set();
      parsedCandidates.forEach(candidate => {
        if (candidate.interview_ai_analysis_status === 'processing') {
          newProcessingCandidates.add(candidate.id);
        }
      });
      setProcessingCandidates(newProcessingCandidates);
      
      setCandidates(parsedCandidates);
      setLastRefresh(new Date());
      
      // Store in database if needed
      await storeCandidatesInDB(parsedCandidates);
      
    } catch (error) {
      console.error('Error fetching interview results:', error);
      if (!silent) {
        setError(`Failed to load interview results: ${error.message}`);
      }
    } finally {
      if (!silent) setLoading(false);
    }
  }, []);

  // Store candidates in database
  const storeCandidatesInDB = async (candidatesData) => {
    try {
      await fetchWithTimeout(`${BACKEND_URL}/api/interview-results/store`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ candidates: candidatesData })
      });
    } catch (error) {
      console.error('Error storing candidates:', error);
    }
  };

  // Fetch individual candidate details
  const fetchCandidateDetails = async (candidateId) => {
    try {
      setLoading(true);
      
      // Fetch complete candidate details
      const [candidateRes, analysisRes, qaRes, progressRes] = await Promise.all([
        fetchWithTimeout(`${BACKEND_URL}/api/candidates/${candidateId}`),
        fetchWithTimeout(`${BACKEND_URL}/api/interview/analysis/${candidateId}`),
        fetchWithTimeout(`${BACKEND_URL}/api/interview/qa/get/${candidateId}`),
        fetchWithTimeout(`${BACKEND_URL}/api/interview/progress/${candidateId}`)
      ]);
      
      const candidateData = candidateRes.ok ? await candidateRes.json() : null;
      const analysisData = analysisRes.ok ? await analysisRes.json() : null;
      const qaData = qaRes.ok ? await qaRes.json() : null;
      const progressData = progressRes.ok ? await progressRes.json() : null;
      
      const completeDetails = {
        candidate: safeParseCandidate(candidateData || candidates.find(c => c.id === candidateId)),
        analysis: analysisData || null,
        qa_data: qaData?.qa_data || null,
        progress: progressData || null,
        timestamp: new Date().toISOString()
      };
      
      setSelectedCandidateDetails(completeDetails);
      setShowCandidateModal(true);
      
      // Store this view in database
      await storeViewHistory(candidateId);
      
    } catch (error) {
      console.error('Error fetching candidate details:', error);
      alert('Failed to load candidate details. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Store view history
  const storeViewHistory = async (candidateId) => {
    try {
      await fetchWithTimeout(`${BACKEND_URL}/api/interview-results/view-history`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          candidate_id: candidateId,
          viewed_at: new Date().toISOString()
        })
      });
    } catch (error) {
      console.error('Error storing view history:', error);
    }
  };

  // Poll live interview updates
  const pollLiveUpdates = useCallback(async () => {
    const activeCandidates = candidates.filter(c => 
      c && c.interview_started_at && !c.interview_completed_at
    );
    
    if (activeCandidates.length === 0) return;
    
    for (const candidate of activeCandidates) {
      if (!candidate.id) continue;
      
      try {
        const response = await fetchWithTimeout(
          `${BACKEND_URL}/api/interview/live-status/${candidate.id}`,
          {},
          5000
        );
        
        if (response.ok) {
          const status = await response.json();
          if (status && typeof status === 'object') {
            setLiveStatuses(prev => ({
              ...prev,
              [candidate.id]: {
                is_active: Boolean(status.is_active),
                connection_quality: status.connection_quality || 'unknown',
                progress: parseFloat(status.progress) || 0,
                current_question: status.current_question || '',
                answered_questions: parseInt(status.answered_questions) || 0,
                total_questions: parseInt(status.total_questions) || 0,
                duration: parseInt(status.duration) || 0,
                interview_status: status.interview_status || 'unknown',
                analysis_status: status.analysis_status || null,
                ai_score: parseFloat(status.ai_score) || null
              }
            }));
            
            // Update progress in database
            await updateProgressInDB(candidate.id, status);
          }
        }
      } catch (error) {
        console.error(`Error polling candidate ${candidate.id}:`, error);
      }
    }
  }, [candidates]);

  // Update progress in database
  const updateProgressInDB = async (candidateId, progressData) => {
    try {
      await fetchWithTimeout(`${BACKEND_URL}/api/interview-results/update-progress`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          candidate_id: candidateId,
          progress: progressData
        })
      });
    } catch (error) {
      console.error('Error updating progress:', error);
    }
  };

  // Get interview status with processing state
  const getInterviewStatus = useCallback((candidate) => {
    if (!candidate) {
      return { text: 'Unknown', color: 'bg-gray-100 text-gray-800', icon: AlertCircle };
    }
    
    // Check if currently processing
    if (candidate.interview_ai_analysis_status === 'processing' || processingCandidates.has(candidate.id)) {
      return { 
        text: 'Analyzing...', 
        color: 'bg-purple-100 text-purple-800 animate-pulse', 
        icon: () => <Loader className="w-4 h-4 animate-spin" />
      };
    }
    
    const hasInterviewData = candidate.interview_scheduled || 
                            candidate.interview_started_at || 
                            candidate.interview_completed_at ||
                            candidate.interview_ai_score ||
                            candidate.interview_token;
    
    if (!hasInterviewData) {
      return { text: 'Not Scheduled', color: 'bg-gray-100 text-gray-800', icon: XCircle };
    }
    
    if (candidate.interview_completed_at) {
      if (candidate.interview_ai_score !== null && candidate.interview_ai_score > 0) {
        if (candidate.interview_ai_score >= 70) {
          return { text: 'Passed', color: 'bg-green-100 text-green-800', icon: CheckCircle };
        } else {
          return { text: 'Failed', color: 'bg-red-100 text-red-800', icon: XCircle };
        }
      }
      return { text: 'Pending Analysis', color: 'bg-yellow-100 text-yellow-800', icon: Clock };
    }
    
    if (candidate.interview_started_at && !candidate.interview_completed_at) {
      return { text: 'In Progress', color: 'bg-blue-100 text-blue-800', icon: PlayCircle };
    }
    
    if (candidate.interview_scheduled && !candidate.interview_started_at) {
      return { text: 'Scheduled', color: 'bg-yellow-100 text-yellow-800', icon: Clock };
    }
    
    return { text: 'Unknown', color: 'bg-gray-100 text-gray-800', icon: AlertCircle };
  }, [processingCandidates]);

  // Format duration
  const formatDuration = useCallback((seconds) => {
    const safeSeconds = parseInt(seconds) || 0;
    const hours = Math.floor(safeSeconds / 3600);
    const mins = Math.floor((safeSeconds % 3600) / 60);
    const secs = safeSeconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${mins}m ${secs}s`;
    } else if (mins > 0) {
      return `${mins}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  }, []);

  // Analysis Status Indicator Component
  const AnalysisStatusIndicator = ({ status }) => {
    if (status === 'processing') {
      return (
        <div className="flex items-center">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-600 mr-2"></div>
          <span className="text-purple-600 text-sm">Analyzing...</span>
        </div>
      );
    }
    return null;
  };

  // Candidate Details Modal
  const CandidateDetailsModal = ({ details, onClose }) => {
    if (!details || !details.candidate) return null;
    
    const candidate = details.candidate;
    const analysis = details.analysis || {};
    const qaData = details.qa_data || {};
    const progress = details.progress || {};
    const status = getInterviewStatus(candidate);
    
    // Progress chart data
    const progressData = [
      {
        name: 'Progress',
        value: candidate.interview_progress || 0,
        fill: '#3B82F6'
      }
    ];
    
    // Skills radar data
    const skillsData = [
      { skill: 'Technical', score: candidate.interview_ai_technical_score || 0 },
      { skill: 'Communication', score: candidate.interview_ai_communication_score || 0 },
      { skill: 'Problem Solving', score: candidate.interview_ai_problem_solving_score || 0 },
      { skill: 'Cultural Fit', score: candidate.interview_ai_cultural_fit_score || 0 }
    ];
    
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg w-full max-w-7xl max-h-[95vh] overflow-hidden">
          {/* Modal Header */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6">
            <div className="flex justify-between items-start">
              <div>
                <h2 className="text-2xl font-bold mb-2">{candidate.name}</h2>
                <div className="flex items-center space-x-4 text-blue-100">
                  <span className="flex items-center">
                    <Mail className="w-4 h-4 mr-1" />
                    {candidate.email}
                  </span>
                  {candidate.phone && (
                    <span className="flex items-center">
                      <Phone className="w-4 h-4 mr-1" />
                      {candidate.phone}
                    </span>
                  )}
                  {candidate.location && (
                    <span className="flex items-center">
                      <MapPin className="w-4 h-4 mr-1" />
                      {candidate.location}
                    </span>
                  )}
                </div>
                <div className="mt-2">
                  <span className="bg-white/20 px-3 py-1 rounded-full text-sm">
                    {candidate.job_title}
                  </span>
                </div>
              </div>
              <button
                onClick={onClose}
                className="text-white/80 hover:text-white transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>
          
          {/* Tabs */}
          <div className="border-b border-gray-200 bg-gray-50">
            <div className="flex space-x-1 p-1">
              {['overview', 'analysis', 'qa', 'progress'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`flex-1 py-2 px-4 rounded-lg font-medium text-sm transition-colors ${
                    activeTab === tab
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>
          </div>
          
          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(95vh-280px)]">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Status and Scores */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-white p-4 rounded-lg border">
                    <p className="text-sm text-gray-600 mb-1">Interview Status</p>
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${status.color}`}>
                      {typeof status.icon === 'function' ? <status.icon /> : <status.icon className="w-4 h-4 mr-1" />}
                      {status.text}
                    </span>
                  </div>
                  <div className="bg-white p-4 rounded-lg border">
                    <p className="text-sm text-gray-600 mb-1">Overall Score</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {candidate.interview_ai_score !== null ? `${Math.round(candidate.interview_ai_score)}%` : '—'}
                    </p>
                  </div>
                  <div className="bg-white p-4 rounded-lg border">
                    <p className="text-sm text-gray-600 mb-1">Questions Answered</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {candidate.interview_questions_answered}/{candidate.interview_total_questions || '—'}
                    </p>
                  </div>
                  <div className="bg-white p-4 rounded-lg border">
                    <p className="text-sm text-gray-600 mb-1">Duration</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatDuration(candidate.interview_duration)}
                    </p>
                  </div>
                </div>
                
                {/* Skills Chart */}
                {candidate.interview_ai_score !== null && (
                  <div className="bg-white p-6 rounded-lg border">
                    <h3 className="text-lg font-semibold mb-4">Skills Assessment</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <RechartsBarChart data={skillsData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="skill" />
                        <YAxis domain={[0, 100]} />
                        <Tooltip />
                        <Bar dataKey="score" fill="#3B82F6" />
                      </RechartsBarChart>
                    </ResponsiveContainer>
                  </div>
                )}
                
                {/* Strengths and Weaknesses */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {candidate.strengths && candidate.strengths.length > 0 && (
                    <div className="bg-green-50 p-6 rounded-lg border border-green-200">
                      <h3 className="text-lg font-semibold text-green-800 mb-3">Strengths</h3>
                      <ul className="space-y-2">
                        {candidate.strengths.map((strength, index) => (
                          <li key={index} className="flex items-start">
                            <CheckCircle className="w-5 h-5 text-green-600 mr-2 mt-0.5" />
                            <span className="text-gray-700">{strength}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {candidate.weaknesses && candidate.weaknesses.length > 0 && (
                    <div className="bg-red-50 p-6 rounded-lg border border-red-200">
                      <h3 className="text-lg font-semibold text-red-800 mb-3">Areas for Improvement</h3>
                      <ul className="space-y-2">
                        {candidate.weaknesses.map((weakness, index) => (
                          <li key={index} className="flex items-start">
                            <AlertCircle className="w-5 h-5 text-red-600 mr-2 mt-0.5" />
                            <span className="text-gray-700">{weakness}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
            
            {/* Analysis Tab */}
            {activeTab === 'analysis' && (
              <div className="space-y-6">
                {candidate.interview_ai_overall_feedback || analysis.overall_feedback ? (
                  <>
                    <div className="bg-blue-50 p-6 rounded-lg border border-blue-200">
                      <h3 className="text-lg font-semibold text-blue-800 mb-3">AI Analysis</h3>
                      <p className="text-gray-700 whitespace-pre-line">
                        {candidate.interview_ai_overall_feedback || analysis.overall_feedback}
                      </p>
                    </div>
                    
                    {(candidate.recommendations?.length > 0 || analysis.recommendations?.length > 0) && (
                      <div className="bg-yellow-50 p-6 rounded-lg border border-yellow-200">
                        <h3 className="text-lg font-semibold text-yellow-800 mb-3">Recommendations</h3>
                        <ul className="space-y-2">
                          {(candidate.recommendations || analysis.recommendations || []).map((rec, index) => (
                            <li key={index} className="flex items-start">
                              <ChevronRight className="w-5 h-5 text-yellow-600 mr-2 mt-0.5" />
                              <span className="text-gray-700">{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    <div className={`p-4 rounded-lg ${
                      candidate.interview_final_status === 'Passed' || 
                      candidate.interview_final_status === 'Recommended' ||
                      (candidate.interview_ai_score >= 70)
                        ? 'bg-green-50 border border-green-200' 
                        : 'bg-red-50 border border-red-200'
                    }`}>
                      <p className="font-semibold text-lg">
                        Final Decision: {
                          candidate.interview_final_status || 
                          analysis.final_status ||
                          (candidate.interview_ai_score >= 70 ? 'Recommended' : 'Not Recommended') ||
                          'Pending'
                        }
                      </p>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    <BarChart className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p>No analysis available yet</p>
                  </div>
                )}
              </div>
            )}
            
            {/* Q&A Tab */}
            {activeTab === 'qa' && (
              <div className="space-y-4">
                {qaData.qa_pairs && qaData.qa_pairs.length > 0 ? (
                  qaData.qa_pairs.map((qa, index) => (
                    <div key={index} className="bg-white border rounded-lg p-4">
                      <div className="mb-3">
                        <p className="font-semibold text-blue-700 mb-2">Question {index + 1}:</p>
                        <p className="text-gray-800">{qa.question}</p>
                      </div>
                      <div>
                        <p className="font-semibold text-green-700 mb-2">Answer:</p>
                        <p className="text-gray-800">
                          {qa.answer || <span className="text-red-500 italic">No answer provided</span>}
                        </p>
                      </div>
                      {qa.score && (
                        <div className="mt-3 flex items-center">
                          <span className="text-sm text-gray-600">Score:</span>
                          <span className={`ml-2 font-medium ${
                            qa.score >= 7 ? 'text-green-600' : 
                            qa.score >= 5 ? 'text-yellow-600' : 'text-red-600'
                          }`}>
                            {qa.score}/10
                          </span>
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    <MessageSquare className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p>No Q&A data available</p>
                  </div>
                )}
              </div>
            )}
            
            {/* Progress Tab */}
            {activeTab === 'progress' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Progress Chart */}
                  <div className="bg-white p-6 rounded-lg border">
                    <h3 className="text-lg font-semibold mb-4">Interview Progress</h3>
                    <ResponsiveContainer width="100%" height={200}>
                      <RadialBarChart cx="50%" cy="50%" innerRadius="60%" outerRadius="90%" data={progressData}>
                        <RadialBar dataKey="value" cornerRadius={10} fill="#3B82F6" />
                        <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" className="text-2xl font-bold">
                          {Math.round(candidate.interview_progress || 0)}%
                        </text>
                      </RadialBarChart>
                    </ResponsiveContainer>
                  </div>
                  
                  {/* Timeline */}
                  <div className="bg-white p-6 rounded-lg border">
                    <h3 className="text-lg font-semibold mb-4">Interview Timeline</h3>
                    <div className="space-y-3">
                      {candidate.interview_scheduled && (
                        <div className="flex items-center">
                          <CheckCircle className="w-5 h-5 text-green-600 mr-3" />
                          <div>
                            <p className="font-medium">Scheduled</p>
                            <p className="text-sm text-gray-500">
                              {new Date(candidate.interview_date).toLocaleString()}
                            </p>
                          </div>
                        </div>
                      )}
                      {candidate.interview_started_at && (
                        <div className="flex items-center">
                          <PlayCircle className="w-5 h-5 text-blue-600 mr-3" />
                          <div>
                            <p className="font-medium">Started</p>
                            <p className="text-sm text-gray-500">
                              {new Date(candidate.interview_started_at).toLocaleString()}
                            </p>
                          </div>
                        </div>
                      )}
                      {candidate.interview_completed_at && (
                        <div className="flex items-center">
                          <CheckCircle className="w-5 h-5 text-green-600 mr-3" />
                          <div>
                            <p className="font-medium">Completed</p>
                            <p className="text-sm text-gray-500">
                              {new Date(candidate.interview_completed_at).toLocaleString()}
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                
                {/* Live Status if in progress */}
                {liveStatuses[candidate.id] && (
                  <div className="bg-blue-50 p-6 rounded-lg border border-blue-200">
                    <h3 className="text-lg font-semibold text-blue-800 mb-4">Live Status</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <p className="text-sm text-gray-600">Connection</p>
                        <p className="font-medium">
                          {liveStatuses[candidate.id].connection_quality === 'good' ? 
                            <span className="text-green-600">Good</span> : 
                            <span className="text-red-600">Poor</span>
                          }
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Current Question</p>
                        <p className="font-medium">{liveStatuses[candidate.id].current_question || '—'}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Questions Answered</p>
                        <p className="font-medium">
                          {liveStatuses[candidate.id].answered_questions}/{liveStatuses[candidate.id].total_questions}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Duration</p>
                        <p className="font-medium">{formatDuration(liveStatuses[candidate.id].duration)}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
          
          {/* Modal Footer */}
          <div className="p-6 border-t bg-gray-50">
            <div className="flex justify-between items-center">
              <div className="flex space-x-3">
                {candidate.interview_recording_url && (
                  <a                  
                    href={candidate.interview_recording_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    <Video className="w-4 h-4 mr-2" />
                    View Recording
                  </a>
                )}
                {candidate.resume_url && (
                  <a
                    href={candidate.resume_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <FileText className="w-4 h-4 mr-2" />
                    View Resume
                  </a>
                )}
              </div>
              <button
                onClick={onClose}
                className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Effects
  useEffect(() => {
    fetchInterviewResults();
  }, []);

  // Real-time update polling effect
  useEffect(() => {
    if (!isPollingActive) return;
    
    // Calculate actual interval with exponential backoff
    const actualInterval = REALTIME_UPDATE_INTERVAL * Math.pow(2, Math.min(retryCountRef.current, 3));
    
    // Start polling
    realtimePollingRef.current = setInterval(pollForRealtimeUpdates, actualInterval);
    
    return () => {
      if (realtimePollingRef.current) {
        clearInterval(realtimePollingRef.current);
      }
    };
  }, [isPollingActive, pollForRealtimeUpdates]);

  useEffect(() => {
    if (autoRefreshIntervalRef.current) {
      clearInterval(autoRefreshIntervalRef.current);
    }
    
    if (autoRefresh) {
      autoRefreshIntervalRef.current = setInterval(() => {
        fetchInterviewResults(true);
      }, AUTO_REFRESH_INTERVAL);
    }
    
    return () => {
      if (autoRefreshIntervalRef.current) {
        clearInterval(autoRefreshIntervalRef.current);
      }
    };
  }, [autoRefresh, fetchInterviewResults]);

  useEffect(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    
    const hasActiveInterviews = candidates.some(c => 
      c && c.interview_started_at && !c.interview_completed_at
    );
    
    if (hasActiveInterviews) {
      pollLiveUpdates();
      pollingIntervalRef.current = setInterval(pollLiveUpdates, POLLING_INTERVAL);
    }
    
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [candidates, pollLiveUpdates]);

  // Filter candidates
  const filteredCandidates = candidates.filter(c => {
    if (!c) return false;
    if (!searchTerm) return true;
    
    const search = searchTerm.toLowerCase();
    return (
      (c.name && c.name.toLowerCase().includes(search)) ||
      (c.email && c.email.toLowerCase().includes(search)) ||
      (c.job_title && c.job_title.toLowerCase().includes(search))
    );
  });

  // Calculate stats
  const stats = {
    totalInterviews: filteredCandidates.length,
    completedInterviews: filteredCandidates.filter(c => c.interview_completed_at).length,
    inProgress: filteredCandidates.filter(c => c.interview_started_at && !c.interview_completed_at).length,
    averageScore: filteredCandidates.filter(c => c.interview_ai_score !== null).reduce((sum, c) => sum + c.interview_ai_score, 0) / 
                  (filteredCandidates.filter(c => c.interview_ai_score !== null).length || 1),
    passRate: (filteredCandidates.filter(c => c.interview_ai_score >= 70).length / 
              (filteredCandidates.filter(c => c.interview_ai_score !== null).length || 1)) * 100,
    pendingAnalysis: filteredCandidates.filter(c => c.interview_completed_at && c.interview_ai_score === null).length
  };

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Navigation />
      
      <main className="flex-grow p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Interview Results</h1>
            <p className="text-gray-600 mt-1">Click on any candidate name to view detailed results</p>
          </div>
          <div className="flex items-center space-x-3">
            {processingCandidates.size > 0 && (
              <div className="flex items-center text-sm text-purple-600">
                <Loader className="w-4 h-4 animate-spin mr-1" />
                {processingCandidates.size} analyzing...
              </div>
            )}
            <div className="flex items-center text-sm text-gray-500">
              <Clock className="w-4 h-4 mr-1" />
              Last updated: {lastRefresh.toLocaleTimeString()}
            </div>
            <button
              onClick={() => fetchInterviewResults()}
              className="flex items-center px-3 py-1.5 text-sm bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100"
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm text-gray-600">Auto-refresh</span>
            </label>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
            <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-6 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total</p>
                <p className="text-2xl font-bold">{stats.totalInterviews}</p>
              </div>
              <Users className="w-8 h-8 text-blue-600" />
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">In Progress</p>
                <p className="text-2xl font-bold">{stats.inProgress}</p>
              </div>
              <PlayCircle className="w-8 h-8 text-blue-600" />
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Completed</p>
                <p className="text-2xl font-bold">{stats.completedInterviews}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Score</p>
                <p className="text-2xl font-bold">{stats.averageScore.toFixed(1)}%</p>
              </div>
              <Target className="w-8 h-8 text-purple-600" />
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Pass Rate</p>
                <p className="text-2xl font-bold">{stats.passRate.toFixed(1)}%</p>
              </div>
              <Award className="w-8 h-8 text-yellow-600" />
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Pending</p>
                <p className="text-2xl font-bold">{stats.pendingAnalysis}</p>
              </div>
              <Clock className="w-8 h-8 text-orange-600" />
            </div>
          </div>
        </div>

        {/* Live Sessions */}
        {Object.keys(liveStatuses).length > 0 && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center">
              <Activity className="w-5 h-5 mr-2 text-blue-600" />
              Live Interview Sessions
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {candidates
                .filter(c => c && liveStatuses[c.id])
                .map(candidate => (
                  <div key={candidate.id} className="bg-white rounded-lg shadow-sm border p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h4 className="font-semibold text-gray-900 cursor-pointer hover:text-blue-600"
                            onClick={() => fetchCandidateDetails(candidate.id)}>
                          {candidate.name}
                        </h4>
                        <p className="text-sm text-gray-600">{candidate.job_title}</p>
                      </div>
                      <div className="flex items-center">
                        {liveStatuses[candidate.id].is_active ? (
                          <CircleDot className="w-4 h-4 animate-pulse text-green-600" />
                        ) : (
                          <CircleDot className="w-4 h-4 text-gray-400" />
                        )}
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Progress:</span>
                        <span className="font-medium">{liveStatuses[candidate.id].progress.toFixed(0)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${liveStatuses[candidate.id].progress}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Main Table */}
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-4 border-b">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">All Candidates</h3>
              <div className="flex items-center space-x-2">
                <Search className="w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search candidates..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="px-3 py-1 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Candidate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Position
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Progress
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading && candidates.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center">
                      <Loader className="animate-spin h-8 w-8 text-blue-600 mx-auto" />
                      <p className="mt-2 text-gray-500">Loading...</p>
                    </td>
                  </tr>
                ) : filteredCandidates.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                      <Video className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                      <p>No interview results found</p>
                    </td>
                  </tr>
                ) : (
                  filteredCandidates.map((candidate) => {
                    const status = getInterviewStatus(candidate);
                    const StatusIcon = status.icon;
                    const isUpdated = candidate._updated && (Date.now() - candidate._updateTime < 3000);
                    
                    return (
                      <tr 
                        key={candidate.id} 
                        className={`hover:bg-gray-50 transition-all duration-500 ${
                          isUpdated ? 'bg-green-50' : ''
                        }`}
                      >
                        <td className="px-6 py-4 whitespace-nowrap">
                          <button
                            onClick={() => fetchCandidateDetails(candidate.id)}
                            className="text-left hover:text-blue-600 transition-colors"
                          >
                            <div className="text-sm font-medium text-gray-900">{candidate.name}</div>
                            <div className="text-sm text-gray-500">{candidate.email}</div>
                          </button>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {candidate.job_title}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${status.color}`}>
                            {typeof StatusIcon === 'function' ? <StatusIcon /> : <StatusIcon className="w-3 h-3 mr-1" />}
                            {status.text}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="w-24 bg-gray-200 rounded-full h-2 mr-2">
                              <div
                                className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                                style={{ width: `${candidate.interview_progress || 0}%` }}
                              />
                            </div>
                            <span className="text-sm text-gray-600">
                              {candidate.interview_progress || 0}%
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {candidate.interview_ai_score !== null ? (
                            <div className="flex items-center">
                              <span className={`text-sm font-medium ${
                                candidate.interview_ai_score >= 70 ? 'text-green-600' : 'text-red-600'
                              } ${isUpdated ? 'animate-pulse' : ''}`}>
                                {Math.round(candidate.interview_ai_score)}%
                              </span>
                            </div>
                          ) : candidate.interview_ai_analysis_status === 'processing' ? (
                            <AnalysisStatusIndicator status="processing" />
                          ) : (
                            <span className="text-sm text-gray-500">—</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <button
                            onClick={() => fetchCandidateDetails(candidate.id)}
                            className="text-blue-600 hover:text-blue-900 transition-colors"
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Candidate Details Modal */}
        {showCandidateModal && selectedCandidateDetails && (
          <CandidateDetailsModal
            details={selectedCandidateDetails}
            onClose={() => {
              setShowCandidateModal(false);
              setSelectedCandidateDetails(null);
            }}
          />
        )}
      </main>
    </div>
  );
};

export default InterviewResults;