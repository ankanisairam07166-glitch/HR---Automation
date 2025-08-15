import React, { useState, useEffect } from 'react';
import { 
  Video, Calendar, Clock, Award, BarChart, Download, 
  Eye, TrendingUp, AlertCircle, CheckCircle, XCircle,
  Mic, FileText, Target, Users, Search, Filter,
  MessageSquare, X, ChevronRight, PlayCircle, RefreshCw
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Navigation from './Navigation';
import { BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Legend } from 'recharts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:5000";

const InterviewResults = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [candidates, setCandidates] = useState([]);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [showQADetails, setShowQADetails] = useState(false);
  const [selectedQAData, setSelectedQAData] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [filters, setFilters] = useState({
    status: 'all',
    position: 'all',
    dateRange: 'all'
  });
  const [stats, setStats] = useState({
    totalInterviews: 0,
    completedInterviews: 0,
    averageScore: 0,
    passRate: 0,
    pendingAnalysis: 0,
    inProgress: 0
  });

  useEffect(() => {
    fetchInterviewResults();
    
    // Poll for updates every 30 seconds if auto-refresh is enabled
    let interval;
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchInterviewResults(true);
      }, 30000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [filters, autoRefresh]);

  const fetchInterviewResults = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/candidates`);
      const data = await response.json();
      
      // Filter candidates who have interview data
      const interviewedCandidates = data.filter(c => 
        c.interview_scheduled || 
        c.interview_started_at || 
        c.interview_completed_at || 
        c.interview_ai_score ||
        c.interview_token
      );
      
      setCandidates(interviewedCandidates);
      calculateStats(interviewedCandidates);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Error fetching interview results:', error);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  const calculateStats = (candidates) => {
    const total = candidates.length;
    const completed = candidates.filter(c => c.interview_completed_at).length;
    const inProgress = candidates.filter(c => c.interview_started_at && !c.interview_completed_at).length;
    const withScores = candidates.filter(c => c.interview_ai_score).length;
    const passed = candidates.filter(c => c.interview_ai_score >= 70).length;
    const avgScore = withScores > 0 
      ? candidates.reduce((sum, c) => sum + (c.interview_ai_score || 0), 0) / withScores 
      : 0;
    const pending = candidates.filter(c => 
      c.interview_completed_at && (!c.interview_ai_score || c.interview_ai_analysis_status === 'pending')
    ).length;

    setStats({
      totalInterviews: total,
      completedInterviews: completed,
      inProgress: inProgress,
      averageScore: avgScore.toFixed(1),
      passRate: withScores > 0 ? ((passed / withScores) * 100).toFixed(1) : 0,
      pendingAnalysis: pending
    });
  };

  const getInterviewStatus = (candidate) => {
    // Check if any interview data exists
    const hasInterviewData = candidate.interview_scheduled || 
                            candidate.interview_started_at || 
                            candidate.interview_completed_at ||
                            candidate.interview_ai_score ||
                            candidate.interview_token;
    
    if (!hasInterviewData) {
      return { text: 'Not Scheduled', color: 'bg-gray-100 text-gray-800', icon: XCircle };
    }
    
    // Check completion and analysis status
    if (candidate.interview_completed_at) {
      if (candidate.interview_ai_analysis_status === 'processing') {
        return { text: 'Analyzing', color: 'bg-purple-100 text-purple-800', icon: BarChart };
      }
      if (candidate.interview_ai_score) {
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
  };

  const getScoreBreakdown = () => {
    const scoreRanges = [
      { name: '90-100', count: 0, color: '#10B981' },
      { name: '80-89', count: 0, color: '#3B82F6' },
      { name: '70-79', count: 0, color: '#F59E0B' },
      { name: '60-69', count: 0, color: '#EF4444' },
      { name: 'Below 60', count: 0, color: '#6B7280' }
    ];

    candidates.forEach(c => {
      if (c.interview_ai_score >= 90) scoreRanges[0].count++;
      else if (c.interview_ai_score >= 80) scoreRanges[1].count++;
      else if (c.interview_ai_score >= 70) scoreRanges[2].count++;
      else if (c.interview_ai_score >= 60) scoreRanges[3].count++;
      else if (c.interview_ai_score > 0) scoreRanges[4].count++;
    });

    return scoreRanges;
  };

  const getSkillsAnalysis = () => {
    const skills = [
      { skill: 'Technical', average: 0, count: 0 },
      { skill: 'Communication', average: 0, count: 0 },
      { skill: 'Problem Solving', average: 0, count: 0 },
      { skill: 'Cultural Fit', average: 0, count: 0 }
    ];

    candidates.forEach(c => {
      if (c.interview_ai_technical_score) {
        skills[0].average += c.interview_ai_technical_score;
        skills[0].count++;
      }
      if (c.interview_ai_communication_score) {
        skills[1].average += c.interview_ai_communication_score;
        skills[1].count++;
      }
      if (c.interview_ai_problem_solving_score) {
        skills[2].average += c.interview_ai_problem_solving_score;
        skills[2].count++;
      }
      if (c.interview_ai_cultural_fit_score) {
        skills[3].average += c.interview_ai_cultural_fit_score;
        skills[3].count++;
      }
    });

    return skills.map(s => ({
      skill: s.skill,
      average: s.count > 0 ? (s.average / s.count).toFixed(1) : 0
    }));
  };

  const viewCandidateDetails = async (candidateId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/interview/analysis/${candidateId}`);
      const data = await response.json();
      if (data.success) {
        setSelectedCandidate({ ...candidates.find(c => c.id === candidateId), analysis: data.analysis });
      }
    } catch (error) {
      console.error('Error fetching candidate analysis:', error);
    }
  };

  const triggerAnalysis = async (candidateId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/interview/trigger-analysis/${candidateId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        alert('AI analysis started. Results will appear in 10-30 seconds.');
        // Refresh after a short delay
        setTimeout(() => fetchInterviewResults(), 3000);
        // And again after a longer delay to catch completed analysis
        setTimeout(() => fetchInterviewResults(true), 15000);
      } else {
        const error = await response.json();
        alert(`Failed to trigger analysis: ${error.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error triggering analysis:', error);
      alert('Failed to trigger analysis. Please try again.');
    }
  };

  const viewDetailedQA = async (candidateId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/interview/qa/get/${candidateId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (data.success || data.qa_data) {
        setSelectedQAData(data);
        setShowQADetails(true);
      } else {
        alert('No Q&A data available for this candidate.');
      }
    } catch (error) {
      console.error('Error fetching Q&A details:', error);
      alert('Failed to load Q&A details. Please try again.');
    }
  };

  const QADetailsModal = ({ data, onClose }) => {
    if (!data) return null;
    
    const candidate = data.candidate || {};
    const qaData = data.qa_data || {};
    const analysis = data.analysis || {};
    const qaPairs = qaData.qa_pairs || [];
    
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden">
          <div className="p-6 border-b sticky top-0 bg-white z-10">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">
                Interview Q&A Analysis - {candidate.name || 'Unknown'}
              </h2>
              <button 
                onClick={onClose} 
                className="text-gray-500 hover:text-gray-700 transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>
          
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
            {/* Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-sm text-blue-600">Questions Asked</p>
                <p className="text-2xl font-bold">{qaData.total_questions || 0}</p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <p className="text-sm text-green-600">Questions Answered</p>
                <p className="text-2xl font-bold">{qaData.total_answers || 0}</p>
              </div>
              <div className="bg-yellow-50 p-4 rounded-lg">
                <p className="text-sm text-yellow-600">Completion Rate</p>
                <p className="text-2xl font-bold">{qaData.completion_rate || '0%'}</p>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <p className="text-sm text-purple-600">Overall Score</p>
                <p className="text-2xl font-bold">{analysis.overall_score || '—'}%</p>
              </div>
            </div>
            
            {/* Q&A Pairs */}
            {qaPairs.length > 0 ? (
              <>
                <h3 className="text-lg font-semibold mb-4">Interview Questions & Answers</h3>
                <div className="space-y-4">
                  {qaPairs.map((qa, index) => (
                    <div key={index} className="border rounded-lg p-4 bg-gray-50">
                      <div className="mb-3">
                        <div className="flex items-center justify-between mb-1">
                          <p className="font-semibold text-blue-700">Question {index + 1}:</p>
                          <span className="text-xs text-gray-500">
                            {qa.question_timestamp ? new Date(qa.question_timestamp).toLocaleTimeString() : ''}
                          </span>
                        </div>
                        <p className="text-gray-800">{qa.question || 'No question text'}</p>
                      </div>
                      
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <p className="font-semibold text-green-700">Answer:</p>
                          <span className="text-xs text-gray-500">
                            {qa.answer_timestamp ? new Date(qa.answer_timestamp).toLocaleTimeString() : ''}
                          </span>
                        </div>
                        <p className="text-gray-800">
                          {qa.answer || <span className="text-red-500 italic">No answer provided</span>}
                        </p>
                      </div>
                      
                      {/* Time to answer */}
                      {qa.question_timestamp && qa.answer_timestamp && (
                        <div className="mt-2 text-xs text-gray-600">
                          Response time: {
                            Math.round((new Date(qa.answer_timestamp) - new Date(qa.question_timestamp)) / 1000)
                          } seconds
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <MessageSquare className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p>No Q&A data available</p>
              </div>
            )}
            
            {/* AI Analysis Section */}
            {analysis.overall_feedback && (
              <div className="mt-6">
                <h3 className="text-lg font-semibold mb-4">AI Analysis</h3>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-gray-800 whitespace-pre-line">
                    {analysis.overall_feedback}
                  </p>
                </div>
              </div>
            )}
            
            {/* Full Transcript */}
            {data.transcript && (
              <div className="mt-6">
                <h3 className="text-lg font-semibold mb-4">Full Interview Transcript</h3>
                <div className="bg-gray-100 p-4 rounded-lg max-h-96 overflow-y-auto">
                  <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                    {data.transcript}
                  </pre>
                </div>
              </div>
            )}
          </div>
          
          <div className="p-6 border-t bg-gray-50 sticky bottom-0">
            <div className="flex justify-between items-center">
              <div className="text-sm text-gray-600">
                Interview Status: <span className="font-semibold">
                  {analysis.recommendation || analysis.final_status || 'Pending'}
                </span>
              </div>
              <button
                onClick={onClose}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const downloadReport = () => {
    const data = candidates.map(c => ({
      Name: c.name,
      Email: c.email,
      Position: c.job_title,
      'Interview Date': c.interview_date ? new Date(c.interview_date).toLocaleDateString() : 'N/A',
      'Status': getInterviewStatus(c).text,
      'Started': c.interview_started_at ? 'Yes' : 'No',
      'Completed': c.interview_completed_at ? 'Yes' : 'No',
      'Analysis Status': c.interview_ai_analysis_status || 'N/A',
      'Overall Score': c.interview_ai_score || 'N/A',
      'Technical Score': c.interview_ai_technical_score || 'N/A',
      'Communication Score': c.interview_ai_communication_score || 'N/A',
      'Problem Solving': c.interview_ai_problem_solving_score || 'N/A',
      'Cultural Fit': c.interview_ai_cultural_fit_score || 'N/A',
      'Final Status': c.interview_final_status || 'Pending',
      'Recommendation': c.interview_ai_score >= 70 ? 'Recommended' : (c.interview_ai_score ? 'Not Recommended' : 'Pending')
    }));

    const csv = [
      Object.keys(data[0] || {}).join(','),
      ...data.map(row => Object.values(row).map(v => `"${v}"`).join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `interview_results_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  const handleManualRefresh = () => {
    fetchInterviewResults();
  };

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Navigation />
      
      <main className="flex-grow p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Interview Results</h1>
            <p className="text-gray-600 mt-1">AI-powered interview analysis and insights</p>
          </div>
          <div className="flex items-center space-x-3">
            <div className="flex items-center text-sm text-gray-500">
              <Clock className="w-4 h-4 mr-1" />
              Last updated: {lastRefresh.toLocaleTimeString()}
            </div>
            <button
              onClick={handleManualRefresh}
              className="flex items-center px-3 py-1.5 text-sm bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors"
              title="Refresh data"
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
            <button
              onClick={downloadReport}
              className="flex items-center px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Download className="w-4 h-4 mr-2" />
              Export Report
            </button>
          </div>
        </div>

        {/* Enhanced Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-6 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Interviews</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalInterviews}</p>
              </div>
              <Users className="w-8 h-8 text-blue-600" />
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">In Progress</p>
                <p className="text-2xl font-bold text-gray-900">{stats.inProgress}</p>
              </div>
              <PlayCircle className="w-8 h-8 text-blue-600" />
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Completed</p>
                <p className="text-2xl font-bold text-gray-900">{stats.completedInterviews}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Average Score</p>
                <p className="text-2xl font-bold text-gray-900">{stats.averageScore}%</p>
              </div>
              <Target className="w-8 h-8 text-purple-600" />
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Pass Rate</p>
                <p className="text-2xl font-bold text-gray-900">{stats.passRate}%</p>
              </div>
              <Award className="w-8 h-8 text-yellow-600" />
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Pending Analysis</p>
                <p className="text-2xl font-bold text-gray-900">{stats.pendingAnalysis}</p>
              </div>
              <Clock className="w-8 h-8 text-orange-600" />
            </div>
          </div>
        </div>

        {/* Analytics Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Score Distribution */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold mb-4">Score Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <RechartsBarChart data={getScoreBreakdown()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3B82F6">
                  {getScoreBreakdown().map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </RechartsBarChart>
            </ResponsiveContainer>
          </div>

          {/* Skills Analysis */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold mb-4">Average Skills Assessment</h3>
            <ResponsiveContainer width="100%" height={300}>
              <RechartsBarChart data={getSkillsAnalysis()} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="skill" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Bar dataKey="average" fill="#10B981" />
              </RechartsBarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Results Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Interview Results</h3>
              <div className="flex items-center space-x-2">
                <Search className="w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search candidates..."
                  className="px-3 py-1 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Candidate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Position
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Interview Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Overall Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Skills Breakdown
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-8 text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                      <p className="mt-2 text-gray-500">Loading interview results...</p>
                    </td>
                  </tr>
                ) : candidates.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                      <Video className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                      <p className="text-lg font-medium">No interview results found</p>
                      <p className="mt-1">Interview results will appear here once candidates complete their interviews</p>
                    </td>
                  </tr>
                ) : (
                  candidates.map((candidate) => {
                    const status = getInterviewStatus(candidate);
                    const StatusIcon = status.icon;
                    
                    return (
                      <tr key={candidate.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{candidate.name}</div>
                            <div className="text-sm text-gray-500">{candidate.email}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {candidate.job_title}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {candidate.interview_date 
                            ? new Date(candidate.interview_date).toLocaleDateString()
                            : '—'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${status.color}`}>
                            <StatusIcon className="w-3 h-3 mr-1" />
                            {status.text}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {candidate.interview_ai_score ? (
                            <div className="flex items-center">
                              <span className={`text-sm font-medium ${
                                candidate.interview_ai_score >= 70 ? 'text-green-600' : 'text-red-600'
                              }`}>
                                {candidate.interview_ai_score.toFixed(0)}%
                              </span>
                              <div className="ml-2 w-16 bg-gray-200 rounded-full h-2">
                                <div
                                  className={`h-2 rounded-full ${
                                    candidate.interview_ai_score >= 70 ? 'bg-green-600' : 'bg-red-600'
                                  }`}
                                  style={{ width: `${candidate.interview_ai_score}%` }}
                                ></div>
                              </div>
                            </div>
                          ) : (
                            <span className="text-sm text-gray-500">—</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {candidate.interview_ai_score ? (
                            <div className="flex space-x-1">
                              <div className="text-xs">
                                <span className="text-gray-500">T:</span>
                                <span className="font-medium">{candidate.interview_ai_technical_score?.toFixed(0) || '—'}</span>
                              </div>
                              <div className="text-xs">
                                <span className="text-gray-500">C:</span>
                                <span className="font-medium">{candidate.interview_ai_communication_score?.toFixed(0) || '—'}</span>
                              </div>
                              <div className="text-xs">
                                <span className="text-gray-500">P:</span>
                                <span className="font-medium">{candidate.interview_ai_problem_solving_score?.toFixed(0) || '—'}</span>
                              </div>
                              <div className="text-xs">
                                <span className="text-gray-500">F:</span>
                                <span className="font-medium">{candidate.interview_ai_cultural_fit_score?.toFixed(0) || '—'}</span>
                              </div>
                            </div>
                          ) : (
                            <span className="text-sm text-gray-500">—</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <div className="flex items-center space-x-2">
                            {/* View Analysis button - always visible if there's any data */}
                            {(candidate.interview_ai_score || candidate.interview_completed_at) && (
                              <button
                                onClick={() => viewCandidateDetails(candidate.id)}
                                className="text-blue-600 hover:text-blue-900 transition-colors"
                                title="View Analysis"
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                            )}
                            
                            {/* Q&A button - show if interview completed */}
                            {candidate.interview_completed_at && (
                              <button
                                onClick={() => viewDetailedQA(candidate.id)}
                                className="text-purple-600 hover:text-purple-900 transition-colors"
                                title="View Q&A Details"
                              >
                                <MessageSquare className="w-4 h-4" />
                              </button>
                            )}
                            
                            {/* Trigger Analysis button - show if completed but no score */}
                            {candidate.interview_completed_at && !candidate.interview_ai_score && (
                              <button
                                onClick={() => triggerAnalysis(candidate.id)}
                                className="text-orange-600 hover:text-orange-900 transition-colors animate-pulse"
                                title="Trigger AI Analysis"
                              >
                                <BarChart className="w-4 h-4" />
                              </button>
                            )}
                            
                            {/* Recording button */}
                            {candidate.interview_recording_url && (
                              <a
                                href={candidate.interview_recording_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-green-600 hover:text-green-900 transition-colors"
                                title="View Recording"
                              >
                                <Video className="w-4 h-4" />
                              </a>
                            )}
                            
                            {/* AI Feedback button */}
                            {candidate.interview_ai_overall_feedback && (
                              <button
                                onClick={() => {
                                  setSelectedCandidate({
                                    ...candidate,
                                    analysis: {
                                      overall_feedback: candidate.interview_ai_overall_feedback,
                                      overall_score: candidate.interview_ai_score,
                                      technical_score: candidate.interview_ai_technical_score,
                                      communication_score: candidate.interview_ai_communication_score,
                                      problem_solving_score: candidate.interview_ai_problem_solving_score,
                                      cultural_fit_score: candidate.interview_ai_cultural_fit_score,
                                      final_status: candidate.interview_final_status
                                    }
                                  });
                                }}
                                className="text-indigo-600 hover:text-indigo-900 transition-colors"
                                title="View AI Feedback"
                              >
                                <FileText className="w-4 h-4" />
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

        {/* Q&A Details Modal */}
        {showQADetails && (
          <QADetailsModal 
            data={selectedQAData} 
            onClose={() => {
              setShowQADetails(false);
              setSelectedQAData(null);
            }} 
          />
        )}

        {/* Candidate Detail Modal */}
        {selectedCandidate && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">Interview Analysis - {selectedCandidate.name}</h2>
                <button
                  onClick={() => setSelectedCandidate(null)}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
              
              {selectedCandidate.analysis && (
                <div className="space-y-6">
                  {/* Score Summary */}
                  <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <p className="text-sm text-blue-600">Overall Score</p>
                      <p className="text-2xl font-bold text-blue-900">
                        {selectedCandidate.analysis.overall_score?.toFixed(0) || '—'}%
                      </p>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <p className="text-sm text-green-600">Technical</p>
                      <p className="text-2xl font-bold text-green-900">
                        {selectedCandidate.analysis.technical_score?.toFixed(0) || '—'}%
                      </p>
                    </div>
                    <div className="bg-yellow-50 p-4 rounded-lg">
                      <p className="text-sm text-yellow-600">Communication</p>
                      <p className="text-2xl font-bold text-yellow-900">
                        {selectedCandidate.analysis.communication_score?.toFixed(0) || '—'}%
                      </p>
                    </div>
                    <div className="bg-purple-50 p-4 rounded-lg">
                      <p className="text-sm text-purple-600">Problem Solving</p>
                      <p className="text-2xl font-bold text-purple-900">
                        {selectedCandidate.analysis.problem_solving_score?.toFixed(0) || '—'}%
                      </p>
                    </div>
                    <div className="bg-pink-50 p-4 rounded-lg">
                      <p className="text-sm text-pink-600">Cultural Fit</p>
                      <p className="text-2xl font-bold text-pink-900">
                        {selectedCandidate.analysis.cultural_fit_score?.toFixed(0) || '—'}%
                      </p>
                    </div>
                  </div>

                  {/* AI Feedback */}
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <h3 className="text-lg font-semibold mb-3">AI Overall Feedback</h3>
                    <p className="text-gray-700 whitespace-pre-line">
                      {selectedCandidate.analysis.overall_feedback || 'No feedback available'}
                    </p>
                  </div>

                  {/* Question Analysis */}
                  {selectedCandidate.analysis.question_analysis && 
                   selectedCandidate.analysis.question_analysis.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3">Question-by-Question Analysis</h3>
                      <div className="space-y-3">
                        {selectedCandidate.analysis.question_analysis.map((qa, index) => (
                          <div key={index} className="border rounded-lg p-4">
                            <p className="font-medium text-gray-900 mb-2">
                              Q{index + 1}: {qa.question}
                            </p>
                            <p className="text-gray-700 mb-2">
                              <span className="font-medium">Answer:</span> {qa.answer}
                            </p>
                            <div className="flex items-center justify-between">
                              <p className="text-sm text-gray-600">
                                <span className="font-medium">Analysis:</span> {qa.analysis}
                              </p>
                              <span className={`text-sm font-medium ${
                                qa.score >= 7 ? 'text-green-600' : 
                                qa.score >= 5 ? 'text-yellow-600' : 'text-red-600'
                              }`}>
                                Score: {qa.score}/10
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Final Recommendation */}
                  <div className={`p-4 rounded-lg ${
                    selectedCandidate.analysis.final_status === 'Recommended' || 
                    selectedCandidate.analysis.recommendation === 'Recommended' ||
                    selectedCandidate.analysis.recommendation === 'Strongly Recommended' ||
                    (selectedCandidate.analysis.overall_score >= 70)
                      ? 'bg-green-50 border border-green-200' 
                      : 'bg-red-50 border border-red-200'
                  }`}>
                    <p className="font-semibold">
                      Final Recommendation: {
                        selectedCandidate.analysis.recommendation || 
                        selectedCandidate.analysis.final_status || 
                        (selectedCandidate.analysis.overall_score >= 70 ? 'Recommended' : 'Not Recommended') ||
                        'Pending'
                      }
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default InterviewResults;