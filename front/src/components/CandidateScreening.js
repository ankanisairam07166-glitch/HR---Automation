import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { Search, Filter, CheckCircle, XCircle, Clock, Calendar, FileText, Tag, Download, Plus, X, Mail, Eye, ExternalLink, GitBranch, Linkedin, Star, RefreshCw, Send, Users, PlayCircle, AlertCircle } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import Navigation from './Navigation';
import InteractivePipelineRunner from './InteractivePipelineRunner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:5000";

// Debounce hook for search optimization
const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

// Custom hook for candidates data management
const useCandidates = (selectedJob) => {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastFetchTime, setLastFetchTime] = useState(null);

  const fetchCandidates = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const startTime = Date.now();
      let url = `${BACKEND_URL}/api/candidates`;
      if (selectedJob) {
        url += `?job_id=${selectedJob.id}`;
      }
      
      const response = await fetch(url, {
        headers: { 'Cache-Control': 'max-age=180' }
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch candidates: ${response.status}`);
      }
      
      const data = await response.json();
      console.log(`Candidates fetch took ${Date.now() - startTime}ms`);
      
      setCandidates(data);
      setLastFetchTime(new Date());
    } catch (err) {
      setError(err.message);
      console.error('Error fetching candidates:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedJob]);

  useEffect(() => {
    fetchCandidates();
  }, [fetchCandidates]);

  return { candidates, loading, error, refetch: fetchCandidates, lastFetchTime };
};

// Custom hook for jobs data management
const useJobs = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/jobs`, {
        headers: { 'Cache-Control': 'max-age=300' }
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch jobs: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (Array.isArray(data)) {
        setJobs(data);
        console.log('Jobs loaded:', data.length);
        return data;
      } else {
        setJobs([]);
        return [];
      }
    } catch (error) {
      console.error('Error fetching jobs:', error);
      setJobs([]);
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  return { jobs, loading, refetch: fetchJobs };
};

// Custom hook for pipeline status management
const usePipelineStatus = (selectedJob) => {
  const [pipelineStatus, setPipelineStatus] = useState({});
  const intervalRef = useRef(null);

  const fetchPipelineStatus = useCallback(async () => {
    if (!selectedJob) return;
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/pipeline_status/${selectedJob.id}`);
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.status) {
          setPipelineStatus(prev => ({
            ...prev,
            [selectedJob.id]: data.status
          }));
          return data.status;
        }
      }
    } catch (error) {
      console.error('Error fetching pipeline status:', error);
    }
  }, [selectedJob]);

  useEffect(() => {
    if (selectedJob) {
      fetchPipelineStatus();
      intervalRef.current = setInterval(fetchPipelineStatus, 5000);
      
      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }
  }, [selectedJob, fetchPipelineStatus]);

  const updatePipelineStatus = useCallback((jobId, status) => {
    setPipelineStatus(prev => ({
      ...prev,
      [jobId]: status
    }));
  }, []);

  return { 
    pipelineStatus, 
    updatePipelineStatus,
    currentStatus: selectedJob ? pipelineStatus[selectedJob.id] : null
  };
};

// Memoized status map to prevent recreations
const STATUS_MAP = {
  'Hired': { color: 'bg-green-100 text-green-800', icon: CheckCircle, priority: 8 },
  'Interview Scheduled': { color: 'bg-blue-100 text-blue-800', icon: Calendar, priority: 7 },
  'Assessment Passed': { color: 'bg-green-100 text-green-800', icon: CheckCircle, priority: 6 },
  'Assessment Failed': { color: 'bg-red-100 text-red-800', icon: XCircle, priority: 5 },
  'Assessment In Progress': { color: 'bg-yellow-100 text-yellow-800', icon: Clock, priority: 4 },
  'Assessment Sent': { color: 'bg-blue-100 text-blue-800', icon: Mail, priority: 3 },
  'Assessment Expired': { color: 'bg-gray-100 text-gray-800', icon: Clock, priority: 2 },
  'Shortlisted': { color: 'bg-green-100 text-green-800', icon: CheckCircle, priority: 2 },
  'Rejected': { color: 'bg-red-100 text-red-800', icon: XCircle, priority: 1 },
  'Under Review': { color: 'bg-gray-100 text-gray-800', icon: Clock, priority: 0 }
};

// Utility functions
const getDisplayStatus = (candidate) => {
  if (candidate.final_status === 'Hired') return 'Hired';
  if (candidate.interview_scheduled) return 'Interview Scheduled';
  if (candidate.exam_completed) {
    return candidate.exam_percentage >= 70 ? 'Assessment Passed' : 'Assessment Failed';
  }
  if (candidate.exam_started) return 'Assessment In Progress';
  if (candidate.exam_link_sent) {
    return candidate.link_expired ? 'Assessment Expired' : 'Assessment Sent';
  }
  if (candidate.status === 'Shortlisted') return 'Shortlisted';
  if (candidate.status === 'Rejected') return 'Rejected';
  return 'Under Review';
};

const getCandidateStatusInfo = (candidate) => {
  const status = getDisplayStatus(candidate);
  return STATUS_MAP[status] || STATUS_MAP['Under Review'];
};

const getScoreColor = (score) => {
  if (score >= 85) return 'text-green-600';
  if (score >= 70) return 'text-yellow-600';
  return 'text-red-600';
};

// Optimized Filter Bar Component
const FilterBar = React.memo(({ 
  jobs, 
  selectedJob, 
  onJobChange, 
  searchTerm, 
  onSearchChange, 
  filterStatus, 
  onFilterStatusChange, 
  sortBy, 
  onSortChange 
}) => (
  <div className="mb-6 flex flex-wrap items-center gap-4">
    <select
      value={selectedJob?.id || ''}
      onChange={(e) => {
        const job = jobs.find(j => j.id == e.target.value);
        onJobChange(job || null);
      }}
      className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
    >
      <option value="">All Jobs</option>
      {jobs.map(job => (
        <option key={job.id} value={job.id}>
          {job.title} ({job.location})
        </option>
      ))}
    </select>
    
    <div className="relative flex-1 max-w-md">
      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
      <input
        type="text"
        placeholder="Search candidates..."
        value={searchTerm}
        onChange={(e) => onSearchChange(e.target.value)}
        className="pl-10 pr-4 py-2 w-full border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
    </div>
    
    <select
      value={filterStatus}
      onChange={(e) => onFilterStatusChange(e.target.value)}
      className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
    >
      <option value="all">All Status</option>
      <option value="shortlisted">Shortlisted</option>
      <option value="assessment_pending">Assessment Pending</option>
      <option value="assessment_completed">Assessment Completed</option>
      <option value="interview_scheduled">Interview Scheduled</option>
      <option value="rejected">Rejected</option>
    </select>
    
    <select
      value={sortBy}
      onChange={(e) => onSortChange(e.target.value)}
      className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
    >
      <option value="score_desc">Score (High to Low)</option>
      <option value="score_asc">Score (Low to High)</option>
      <option value="date_desc">Date (Newest First)</option>
      <option value="date_asc">Date (Oldest First)</option>
      <option value="name">Name (A-Z)</option>
      <option value="status">Status Priority</option>
    </select>
  </div>
));

// Optimized Candidate Card Component
const CandidateCard = React.memo(({ candidate, isSelected, onClick }) => {
  const StatusIcon = candidate.statusInfo.icon;
  const daysSinceProcessed = Math.floor((new Date() - new Date(candidate.processed_date)) / (1000 * 60 * 60 * 24));
  
  return (
    <div
      className={`p-4 cursor-pointer transition-all border-l-4 ${
        isSelected 
          ? 'bg-blue-50 border-blue-500 shadow-md' 
          : 'hover:bg-gray-50 border-transparent hover:border-gray-300'
      }`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3 flex-1">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-medium flex-shrink-0">
            {candidate.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
          </div>
          <div className="flex-1">
            <h3 className="font-medium text-gray-900">{candidate.name}</h3>
            <p className="text-sm text-gray-500">{candidate.email}</p>
            <p className="text-xs text-gray-400 mt-1">{candidate.job_title} • Applied {daysSinceProcessed}d ago</p>
          </div>
        </div>
        
        <div className="flex flex-col items-end ml-4">
          <div className="flex items-center space-x-1 mb-2">
            <span className={`text-lg font-bold ${candidate.scoreColor}`}>
              {candidate.displayScore.toFixed(0)}
            </span>
            <span className="text-sm text-gray-500">/100</span>
          </div>
          
          <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${candidate.statusInfo.color}`}>
            <StatusIcon className="w-3 h-3 mr-1" />
            {candidate.displayStatus}
          </span>
        </div>
      </div>
    </div>
  );
});

// Loading skeleton component
const CandidateListSkeleton = () => (
  <div className="p-4 space-y-4">
    {[...Array(5)].map((_, i) => (
      <div key={i} className="animate-pulse flex space-x-4">
        <div className="rounded-full bg-gray-200 h-10 w-10 flex-shrink-0"></div>
        <div className="flex-1 space-y-2 py-1">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-3 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    ))}
  </div>
);

// Main Component
const CandidateScreening = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const jobIdFromUrl = searchParams.get('job_id');
  
  // State management
  const [selectedJob, setSelectedJob] = useState(null);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [sortBy, setSortBy] = useState('score_desc');
  const [refreshing, setRefreshing] = useState(false);
  const [message, setMessage] = useState('');
  const [showPipelineModal, setShowPipelineModal] = useState(false);

  // Custom hooks
  const { jobs, refetch: refetchJobs } = useJobs();
  const { candidates, loading, error, refetch: refetchCandidates, lastFetchTime } = useCandidates(selectedJob);
  const { pipelineStatus, updatePipelineStatus, currentStatus } = usePipelineStatus(selectedJob);

  // Debounced search
  const debouncedSearchTerm = useDebounce(searchTerm, 300);

  // Memoized processed candidates
  const processedCandidates = useMemo(() => 
    candidates.map(candidate => ({
      ...candidate,
      displayStatus: getDisplayStatus(candidate),
      displayScore: candidate.ats_score || 0,
      scoreColor: getScoreColor(candidate.ats_score || 0),
      statusInfo: getCandidateStatusInfo(candidate)
    })), [candidates]
  );

  // Memoized filtered and sorted candidates
  const filteredCandidates = useMemo(() => {
    let filtered = processedCandidates;
    
    // Apply search filter
    if (debouncedSearchTerm) {
      const searchLower = debouncedSearchTerm.toLowerCase();
      filtered = filtered.filter(c => 
        c.name.toLowerCase().includes(searchLower) ||
        c.email.toLowerCase().includes(searchLower) ||
        c.job_title?.toLowerCase().includes(searchLower)
      );
    }
    
    // Apply status filter
    if (filterStatus !== 'all') {
      filtered = filtered.filter(c => {
        switch (filterStatus) {
          case 'shortlisted':
            return c.status === 'Shortlisted';
          case 'assessment_pending':
            return c.exam_link_sent && !c.exam_completed && !c.link_expired;
          case 'assessment_completed':
            return c.exam_completed;
          case 'interview_scheduled':
            return c.interview_scheduled;
          case 'rejected':
            return c.status === 'Rejected' || c.final_status === 'Rejected After Exam';
          default:
            return true;
        }
      });
    }
    
    // Apply sorting
    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'score_desc':
          return (b.ats_score || 0) - (a.ats_score || 0);
        case 'score_asc':
          return (a.ats_score || 0) - (b.ats_score || 0);
        case 'date_desc':
          return new Date(b.processed_date) - new Date(a.processed_date);
        case 'date_asc':
          return new Date(a.processed_date) - new Date(b.processed_date);
        case 'name':
          return a.name.localeCompare(b.name);
        case 'status':
          return b.statusInfo.priority - a.statusInfo.priority;
        default:
          return 0;
      }
    });
  }, [processedCandidates, debouncedSearchTerm, filterStatus, sortBy]);

  // Initialize with job from URL if present
  useEffect(() => {
    if (jobIdFromUrl && jobs.length > 0) {
      const job = jobs.find(j => j.id === jobIdFromUrl);
      if (job) setSelectedJob(job);
    }
  }, [jobIdFromUrl, jobs]);

  // Auto-select first candidate when list changes
  useEffect(() => {
    if (filteredCandidates.length > 0 && !selectedCandidate) {
      setSelectedCandidate(filteredCandidates[0]);
    }
  }, [filteredCandidates, selectedCandidate]);

  // Event handlers
  const refreshData = async () => {
    setRefreshing(true);
    await Promise.all([refetchJobs(), refetchCandidates()]);
    setRefreshing(false);
    setMessage('Data refreshed successfully!');
    setTimeout(() => setMessage(''), 3000);
  };

  const sendAssessmentReminder = async (candidateId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/send_reminder/${candidateId}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        setMessage('Reminder sent successfully!');
        setTimeout(() => setMessage(''), 3000);
        refetchCandidates();
      }
    } catch (error) {
      console.error('Error sending reminder:', error);
      setMessage('Failed to send reminder');
      setTimeout(() => setMessage(''), 3000);
    }
  };

  // Component sub-components
  const CandidateDetails = ({ candidate }) => {
    if (!candidate) {
      return (
        <div className="p-8 text-center text-gray-500">
          <Eye className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-lg font-medium">Select a candidate to view details</p>
        </div>
      );
    }

    const timeline = getTimelineEvents(candidate);
    const assessmentStats = getAssessmentStats(candidate);

    return (
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white text-xl font-medium">
              {candidate.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">{candidate.name}</h2>
              <p className="text-gray-500">{candidate.job_title}</p>
              <div className="flex items-center space-x-3 mt-2">
                <a href={`mailto:${candidate.email}`} className="text-sm text-blue-600 hover:text-blue-700">
                  {candidate.email}
                </a>
              </div>
            </div>
          </div>
          
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full border-4 border-blue-100 bg-white">
              <div>
                <div className={`text-2xl font-bold ${candidate.scoreColor}`}>
                  {candidate.displayScore.toFixed(0)}
                </div>
                <div className="text-xs text-gray-500">ATS Score</div>
              </div>
            </div>
          </div>
        </div>

        {/* Status Badge */}
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Current Status</p>
              <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium ${candidate.statusInfo.color}`}>
                <candidate.statusInfo.icon className="w-4 h-4 mr-1.5" />
                {candidate.displayStatus}
              </span>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600 mb-1">Applied</p>
              <p className="font-medium">{new Date(candidate.processed_date).toLocaleDateString()}</p>
            </div>
          </div>
        </div>

        {/* Timeline, Assessment Stats, and Actions - Same as before */}
        {/* ... */}
        
        {/* Actions */}
        <div className="space-y-3">
          {candidate.resume_path && (
            <button className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
              <Download className="w-4 h-4 mr-2" />
              Download Resume
            </button>
          )}
          
          {candidate.exam_link_sent && !candidate.exam_completed && !candidate.link_expired && (
            <button 
              onClick={() => sendAssessmentReminder(candidate.id)}
              className="w-full flex items-center justify-center px-4 py-2 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50"
            >
              <Send className="w-4 h-4 mr-2" />
              Send Reminder
            </button>
          )}
          
          {candidate.exam_completed && candidate.exam_percentage >= 70 && !candidate.interview_scheduled && (
            <button 
              onClick={() => navigate(`/scheduler?candidate_id=${candidate.id}`)}
              className="w-full flex items-center justify-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              <Calendar className="w-4 h-4 mr-2" />
              Schedule Interview
            </button>
          )}
        </div>
      </div>
    );
  };

  const getTimelineEvents = (candidate) => {
    const events = [
      {
        title: 'Application Received',
        date: new Date(candidate.processed_date).toLocaleDateString(),
        completed: true
      }
    ];
    
    if (candidate.status === 'Shortlisted') {
      events.push({
        title: 'Shortlisted',
        date: new Date(candidate.processed_date).toLocaleDateString(),
        completed: true
      });
    }
    
    return events;
  };

  const getAssessmentStats = (candidate) => {
    if (!candidate.exam_completed) return null;
    
    return {
      score: candidate.exam_percentage?.toFixed(0) || 0,
      correct: candidate.exam_correct_answers || candidate.exam_score || 0,
      total: candidate.exam_total_questions || 0,
      timeTaken: candidate.exam_time_taken || 0,
      completedDate: candidate.exam_completed_date 
        ? new Date(candidate.exam_completed_date).toLocaleDateString() 
        : 'N/A'
    };
  };

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Navigation />
      
      <main className="flex-grow p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Candidate Screening</h1>
            {selectedJob && (
              <div className="flex items-center mt-1 space-x-4">
                <p className="text-gray-600">
                  {selectedJob.title} • {selectedJob.location} • {filteredCandidates.length} candidates
                </p>
                {lastFetchTime && (
                  <span className="text-xs text-gray-500">
                    Updated: {lastFetchTime.toLocaleTimeString()}
                  </span>
                )}
              </div>
            )}
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={refreshData}
              className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50"
              disabled={refreshing}
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
            {selectedJob && (
              <button
                onClick={() => setShowPipelineModal(true)}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                <PlayCircle className="w-4 h-4 mr-2" />
                Run Pipeline
              </button>
            )}
            <button
              onClick={() => {
                const newJob = { 
                  id: 'new', 
                  title: 'New Position', 
                  location: 'Remote',
                  description: '' 
                };
                setSelectedJob(newJob);
                setShowPipelineModal(true);
              }}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Pipeline
            </button>
          </div>
        </div>

        {/* Success Message */}
        {message && (
          <div className="mb-4 p-4 bg-green-100 text-green-700 rounded-lg flex items-center">
            <CheckCircle className="w-5 h-5 mr-2" />
            {message}
          </div>
        )}

        {/* Filters */}
        <FilterBar
          jobs={jobs}
          selectedJob={selectedJob}
          onJobChange={setSelectedJob}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          filterStatus={filterStatus}
          onFilterStatusChange={setFilterStatus}
          sortBy={sortBy}
          onSortChange={setSortBy}
        />

        {/* Main Content */}
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Candidate List */}
          <div className="lg:w-1/2 bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="p-4 border-b border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between">
                <h2 className="font-medium text-gray-700">Candidates</h2>
                <span className="text-sm text-gray-500">
                  {filteredCandidates.length} of {candidates.length}
                </span>
              </div>
            </div>
            <div className="divide-y divide-gray-200 max-h-[calc(100vh-300px)] overflow-y-auto">
              {loading ? (
                <CandidateListSkeleton />
              ) : filteredCandidates.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <Users className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p className="text-lg font-medium">No candidates found</p>
                  <p className="mt-1">
                    {candidates.length === 0 
                      ? "Try adjusting your filters or run a new pipeline"
                      : "Try adjusting your search or filters"
                    }
                  </p>
                  {candidates.length === 0 && (
                    <button
                      onClick={() => {
                        const newJob = selectedJob || { 
                          id: 'new', 
                          title: 'New Position', 
                          location: 'Remote',
                          description: '' 
                        };
                        setSelectedJob(newJob);
                        setShowPipelineModal(true);
                      }}
                      className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      Run New Pipeline
                    </button>
                  )}
                </div>
              ) : (
                filteredCandidates.map((candidate) => (
                  <CandidateCard
                    key={candidate.id}
                    candidate={candidate}
                    isSelected={selectedCandidate?.id === candidate.id}
                    onClick={() => setSelectedCandidate(candidate)}
                  />
                ))
              )}
            </div>
          </div>

          {/* Candidate Details */}
          <div className="lg:w-1/2 bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="p-4 border-b border-gray-200 bg-gray-50">
              <h2 className="font-medium text-gray-700">Candidate Details</h2>
            </div>
            <div className="max-h-[calc(100vh-300px)] overflow-y-auto">
              <CandidateDetails candidate={selectedCandidate} />
            </div>
          </div>
        </div>
      </main>
      
      {/* Interactive Pipeline Runner Modal */}
      {showPipelineModal && selectedJob && (
        <InteractivePipelineRunner
          job={selectedJob}
          onPipelineStart={() => {
            updatePipelineStatus(selectedJob.id, { 
              status: 'running', 
              message: 'Pipeline running...' 
            });
          }}
          onPipelineComplete={() => {
            refetchCandidates();
            updatePipelineStatus(selectedJob.id, { 
              status: 'completed', 
              message: 'Pipeline completed!' 
            });
            setMessage('Pipeline completed successfully!');
            setTimeout(() => setMessage(''), 5000);
          }}
          onClose={() => setShowPipelineModal(false)}
        />
      )}
    </div>
  );
};

export default CandidateScreening;