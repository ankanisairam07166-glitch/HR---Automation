// Create a config file: src/config/api.ts
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5000';

export const api = {
  // Jobs
  getJobs: () => fetch(`${API_BASE_URL}/api/jobs`),
  
  // Candidates
  getCandidates: (jobId?: string) => 
    fetch(`${API_BASE_URL}/api/candidates${jobId ? `?job_id=${jobId}` : ''}`),
  
  // Interview
  getInterview: (token: string) => 
    fetch(`${API_BASE_URL}/api/avatar/interview/${token}`),
  
  // Schedule Interview
  scheduleInterview: (data: any) =>
    fetch(`${API_BASE_URL}/api/schedule-interview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),
};