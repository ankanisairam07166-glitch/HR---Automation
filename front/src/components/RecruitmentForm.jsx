import React, { useState } from 'react';
import { useAppContext } from './AppContext'; // Adjust path as needed

const RecruitmentForm = () => {
  const { runPipeline, jobs } = useAppContext();
  const [jobId, setJobId] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [jobDesc, setJobDesc] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  // Optional: Automatically fill job title when job selected
  const handleJobChange = (e) => {
    const id = e.target.value;
    setJobId(id);
    const job = jobs.find(j => String(j.id) === String(id));
    if (job) setJobTitle(job.title);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    try {
      const result = await runPipeline(jobId, jobTitle, jobDesc);
      if (result.success) {
        setMessage('✅ Pipeline started successfully!');
      } else {
        setMessage('❌ Failed to start pipeline: ' + (result.error || 'Unknown error'));
      }
    } catch (err) {
      setMessage('❌ Error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ 
      border: "1px solid #e0e0e0", borderRadius: 12, padding: 24, maxWidth: 420, margin: "32px auto", background: "#fafbfc", boxShadow: "0 2px 16px rgba(0,0,0,0.06)" 
    }}>
      <h2 style={{ marginBottom: 20 }}>Start New Recruitment Pipeline</h2>
      <label style={{ display: "block", marginBottom: 8 }}>Select Job:</label>
      <select value={jobId} onChange={handleJobChange} required style={{ width: "100%", padding: 8, borderRadius: 8, marginBottom: 18 }}>
        <option value="">-- Select --</option>
        {jobs.map(job => (
          <option key={job.id} value={job.id}>
            {job.title} ({job.location})
          </option>
        ))}
      </select>

      <label style={{ display: "block", marginBottom: 8 }}>Job Title:</label>
      <input
        type="text"
        value={jobTitle}
        onChange={e => setJobTitle(e.target.value)}
        placeholder="Job Title"
        required
        style={{ width: "100%", padding: 8, borderRadius: 8, marginBottom: 18 }}
      />

      <label style={{ display: "block", marginBottom: 8 }}>Job Description:</label>
      <textarea
        value={jobDesc}
        onChange={e => setJobDesc(e.target.value)}
        placeholder="Enter job description (optional)"
        style={{ width: "100%", padding: 8, borderRadius: 8, marginBottom: 18, minHeight: 80 }}
      />

      <button type="submit" disabled={loading} style={{ width: "100%", padding: 12, borderRadius: 8, background: "#2a7cff", color: "#fff", border: "none", fontWeight: "bold", fontSize: 16 }}>
        {loading ? "Starting..." : "Start Pipeline"}
      </button>
      {message && (
        <div style={{ marginTop: 20, fontWeight: "bold", color: message.includes("✅") ? "green" : "red" }}>
          {message}
        </div>
      )}
    </form>
  );
};

export default RecruitmentForm;
