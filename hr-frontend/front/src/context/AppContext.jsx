import React, { createContext, useState, useContext, useEffect } from 'react';

const AppContext = createContext();

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};

export const AppProvider = ({ children }) => {
  const [candidates, setCandidates] = useState([]);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:5000";

  // Fetch candidates
  const fetchCandidates = async (jobId = null) => {
    setLoading(true);
    try {
      const url = jobId 
        ? `${BACKEND_URL}/api/candidates?job_id=${jobId}`
        : `${BACKEND_URL}/api/candidates`;
      
      const response = await fetch(url);
      const data = await response.json();
      
      // Transform data for frontend compatibility
      const transformedCandidates = data.map(candidate => ({
        id: candidate.id,
        name: candidate.name,
        email: candidate.email,
        role: candidate.job_title,
        job_id: candidate.job_id,
        job_title: candidate.job_title,
        experience: "5+ years", // Mock data
        location: "Remote",
        education: "BS Computer Science",
        applied: candidate.processed_date,
        skills: ["Python", "React", "AWS", "Node.js", "Docker"], // Mock skills
        score: candidate.ats_score || 0,
        status: candidate.status === "Shortlisted" ? "Qualified" : "Not Qualified",
        statusColor: candidate.status === "Shortlisted" ? "green" : "red",
        photo: null,
        // Assessment data
        exam_link_sent: candidate.exam_link_sent,
        exam_completed: candidate.exam_completed,
        exam_percentage: candidate.exam_percentage,
        interview_scheduled: candidate.interview_scheduled,
        interview_date: candidate.interview_date,
        assessment_invite_link: candidate.assessment_invite_link
      }));
      
      setCandidates(transformedCandidates);
    } catch (error) {
      console.error('Error fetching candidates:', error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch jobs
  const fetchJobs = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/jobs`);
      const data = await response.json();
      setJobs(Array.isArray(data) ? data : data.jobs || []);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
  };

  // Schedule interview
  const scheduleInterview = async (candidateId, dateTime, interviewers) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/schedule-interview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_id: candidateId,
          date: dateTime,
          time_slot: new Date(dateTime).toLocaleTimeString(),
          interviewers: interviewers
        })
      });
      
      const data = await response.json();
      if (data.success) {
        // Refresh candidates to show updated status
        await fetchCandidates();
      }
      return data;
    } catch (error) {
      console.error('Error scheduling interview:', error);
      throw error;
    }
  };

  // Run recruitment pipeline
  const runPipeline = async (jobId, jobTitle, jobDesc) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/run_full_pipeline`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: jobId,
          job_title: jobTitle,
          job_desc: jobDesc || ''
        })
      });
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error running pipeline:', error);
      throw error;
    }
  };

  // Initial data fetch
  useEffect(() => {
    fetchJobs();
    fetchCandidates();
  }, []);

  const value = {
    candidates,
    setCandidates,
    selectedCandidate,
    setSelectedCandidate,
    jobs,
    loading,
    fetchCandidates,
    fetchJobs,
    scheduleInterview,
    runPipeline,
    BACKEND_URL
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};