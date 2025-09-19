// ResultsManagement.jsx - Add this as a new component and integrate with AssessmentInterface

import React, { useState, useEffect } from 'react';
import { 
  RefreshCw, 
  Download, 
  AlertCircle, 
  CheckCircle, 
  Clock, 
  Eye, 
  Send, 
  Target,
  Activity,
  Users,
  TrendingUp,
  Settings
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:5000";

const ResultsManagement = ({ selectedJob, candidates, onRefreshCandidates }) => {
  const [scrapingStatus, setScrapingStatus] = useState('');
  const [isScrapingLoading, setIsScrapingLoading] = useState(false);
  const [showManualProcessModal, setShowManualProcessModal] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [automationSettings, setAutomationSettings] = useState({
    enabled: false,
    checkInterval: 30, // minutes
    autoProcess: true
  });

  // Get pending assessments that need result checking
  const getPendingAssessments = () => {
    return candidates.filter(c => 
      c.exam_link_sent && 
      !c.exam_completed && 
      !c.link_expired &&
      c.assessment_invite_link
    );
  };

  // Get recently completed assessments
  const getRecentCompletions = () => {
    const completed = candidates.filter(c => c.exam_completed);
    return completed
      .sort((a, b) => new Date(b.exam_completed_date) - new Date(a.exam_completed_date))
      .slice(0, 5);
  };

  // Calculate assessment metrics
  const getAssessmentMetrics = () => {
    const pending = getPendingAssessments();
    const completed = candidates.filter(c => c.exam_completed);
    const passed = completed.filter(c => c.exam_percentage >= 70);
    const avgScore = completed.length > 0 
      ? (completed.reduce((sum, c) => sum + (c.exam_percentage || 0), 0) / completed.length).toFixed(1)
      : 0;

    return {
      pending: pending.length,
      completed: completed.length,
      passed: passed.length,
      passRate: completed.length > 0 ? ((passed.length / completed.length) * 100).toFixed(1) : 0,
      avgScore
    };
  };

  // Scrape results for specific assessment
  const handleScrapeAssessment = async (assessmentName) => {
    if (!assessmentName) {
      setScrapingStatus('❌ Please select a job first');
      return;
    }

    setIsScrapingLoading(true);
    setScrapingStatus(`🔍 Scraping results for "${assessmentName}"...`);

    try {
      const response = await fetch(`${BACKEND_URL}/api/scrape_assessment_results`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ assessment_name: assessmentName })
      });

      const data = await response.json();

      if (data.success) {
        setScrapingStatus(`✅ ${data.message}`);
        // Refresh candidates after 3 seconds
        setTimeout(() => {
          onRefreshCandidates();
          setScrapingStatus('');
        }, 3000);
      } else {
        setScrapingStatus(`❌ Error: ${data.message}`);
      }
    } catch (error) {
      setScrapingStatus(`❌ Network error: ${error.message}`);
    } finally {
      setIsScrapingLoading(false);
      // Clear status after 10 seconds
      setTimeout(() => setScrapingStatus(''), 10000);
    }
  };

  // Scrape all pending assessments
  const handleScrapeAllPending = async () => {
    setIsScrapingLoading(true);
    setScrapingStatus('🔍 Scraping all pending assessments...');

    try {
      const response = await fetch(`${BACKEND_URL}/api/scrape_all_pending_results`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      const data = await response.json();

      if (data.success) {
        setScrapingStatus(`✅ ${data.message}`);
        // Refresh candidates after 5 seconds
        setTimeout(() => {
          onRefreshCandidates();
          setScrapingStatus('');
        }, 5000);
      } else {
        setScrapingStatus(`❌ Error: ${data.message}`);
      }
    } catch (error) {
      setScrapingStatus(`❌ Network error: ${error.message}`);
    } finally {
      setIsScrapingLoading(false);
      setTimeout(() => setScrapingStatus(''), 15000);
    }
  };

  // Manual process candidate result
  const handleManualProcess = async (candidateEmail, score, totalQuestions) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/manual_process_candidate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_email: candidateEmail,
          exam_score: parseInt(score),
          total_questions: parseInt(totalQuestions),
          time_taken: 0
        })
      });

      const data = await response.json();

      if (data.success) {
        setScrapingStatus(`✅ ${data.message}`);
        onRefreshCandidates();
        setShowManualProcessModal(false);
      } else {
        setScrapingStatus(`❌ Error: ${data.message}`);
      }
    } catch (error) {
      setScrapingStatus(`❌ Error: ${error.message}`);
    }
  };

  const metrics = getAssessmentMetrics();
  const pendingAssessments = getPendingAssessments();
  const recentCompletions = getRecentCompletions();

  // Manual Process Modal Component
  const ManualProcessModal = () => {
    const [score, setScore] = useState('');
    const [totalQuestions, setTotalQuestions] = useState('100');

    const handleSubmit = (e) => {
      e.preventDefault();
      handleManualProcess(selectedCandidate.email, score, totalQuestions);
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
          <h3 className="text-lg font-semibold mb-4">
            Manual Process: {selectedCandidate?.name}
          </h3>
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">
                Score (correct answers)
              </label>
              <input
                type="number"
                value={score}
                onChange={(e) => setScore(e.target.value)}
                className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
                min="0"
                placeholder="Enter number of correct answers"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">
                Total Questions
              </label>
              <input
                type="number"
                value={totalQuestions}
                onChange={(e) => setTotalQuestions(e.target.value)}
                className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
                min="1"
              />
            </div>
            <div className="mb-4 p-3 bg-gray-50 rounded">
              <p className="text-sm text-gray-600">
                <strong>Percentage:</strong> {score && totalQuestions ? ((score / totalQuestions) * 100).toFixed(1) : 0}%
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Candidates scoring ≥70% will be scheduled for interviews
              </p>
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                className="flex-1 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                disabled={!score || !totalQuestions}
              >
                Process Result
              </button>
              <button
                type="button"
                onClick={() => setShowManualProcessModal(false)}
                className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Status Messages */}
      {scrapingStatus && (
        <div className={`p-4 rounded-lg border flex items-center ${
          scrapingStatus.includes('❌') 
            ? 'bg-red-50 border-red-200 text-red-700' 
            : scrapingStatus.includes('✅')
            ? 'bg-green-50 border-green-200 text-green-700'
            : 'bg-blue-50 border-blue-200 text-blue-700'
        }`}>
          <div className="flex items-center">
            {scrapingStatus.includes('🔍') && (
              <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
            )}
            {scrapingStatus.includes('✅') && (
              <CheckCircle className="w-5 h-5 mr-2" />
            )}
            {scrapingStatus.includes('❌') && (
              <AlertCircle className="w-5 h-5 mr-2" />
            )}
            <span>{scrapingStatus}</span>
          </div>
        </div>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Pending Results</p>
              <p className="text-2xl font-bold text-orange-600">{metrics.pending}</p>
            </div>
            <Clock className="w-8 h-8 text-orange-600" />
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Completed</p>
              <p className="text-2xl font-bold text-green-600">{metrics.completed}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Pass Rate</p>
              <p className="text-2xl font-bold text-blue-600">{metrics.passRate}%</p>
            </div>
            <Target className="w-8 h-8 text-blue-600" />
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Score</p>
              <p className="text-2xl font-bold text-purple-600">{metrics.avgScore}%</p>
            </div>
            <TrendingUp className="w-8 h-8 text-purple-600" />
          </div>
        </div>
      </div>

      {/* Main Actions */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Results Management</h3>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => selectedJob && handleScrapeAssessment(selectedJob.title)}
              disabled={!selectedJob || isScrapingLoading}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              <Eye className="w-4 h-4 mr-2" />
              {isScrapingLoading ? 'Scraping...' : 'Check Results'}
            </button>
            
            <button
              onClick={handleScrapeAllPending}
              disabled={isScrapingLoading || pendingAssessments.length === 0}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isScrapingLoading ? 'animate-spin' : ''}`} />
              Check All Pending
            </button>
          </div>
        </div>

        {!selectedJob && (
          <div className="text-center py-8 text-gray-500">
            <Users className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>Select a job position to manage assessment results</p>
          </div>
        )}

        {selectedJob && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Pending Assessments */}
            <div>
              <h4 className="font-medium mb-3">
                Pending Assessments ({pendingAssessments.length})
              </h4>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {pendingAssessments.length === 0 ? (
                  <p className="text-gray-500 text-sm">No pending assessments</p>
                ) : (
                  pendingAssessments.map((candidate) => (
                    <div key={candidate.id} className="border rounded p-3">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">{candidate.name}</p>
                          <p className="text-sm text-gray-500">{candidate.email}</p>
                          <p className="text-xs text-gray-400">
                            Sent: {candidate.exam_link_sent_date 
                              ? new Date(candidate.exam_link_sent_date).toLocaleDateString()
                              : 'N/A'}
                          </p>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => {
                              setSelectedCandidate(candidate);
                              setShowManualProcessModal(true);
                            }}
                            className="text-blue-600 hover:text-blue-700 text-sm"
                          >
                            Manual Process
                          </button>
                          {candidate.assessment_invite_link && (
                            <a
                              href={candidate.assessment_invite_link}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-green-600 hover:text-green-700 text-sm"
                            >
                              View
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Recent Completions */}
            <div>
              <h4 className="font-medium mb-3">
                Recent Completions ({recentCompletions.length})
              </h4>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {recentCompletions.length === 0 ? (
                  <p className="text-gray-500 text-sm">No completed assessments yet</p>
                ) : (
                  recentCompletions.map((candidate) => (
                    <div key={candidate.id} className="border rounded p-3">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">{candidate.name}</p>
                          <p className="text-sm text-gray-500">{candidate.email}</p>
                          <div className="flex items-center space-x-2 mt-1">
                            <span className={`px-2 py-1 rounded text-xs ${
                              candidate.exam_percentage >= 70 
                                ? 'bg-green-100 text-green-700' 
                                : 'bg-red-100 text-red-700'
                            }`}>
                              {candidate.exam_percentage?.toFixed(0)}%
                            </span>
                            <span className="text-xs text-gray-400">
                              {candidate.exam_completed_date 
                                ? new Date(candidate.exam_completed_date).toLocaleDateString()
                                : 'N/A'}
                            </span>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium">
                            {candidate.final_status || 'Processing...'}
                          </p>
                          {candidate.exam_feedback && (
                            <p className="text-xs text-gray-500 mt-1 max-w-32 truncate">
                              {candidate.exam_feedback}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Automation Settings */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold flex items-center">
            <Settings className="w-5 h-5 mr-2" />
            Automation Settings
          </h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center justify-between p-3 border rounded">
            <div>
              <p className="font-medium">Auto-Check Results</p>
              <p className="text-sm text-gray-500">Automatically check for new results</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={automationSettings.enabled}
                onChange={(e) => setAutomationSettings({
                  ...automationSettings,
                  enabled: e.target.checked
                })}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
          
          <div className="p-3 border rounded">
            <label className="block font-medium mb-2">Check Interval</label>
            <select
              value={automationSettings.checkInterval}
              onChange={(e) => setAutomationSettings({
                ...automationSettings,
                checkInterval: parseInt(e.target.value)
              })}
              className="w-full border rounded px-3 py-2 text-sm"
            >
              <option value="15">Every 15 minutes</option>
              <option value="30">Every 30 minutes</option>
              <option value="60">Every hour</option>
              <option value="120">Every 2 hours</option>
            </select>
          </div>
          
          <div className="flex items-center justify-between p-3 border rounded">
            <div>
              <p className="font-medium">Auto-Process</p>
              <p className="text-sm text-gray-500">Send emails automatically</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={automationSettings.autoProcess}
                onChange={(e) => setAutomationSettings({
                  ...automationSettings,
                  autoProcess: e.target.checked
                })}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
        </div>
      </div>

      {/* Manual Process Modal */}
      {showManualProcessModal && selectedCandidate && <ManualProcessModal />}
    </div>
  );
};

export default ResultsManagement;