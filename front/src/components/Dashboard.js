import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Search, Filter, Calendar, Users, Clock, Award, Bell, ChevronDown, Plus, X, TrendingUp, AlertCircle, CheckCircle, XCircle, BarChart3, Target, RefreshCw, PlayCircle, Play, FileText, Zap } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, Legend } from 'recharts';
import { useNavigate } from 'react-router-dom';
import Navigation from './Navigation';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://127.0.0.1:5000';

// PipelineRunner Component
const PipelineRunner = ({ job, onPipelineStart, onPipelineComplete, onClose }) => {
  const [showConfirmModal, setShowConfirmModal] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [status, setStatus] = useState(null);

  const runPipeline = async (createAssessment) => {
    setShowConfirmModal(false);
    setIsRunning(true);
    setStatus('Starting pipeline...');
    
    if (onPipelineStart) onPipelineStart();

    try {
      const response = await fetch(`${BACKEND_URL}/api/run_full_pipeline`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_id: job.id,
          job_title: job.title,
          job_desc: job.description || '',
          create_assessment: createAssessment
        }),
      });

      const data = await response.json();
      
      if (response.ok) {
        setStatus('Pipeline completed successfully');
        setTimeout(() => {
          if (onPipelineComplete) onPipelineComplete();
          if (onClose) onClose();
        }, 2000);
      } else {
        setStatus(`Error: ${data.message}`);
        setIsRunning(false);
      }
    } catch (error) {
      console.error('Pipeline error:', error);
      setStatus(`Error: ${error.message}`);
      setIsRunning(false);
    }
  };

  if (!showConfirmModal && status) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
          <div className="text-center">
            {isRunning ? (
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            ) : status.includes('Error') ? (
              <XCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
            ) : (
              <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-4" />
            )}
            <p className="text-gray-900">{status}</p>
            {!isRunning && (
              <button
                onClick={onClose}
                className="mt-4 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
              >
                Close
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Configure Pipeline
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="mb-6">
          <p className="text-gray-600 mb-4">
            Choose how you want to run the recruitment pipeline for:
          </p>
          <div className="bg-gray-50 p-3 rounded-lg">
            <p className="font-medium text-gray-900">{job.title}</p>
            <p className="text-sm text-gray-500">{job.location}</p>
          </div>
        </div>

        <div className="space-y-3 mb-6">
          <button
            onClick={() => runPipeline(true)}
            className="w-full p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all group"
          >
            <div className="flex items-start">
              <FileText className="w-5 h-5 text-blue-600 mt-0.5 mr-3" />
              <div className="text-left flex-1">
                <h4 className="font-medium text-gray-900 group-hover:text-blue-600">
                  Full Pipeline with Assessment
                </h4>
                <p className="text-sm text-gray-500 mt-1">
                  • Scrape resumes<br/>
                  • Create Testlify assessment<br/>
                  • AI screening & scoring
                </p>
                <p className="text-xs text-blue-600 mt-2">
                  ~5-10 minutes
                </p>
              </div>
            </div>
          </button>

          <button
            onClick={() => runPipeline(false)}
            className="w-full p-4 border-2 border-gray-200 rounded-lg hover:border-green-500 hover:bg-green-50 transition-all group"
          >
            <div className="flex items-start">
              <Zap className="w-5 h-5 text-green-600 mt-0.5 mr-3" />
              <div className="text-left flex-1">
                <h4 className="font-medium text-gray-900 group-hover:text-green-600">
                  Quick Pipeline (No Assessment)
                </h4>
                <p className="text-sm text-gray-500 mt-1">
                  • Scrape resumes<br/>
                  • AI screening & scoring only
                </p>
                <p className="text-xs text-green-600 mt-2">
                  ~3-5 minutes
                </p>
              </div>
            </div>
          </button>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <div className="flex">
            <AlertCircle className="w-5 h-5 text-yellow-600 mr-2 flex-shrink-0" />
            <div className="text-sm text-yellow-800">
              <p className="font-medium">Note:</p>
              <p>You can create assessments manually later from the Assessments page if you skip it now.</p>
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

// Main Dashboard Component
const Dashboard = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [candidates, setCandidates] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [stats, setStats] = useState({
    totalApplications: 0,
    activeInterviews: 0,
    timeToHire: 0,
    activeAssessments: 0,
    shortlistRate: 0,
    assessmentCompletionRate: 0,
    totalHires: 0,
    pendingActions: 0
  });
  const [recruitmentData, setRecruitmentData] = useState([]);
  const [selectedPipelineJob, setSelectedPipelineJob] = useState(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState('month');
  const [notifications, setNotifications] = useState([]);
  const [pipelineStatus, setPipelineStatus] = useState({});
  const [lastFetchTime, setLastFetchTime] = useState(null);

  const dataCache = useRef({});
  const abortController = useRef(null);

  const fetchDashboardData = useCallback(async (forceRefresh = false) => {
    const cacheKey = `dashboard_${selectedTimeRange}`;
    const now = Date.now();
    
    if (!forceRefresh && dataCache.current[cacheKey] && 
        (now - dataCache.current[cacheKey].timestamp) < 300000) {
      const cached = dataCache.current[cacheKey];
      setJobs(cached.jobs);
      setCandidates(cached.candidates);
      setRecruitmentData(cached.recruitmentData);
      calculateStats(cached.candidates);
      generateNotifications(cached.candidates);
      setLoading(false);
      return;
    }

    setLoading(!forceRefresh ? true : false);
    setRefreshing(forceRefresh);

    if (abortController.current) {
      abortController.current.abort();
    }
    abortController.current = new AbortController();

    try {
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Request timeout')), 15000)
      );

      const fetchPromises = [
        Promise.race([
          fetch(`${BACKEND_URL}/api/jobs`, { 
            signal: abortController.current.signal,
            headers: { 'Cache-Control': 'max-age=300' }
          }).then(res => res.ok ? res.json() : []),
          timeoutPromise
        ]).catch(() => []),
        
        Promise.race([
          fetch(`${BACKEND_URL}/api/candidates`, { 
            signal: abortController.current.signal,
            headers: { 'Cache-Control': 'max-age=300' }
          }).then(res => res.ok ? res.json() : []),
          timeoutPromise
        ]).catch(() => []),
        
        Promise.race([
          fetch(`${BACKEND_URL}/api/recruitment-stats`, { 
            signal: abortController.current.signal,
            headers: { 'Cache-Control': 'max-age=600' }
          }).then(res => res.ok ? res.json() : []),
          timeoutPromise
        ]).catch(() => [])
      ];

      const [jobsData, candidatesData, statsData] = await Promise.all(fetchPromises);

      const safeJobs = Array.isArray(jobsData) ? jobsData : [];
      const safeCandidates = Array.isArray(candidatesData) ? candidatesData : [];
      const safeStats = Array.isArray(statsData) ? statsData : [];

      dataCache.current[cacheKey] = {
        jobs: safeJobs,
        candidates: safeCandidates,
        recruitmentData: safeStats,
        timestamp: now
      };

      setJobs(safeJobs);
      setCandidates(safeCandidates);
      setRecruitmentData(safeStats);
      setLastFetchTime(new Date());

      calculateStats(safeCandidates);
      generateNotifications(safeCandidates);

    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('Error fetching dashboard data:', error);
        if (!dataCache.current[cacheKey]) {
          setJobs([]);
          setCandidates([]);
          setRecruitmentData([]);
        }
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedTimeRange]);

  useEffect(() => {
    fetchDashboardData();
    
    const interval = setInterval(() => fetchDashboardData(true), 120000);
    return () => {
      clearInterval(interval);
      if (abortController.current) {
        abortController.current.abort();
      }
    };
  }, [fetchDashboardData]);

  const handleRefresh = useCallback(() => {
    fetchDashboardData(true);
  }, [fetchDashboardData]);

  const calculateStats = (candidatesData) => {
    if (!Array.isArray(candidatesData)) {
      candidatesData = [];
    }

    const total = candidatesData.length;
    const shortlisted = candidatesData.filter(c => c && c.status === 'Shortlisted').length;
    const interviews = candidatesData.filter(c => c && c.interview_scheduled).length;
    const assessmentsSent = candidatesData.filter(c => c && c.exam_link_sent).length;
    const assessmentsCompleted = candidatesData.filter(c => c && c.exam_completed).length;
    const hires = candidatesData.filter(c => c && c.final_status === 'Hired').length;
    const pendingAssessments = candidatesData.filter(c => 
      c && c.exam_link_sent && !c.exam_completed && !c.link_expired
    ).length;
    const pendingInterviews = candidatesData.filter(c => {
      if (!c || !c.interview_scheduled || !c.interview_date) return false;
      try {
        return new Date(c.interview_date) > new Date();
      } catch {
        return false;
      }
    }).length;

    setStats({
      totalApplications: total,
      activeInterviews: interviews,
      timeToHire: calculateAverageTimeToHire(candidatesData),
      activeAssessments: pendingAssessments,
      shortlistRate: total > 0 ? ((shortlisted / total) * 100).toFixed(1) : 0,
      assessmentCompletionRate: assessmentsSent > 0 ? ((assessmentsCompleted / assessmentsSent) * 100).toFixed(1) : 0,
      totalHires: hires,
      pendingActions: pendingAssessments + pendingInterviews
    });
  };

  const calculateAverageTimeToHire = (candidates) => {
    if (!Array.isArray(candidates)) return 0;
    
    const hiredCandidates = candidates.filter(c => 
      c && c.final_status === 'Hired' && c.processed_date
    );
    
    if (hiredCandidates.length === 0) return 0;
    
    const totalDays = hiredCandidates.reduce((acc, c) => {
      try {
        const processedDate = new Date(c.processed_date);
        const hireDate = new Date();
        const days = Math.floor((hireDate - processedDate) / (1000 * 60 * 60 * 24));
        return acc + Math.max(days, 0);
      } catch {
        return acc;
      }
    }, 0);
    
    return Math.round(totalDays / hiredCandidates.length);
  };

  const generateNotifications = (candidatesData) => {
    if (!Array.isArray(candidatesData)) {
      setNotifications([]);
      return;
    }

    const notifications = [];
    
    const pendingAssessments = candidatesData.filter(c => 
      c && c.exam_link_sent && !c.exam_completed && !c.link_expired
    );
    
    if (pendingAssessments.length > 0) {
      notifications.push({
        id: 1,
        type: 'warning',
        message: `${pendingAssessments.length} candidates have pending assessments`,
        action: 'View Candidates',
        route: '/candidates'
      });
    }

    const upcomingInterviews = candidatesData.filter(c => {
      if (!c || !c.interview_date) return false;
      try {
        const interviewDate = new Date(c.interview_date);
        const now = new Date();
        const hoursDiff = (interviewDate - now) / (1000 * 60 * 60);
        return hoursDiff > 0 && hoursDiff < 24;
      } catch {
        return false;
      }
    });
    
    if (upcomingInterviews.length > 0) {
      notifications.push({
        id: 2,
        type: 'info',
        message: `${upcomingInterviews.length} interviews scheduled for today`,
        action: 'View Schedule',
        route: '/scheduler'
      });
    }

    setNotifications(notifications);
  };

  const StatCard = ({ title, value, change, icon: Icon, color, subtitle, loading: cardLoading }) => (
    <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-gray-500 text-sm font-medium">{title}</h3>
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      </div>
      <div className="flex items-baseline">
        {cardLoading ? (
          <div className="animate-pulse bg-gray-200 h-8 w-16 rounded"></div>
        ) : (
          <p className="text-3xl font-bold text-gray-900">{value}</p>
        )}
        {change !== undefined && !cardLoading && (
          <span className={`ml-2 text-sm font-medium flex items-center ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {change >= 0 ? <TrendingUp className="w-4 h-4 mr-1" /> : null}
            {change >= 0 ? '+' : ''}{change}%
          </span>
        )}
      </div>
      {subtitle && <p className="text-gray-500 text-xs mt-1">{subtitle}</p>}
    </div>
  );

  const getPipelineStages = () => {
    const stages = [
      { name: 'Applied', value: candidates.length, color: '#3B82F6' },
      { name: 'Screened', value: candidates.filter(c => c && c.ats_score > 0).length, color: '#10B981' },
      { name: 'Shortlisted', value: candidates.filter(c => c && c.status === 'Shortlisted').length, color: '#F59E0B' },
      { name: 'Assessment', value: candidates.filter(c => c && c.exam_completed).length, color: '#8B5CF6' },
      { name: 'Interview', value: candidates.filter(c => c && c.interview_scheduled).length, color: '#EF4444' },
      { name: 'Hired', value: candidates.filter(c => c && c.final_status === 'Hired').length, color: '#059669' }
    ];
    
    return stages;
  };

  const getAssessmentMetrics = () => {
    const sent = candidates.filter(c => c && c.exam_link_sent).length;
    const started = candidates.filter(c => c && c.exam_started).length;
    const completed = candidates.filter(c => c && c.exam_completed).length;
    const passed = candidates.filter(c => c && c.exam_percentage >= 70).length;
    
    return [
      { name: 'Sent', value: sent },
      { name: 'Started', value: started },
      { name: 'Completed', value: completed },
      { name: 'Passed', value: passed }
    ];
  };

  if (loading && !lastFetchTime) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <main className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Recruitment Dashboard</h1>
            <div className="flex items-center mt-1 space-x-4">
              <p className="text-gray-600">Welcome back! Here's your recruitment overview</p>
              {lastFetchTime && (
                <span className="text-xs text-gray-500">
                  Last updated: {lastFetchTime.toLocaleTimeString()}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
              title="Refresh Data"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
            <select
              value={selectedTimeRange}
              onChange={(e) => setSelectedTimeRange(e.target.value)}
              className="border rounded-lg px-4 py-2 text-sm"
            >
              <option value="week">This Week</option>
              <option value="month">This Month</option>
              <option value="quarter">This Quarter</option>
              <option value="year">This Year</option>
            </select>
            <button
              onClick={() => {
                if (jobs.length > 0) {
                  setSelectedPipelineJob(jobs[0]);
                }
              }}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2"
            >
              <Plus className="w-4 h-4" />
              <span>New Pipeline</span>
            </button>
          </div>
        </div>

        {/* Notifications */}
        {notifications.length > 0 && (
          <div className="mb-6 space-y-2">
            {notifications.map(notification => (
              <div
                key={notification.id}
                className={`p-4 rounded-lg border flex items-center justify-between ${
                  notification.type === 'warning' 
                    ? 'bg-yellow-50 border-yellow-200' 
                    : 'bg-blue-50 border-blue-200'
                }`}
              >
                <div className="flex items-center">
                  <AlertCircle className={`w-5 h-5 mr-3 ${
                    notification.type === 'warning' ? 'text-yellow-600' : 'text-blue-600'
                  }`} />
                  <span className={notification.type === 'warning' ? 'text-yellow-800' : 'text-blue-800'}>
                    {notification.message}
                  </span>
                </div>
                <button
                  onClick={() => navigate(notification.route)}
                  className={`px-3 py-1 rounded text-sm font-medium ${
                    notification.type === 'warning'
                      ? 'bg-yellow-600 text-white hover:bg-yellow-700'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {notification.action}
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Applications"
            value={stats.totalApplications}
            change={12.5}
            icon={Users}
            color="bg-blue-600"
            subtitle="All time applications"
            loading={loading}
          />
          <StatCard
            title="Shortlist Rate"
            value={`${stats.shortlistRate}%`}
            change={5.2}
            icon={Target}
            color="bg-green-600"
            subtitle="Candidates shortlisted"
            loading={loading}
          />
          <StatCard
            title="Time-to-Hire"
            value={`${stats.timeToHire}d`}
            change={-8.3}
            icon={Clock}
            color="bg-yellow-600"
            subtitle="Average days to hire"
            loading={loading}
          />
          <StatCard
            title="Pending Actions"
            value={stats.pendingActions}
            icon={Bell}
            color="bg-purple-600"
            subtitle="Requires attention"
            loading={loading}
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Pipeline Funnel */}
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold mb-4">Recruitment Pipeline</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={getPipelineStages()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3B82F6">
                  {getPipelineStages().map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Activity Trend */}
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold mb-4">Recruitment Activity</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={recruitmentData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="applications" stroke="#3B82F6" strokeWidth={2} name="Applications" />
                <Line type="monotone" dataKey="interviews" stroke="#10B981" strokeWidth={2} name="Interviews" />
                <Line type="monotone" dataKey="hires" stroke="#EF4444" strokeWidth={2} name="Hires" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Active Jobs Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-100 mb-8">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Active Job Positions</h3>
              <button
                onClick={() => navigate('/candidates')}
                className="text-blue-600 hover:text-blue-700 text-sm font-medium"
              >
                View All Candidates →
              </button>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
                  <th className="px-6 py-3">Position</th>
                  <th className="px-6 py-3">Department</th>
                  <th className="px-6 py-3">Location</th>
                  <th className="px-6 py-3">Applications</th>
                  <th className="px-6 py-3">Shortlisted</th>
                  <th className="px-6 py-3">In Progress</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {jobs.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="px-6 py-8 text-center text-gray-500">
                      <Users className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                      <p className="text-lg font-medium">No job positions found</p>
                      <p className="mt-1">Start a new recruitment pipeline to begin</p>
                    </td>
                  </tr>
                ) : (
                  jobs.map((job) => {
                    const jobCandidates = candidates.filter(c => c && c.job_id === job.id);
                    const shortlisted = jobCandidates.filter(c => c.status === 'Shortlisted').length;
                    const inProgress = jobCandidates.filter(c => c.exam_link_sent || c.interview_scheduled).length;
                    const currentPipelineStatus = pipelineStatus[job.id];
                    
                    return (
                      <tr key={job.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <div className="text-sm font-medium text-gray-900">{job.title}</div>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">{job.department}</td>
                        <td className="px-6 py-4 text-sm text-gray-500">{job.location}</td>
                        <td className="px-6 py-4">
                          <div className="flex items-center">
                            <span className="text-sm font-medium text-gray-900">{jobCandidates.length}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center">
                            <span className="text-sm font-medium text-green-600">{shortlisted}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center">
                            <span className="text-sm font-medium text-blue-600">{inProgress}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="inline-flex px-2 py-1 text-xs font-semibold leading-5 text-green-800 bg-green-100 rounded-full">
                            Active
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => navigate(`/candidates?job_id=${job.id}`)}
                              className="text-blue-600 hover:text-blue-900 font-medium"
                            >
                              View
                            </button>
                            <button
                              onClick={() => setSelectedPipelineJob(job)}
                              className="text-green-600 hover:text-green-900 font-medium flex items-center"
                            >
                              <Play className="w-3 h-3 mr-1" />
                              Run Pipeline
                            </button>
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

        {/* Assessment Metrics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Assessment Completion */}
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold mb-4">Assessment Metrics</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={getAssessmentMetrics()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#8B5CF6" />
              </BarChart>
            </ResponsiveContainer>
            <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Completion Rate</p>
                <p className="text-xl font-semibold">{stats.assessmentCompletionRate}%</p>
              </div>
              <div>
                <p className="text-gray-500">Pass Rate</p>
                <p className="text-xl font-semibold">
                  {candidates.filter(c => c && c.exam_completed).length > 0
                    ? ((candidates.filter(c => c && c.exam_percentage >= 70).length / candidates.filter(c => c && c.exam_completed).length) * 100).toFixed(1)
                    : 0}%
                </p>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <button
                onClick={() => navigate('/assessments')}
                className="w-full p-4 border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center justify-between transition-colors"
              >
                <div className="flex items-center">
                  <Award className="w-5 h-5 text-purple-600 mr-3" />
                  <span className="font-medium">Manage Assessments</span>
                </div>
                <span className="text-sm text-gray-500">{stats.activeAssessments} pending</span>
              </button>
              
              <button
                onClick={() => navigate('/scheduler')}
                className="w-full p-4 border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center justify-between transition-colors"
              >
                <div className="flex items-center">
                  <Calendar className="w-5 h-5 text-blue-600 mr-3" />
                  <span className="font-medium">Schedule Interviews</span>
                </div>
                <span className="text-sm text-gray-500">{stats.activeInterviews} scheduled</span>
              </button>
              
              <button
                onClick={() => {
                  if (jobs.length > 0) {
                    setSelectedPipelineJob(jobs[0]);
                  }
                }}
                className="w-full p-4 border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center justify-between transition-colors"
              >
                <div className="flex items-center">
                  <Users className="w-5 h-5 text-green-600 mr-3" />
                  <span className="font-medium">Start New Recruitment</span>
                </div>
                <Plus className="w-4 h-4 text-gray-400" />
              </button>
              
              <button
                onClick={() => navigate('/candidates')}
                className="w-full p-4 border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center justify-between transition-colors"
              >
                <div className="flex items-center">
                  <Users className="w-5 h-5 text-indigo-600 mr-3" />
                  <span className="font-medium">View All Candidates</span>
                </div>
                <span className="text-sm text-gray-500">{candidates.length} total</span>
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* Pipeline Runner Modal */}
      {selectedPipelineJob && (
        <PipelineRunner
          job={selectedPipelineJob}
          onPipelineStart={() => {
            setPipelineStatus(prev => ({
              ...prev,
              [selectedPipelineJob.id]: { status: 'running', message: 'Pipeline running...' }
            }));
          }}
          onPipelineComplete={() => {
            fetchDashboardData(true);
            setPipelineStatus(prev => ({
              ...prev,
              [selectedPipelineJob.id]: { status: 'completed', message: 'Pipeline completed!' }
            }));
          }}
          onClose={() => setSelectedPipelineJob(null)}
        />
      )}
    </div>
  );
};

export default Dashboard;