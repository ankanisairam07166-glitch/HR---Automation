// import React, { useState, useEffect } from 'react';
// import { Search, Filter, CheckCircle, XCircle, Clock, Calendar, FileText, Tag, Download, Plus, X, Mail, Eye, ExternalLink, GitBranch, Linkedin, Star, RefreshCw, Send ,Users} from 'lucide-react';
// import { useNavigate, useSearchParams } from 'react-router-dom';
// import Navigation from './Navigation';

// const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:5000";

// const CandidateScreening = () => {
//   const navigate = useNavigate();
//   const [searchParams] = useSearchParams();
//   const jobIdFromUrl = searchParams.get('job_id');
  
//   const [candidates, setCandidates] = useState([]);
//   const [jobs, setJobs] = useState([]);
//   const [selectedJob, setSelectedJob] = useState(null);
//   const [selectedCandidate, setSelectedCandidate] = useState(null);
//   const [loading, setLoading] = useState(false);
//   const [showNewPipelineModal, setShowNewPipelineModal] = useState(false);
//   const [pipelineRunning, setPipelineRunning] = useState(false);
//   const [message, setMessage] = useState('');
//   const [searchTerm, setSearchTerm] = useState('');
//   const [filterStatus, setFilterStatus] = useState('all');
//   const [sortBy, setSortBy] = useState('score_desc');
//   const [refreshing, setRefreshing] = useState(false);

//   // Initialize with job from URL if present
//   useEffect(() => {
//     fetchJobs().then(() => {
//       if (jobIdFromUrl && jobs.length > 0) {
//         const job = jobs.find(j => j.id === jobIdFromUrl);
//         if (job) setSelectedJob(job);
//       }
//     });
//   }, [jobIdFromUrl]);

//   useEffect(() => {
//     fetchJobs();
//   }, []);

//   useEffect(() => {
//     fetchCandidates();
//   }, [selectedJob]);

//   const fetchJobs = async () => {
//     try {
//       const response = await fetch(`${BACKEND_URL}/api/jobs`);
//       const data = await response.json();
      
//       if (Array.isArray(data)) {
//         setJobs(data);
//         return data;
//       } else {
//         setJobs([]);
//         return [];
//       }
//     } catch (error) {
//       console.error('Error fetching jobs:', error);
//       setJobs([]);
//       return [];
//     }
//   };

//   const fetchCandidates = async () => {
//     setLoading(true);
//     try {
//       let url = `${BACKEND_URL}/api/candidates`;
//       if (selectedJob) {
//         url += `?job_id=${selectedJob.id}`;
//       }
      
//       const response = await fetch(url);
//       const data = await response.json();
      
//       const transformedCandidates = data.map(candidate => ({
//         ...candidate,
//         displayStatus: getDisplayStatus(candidate),
//         displayScore: candidate.ats_score || 0,
//         scoreColor: getScoreColor(candidate.ats_score || 0),
//         statusInfo: getCandidateStatusInfo(candidate)
//       }));
      
//       setCandidates(transformedCandidates);
      
//       if (transformedCandidates.length > 0 && !selectedCandidate) {
//         setSelectedCandidate(transformedCandidates[0]);
//       }
//     } catch (error) {
//       console.error('Error fetching candidates:', error);
//       setCandidates([]);
//     } finally {
//       setLoading(false);
//     }
//   };

//   const refreshData = async () => {
//     setRefreshing(true);
//     await Promise.all([fetchJobs(), fetchCandidates()]);
//     setRefreshing(false);
//     setMessage('Data refreshed successfully!');
//     setTimeout(() => setMessage(''), 3000);
//   };

//   const getDisplayStatus = (candidate) => {
//     if (candidate.final_status === 'Hired') return 'Hired';
//     if (candidate.interview_scheduled) return 'Interview Scheduled';
//     if (candidate.exam_completed) {
//       return candidate.exam_percentage >= 70 ? 'Assessment Passed' : 'Assessment Failed';
//     }
//     if (candidate.exam_started) return 'Assessment In Progress';
//     if (candidate.exam_link_sent) {
//       return candidate.link_expired ? 'Assessment Expired' : 'Assessment Sent';
//     }
//     if (candidate.status === 'Shortlisted') return 'Shortlisted';
//     if (candidate.status === 'Rejected') return 'Rejected';
//     return 'Under Review';
//   };

//   const getCandidateStatusInfo = (candidate) => {
//     const status = getDisplayStatus(candidate);
//     const statusMap = {
//       'Hired': { color: 'bg-green-100 text-green-800', icon: CheckCircle, priority: 8 },
//       'Interview Scheduled': { color: 'bg-blue-100 text-blue-800', icon: Calendar, priority: 7 },
//       'Assessment Passed': { color: 'bg-green-100 text-green-800', icon: CheckCircle, priority: 6 },
//       'Assessment Failed': { color: 'bg-red-100 text-red-800', icon: XCircle, priority: 5 },
//       'Assessment In Progress': { color: 'bg-yellow-100 text-yellow-800', icon: Clock, priority: 4 },
//       'Assessment Sent': { color: 'bg-blue-100 text-blue-800', icon: Mail, priority: 3 },
//       'Assessment Expired': { color: 'bg-gray-100 text-gray-800', icon: Clock, priority: 2 },
//       'Shortlisted': { color: 'bg-green-100 text-green-800', icon: CheckCircle, priority: 2 },
//       'Rejected': { color: 'bg-red-100 text-red-800', icon: XCircle, priority: 1 },
//       'Under Review': { color: 'bg-gray-100 text-gray-800', icon: Clock, priority: 0 }
//     };
    
//     return statusMap[status] || statusMap['Under Review'];
//   };

//   const getScoreColor = (score) => {
//     if (score >= 85) return 'text-green-600';
//     if (score >= 70) return 'text-yellow-600';
//     return 'text-red-600';
//   };

//   const getFilteredAndSortedCandidates = () => {
//     let filtered = candidates;
    
//     // Apply search filter
//     if (searchTerm) {
//       filtered = filtered.filter(c => 
//         c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
//         c.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
//         c.job_title?.toLowerCase().includes(searchTerm.toLowerCase())
//       );
//     }
    
//     // Apply status filter
//     if (filterStatus !== 'all') {
//       filtered = filtered.filter(c => {
//         switch (filterStatus) {
//           case 'shortlisted':
//             return c.status === 'Shortlisted';
//           case 'assessment_pending':
//             return c.exam_link_sent && !c.exam_completed && !c.link_expired;
//           case 'assessment_completed':
//             return c.exam_completed;
//           case 'interview_scheduled':
//             return c.interview_scheduled;
//           case 'rejected':
//             return c.status === 'Rejected' || c.final_status === 'Rejected After Exam';
//           default:
//             return true;
//         }
//       });
//     }
    
//     // Apply sorting
//     return filtered.sort((a, b) => {
//       switch (sortBy) {
//         case 'score_desc':
//           return (b.ats_score || 0) - (a.ats_score || 0);
//         case 'score_asc':
//           return (a.ats_score || 0) - (b.ats_score || 0);
//         case 'date_desc':
//           return new Date(b.processed_date) - new Date(a.processed_date);
//         case 'date_asc':
//           return new Date(a.processed_date) - new Date(b.processed_date);
//         case 'name':
//           return a.name.localeCompare(b.name);
//         case 'status':
//           return b.statusInfo.priority - a.statusInfo.priority;
//         default:
//           return 0;
//       }
//     });
//   };

//   const sendAssessmentReminder = async (candidateId) => {
//     try {
//       const response = await fetch(`${BACKEND_URL}/api/send_reminder/${candidateId}`, {
//         method: 'POST'
//       });
      
//       if (response.ok) {
//         setMessage('Reminder sent successfully!');
//         setTimeout(() => setMessage(''), 3000);
//       }
//     } catch (error) {
//       console.error('Error sending reminder:', error);
//     }
//   };

//   const CandidateCard = ({ candidate, isSelected, onClick }) => {
//     const StatusIcon = candidate.statusInfo.icon;
//     const daysSinceProcessed = Math.floor((new Date() - new Date(candidate.processed_date)) / (1000 * 60 * 60 * 24));
    
//     return (
//       <div
//         className={`p-4 cursor-pointer transition-all border-l-4 ${
//           isSelected 
//             ? 'bg-blue-50 border-blue-500 shadow-md' 
//             : 'hover:bg-gray-50 border-transparent hover:border-gray-300'
//         }`}
//         onClick={onClick}
//       >
//         <div className="flex items-start justify-between">
//           <div className="flex items-start space-x-3 flex-1">
//             <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-medium flex-shrink-0">
//               {candidate.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
//             </div>
//             <div className="flex-1">
//               <h3 className="font-medium text-gray-900">{candidate.name}</h3>
//               <p className="text-sm text-gray-500">{candidate.email}</p>
//               <p className="text-xs text-gray-400 mt-1">{candidate.job_title} • Applied {daysSinceProcessed}d ago</p>
              
//               <div className="mt-2 flex items-center space-x-4 text-xs">
//                 {candidate.linkedin && (
//                   <a href={candidate.linkedin} target="_blank" rel="noopener noreferrer" 
//                      className="text-blue-600 hover:text-blue-700 flex items-center">
//                     <Linkedin className="w-3 h-3 mr-1" />
//                     LinkedIn
//                   </a>
//                 )}
//                 {candidate.github && (
//                   <a href={candidate.github} target="_blank" rel="noopener noreferrer"
//                      className="text-gray-600 hover:text-gray-700 flex items-center">
//                     <GitBranch className="w-3 h-3 mr-1" />
//                     GitHub
//                   </a>
//                 )}
//               </div>
//             </div>
//           </div>
          
//           <div className="flex flex-col items-end ml-4">
//             <div className="flex items-center space-x-1 mb-2">
//               <span className={`text-lg font-bold ${candidate.scoreColor}`}>
//                 {candidate.displayScore.toFixed(0)}
//               </span>
//               <span className="text-sm text-gray-500">/100</span>
//             </div>
            
//             <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${candidate.statusInfo.color}`}>
//               <StatusIcon className="w-3 h-3 mr-1" />
//               {candidate.displayStatus}
//             </span>
            
//             {candidate.exam_completed && (
//               <div className="mt-2 text-xs text-gray-500">
//                 Score: {candidate.exam_percentage?.toFixed(0)}%
//               </div>
//             )}
//           </div>
//         </div>
//       </div>
//     );
//   };

//   const CandidateDetails = ({ candidate }) => {
//     if (!candidate) {
//       return (
//         <div className="p-8 text-center text-gray-500">
//           <Eye className="w-12 h-12 mx-auto mb-3 text-gray-300" />
//           <p className="text-lg font-medium">Select a candidate to view details</p>
//         </div>
//       );
//     }

//     const timeline = getTimelineEvents(candidate);
//     const assessmentStats = getAssessmentStats(candidate);

//     return (
//       <div className="p-6">
//         {/* Header */}
//         <div className="flex items-start justify-between mb-6">
//           <div className="flex items-center space-x-4">
//             <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white text-xl font-medium">
//               {candidate.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
//             </div>
//             <div>
//               <h2 className="text-xl font-semibold text-gray-900">{candidate.name}</h2>
//               <p className="text-gray-500">{candidate.job_title}</p>
//               <div className="flex items-center space-x-3 mt-2">
//                 <a href={`mailto:${candidate.email}`} className="text-sm text-blue-600 hover:text-blue-700">
//                   {candidate.email}
//                 </a>
//                 {candidate.linkedin && (
//                   <a href={candidate.linkedin} target="_blank" rel="noopener noreferrer" 
//                      className="text-blue-600 hover:text-blue-700">
//                     <Linkedin className="w-4 h-4" />
//                   </a>
//                 )}
//                 {candidate.github && (
//                   <a href={candidate.github} target="_blank" rel="noopener noreferrer"
//                      className="text-gray-600 hover:text-gray-700">
//                     <GitBranch className="w-4 h-4" />
//                   </a>
//                 )}
//               </div>
//             </div>
//           </div>
          
//           <div className="text-center">
//             <div className="inline-flex items-center justify-center w-20 h-20 rounded-full border-4 border-blue-100 bg-white">
//               <div>
//                 <div className={`text-2xl font-bold ${candidate.scoreColor}`}>
//                   {candidate.displayScore.toFixed(0)}
//                 </div>
//                 <div className="text-xs text-gray-500">ATS Score</div>
//               </div>
//             </div>
//           </div>
//         </div>

//         {/* Status Badge */}
//         <div className="mb-6 p-4 bg-gray-50 rounded-lg">
//           <div className="flex items-center justify-between">
//             <div>
//               <p className="text-sm text-gray-600 mb-1">Current Status</p>
//               <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium ${candidate.statusInfo.color}`}>
//                 <candidate.statusInfo.icon className="w-4 h-4 mr-1.5" />
//                 {candidate.displayStatus}
//               </span>
//             </div>
//             <div className="text-right">
//               <p className="text-sm text-gray-600 mb-1">Applied</p>
//               <p className="font-medium">{new Date(candidate.processed_date).toLocaleDateString()}</p>
//             </div>
//           </div>
//         </div>

//         {/* Assessment Stats (if applicable) */}
//         {assessmentStats && (
//           <div className="mb-6 grid grid-cols-2 gap-4">
//             <div className="bg-blue-50 p-4 rounded-lg">
//               <p className="text-sm text-blue-600 mb-1">Assessment Score</p>
//               <p className="text-2xl font-bold text-blue-900">{assessmentStats.score}%</p>
//               <p className="text-xs text-blue-600 mt-1">
//                 {assessmentStats.correct}/{assessmentStats.total} correct
//               </p>
//             </div>
//             <div className="bg-purple-50 p-4 rounded-lg">
//               <p className="text-sm text-purple-600 mb-1">Time Taken</p>
//               <p className="text-2xl font-bold text-purple-900">{assessmentStats.timeTaken}m</p>
//               <p className="text-xs text-purple-600 mt-1">
//                 Completed {assessmentStats.completedDate}
//               </p>
//             </div>
//           </div>
//         )}

//         {/* Timeline */}
//         <div className="mb-6">
//           <h3 className="text-sm font-medium text-gray-700 mb-3">Recruitment Timeline</h3>
//           <div className="space-y-3">
//             {timeline.map((event, index) => (
//               <div key={index} className="flex items-start">
//                 <div className={`w-2 h-2 rounded-full mt-1.5 ${event.completed ? 'bg-green-500' : 'bg-gray-300'}`} />
//                 <div className="ml-3 flex-1">
//                   <p className="text-sm font-medium text-gray-900">{event.title}</p>
//                   <p className="text-xs text-gray-500">{event.date}</p>
//                 </div>
//               </div>
//             ))}
//           </div>
//         </div>

//         {/* ATS Score Reasoning */}
//         {candidate.score_reasoning && (
//           <div className="mb-6">
//             <h3 className="text-sm font-medium text-gray-700 mb-2">ATS Analysis</h3>
//             <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
//               {candidate.score_reasoning}
//             </p>
//           </div>
//         )}

//         {/* Actions */}
//         <div className="space-y-3">
//           {candidate.resume_path && (
//             <button className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
//               <Download className="w-4 h-4 mr-2" />
//               Download Resume
//             </button>
//           )}
          
//           {candidate.assessment_invite_link && (
//             <a 
//               href={candidate.assessment_invite_link} 
//               target="_blank" 
//               rel="noopener noreferrer"
//               className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
//             >
//               <ExternalLink className="w-4 h-4 mr-2" />
//               View Assessment
//             </a>
//           )}
          
//           {candidate.exam_link_sent && !candidate.exam_completed && !candidate.link_expired && (
//             <button 
//               onClick={() => sendAssessmentReminder(candidate.id)}
//               className="w-full flex items-center justify-center px-4 py-2 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50"
//             >
//               <Send className="w-4 h-4 mr-2" />
//               Send Reminder
//             </button>
//           )}
          
//           {candidate.exam_completed && candidate.exam_percentage >= 70 && !candidate.interview_scheduled && (
//             <button 
//               onClick={() => navigate(`/scheduler?candidate_id=${candidate.id}`)}
//               className="w-full flex items-center justify-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
//             >
//               <Calendar className="w-4 h-4 mr-2" />
//               Schedule Interview
//             </button>
//           )}
//         </div>
//       </div>
//     );
//   };

//   const getTimelineEvents = (candidate) => {
//     const events = [
//       {
//         title: 'Application Received',
//         date: new Date(candidate.processed_date).toLocaleDateString(),
//         completed: true
//       }
//     ];
    
//     if (candidate.status === 'Shortlisted') {
//       events.push({
//         title: 'Shortlisted',
//         date: new Date(candidate.processed_date).toLocaleDateString(),
//         completed: true
//       });
//     }
    
//     if (candidate.exam_link_sent) {
//       events.push({
//         title: 'Assessment Sent',
//         date: new Date(candidate.exam_link_sent_date).toLocaleDateString(),
//         completed: true
//       });
//     }
    
//     if (candidate.exam_completed) {
//       events.push({
//         title: `Assessment Completed (${candidate.exam_percentage?.toFixed(0)}%)`,
//         date: new Date(candidate.exam_completed_date).toLocaleDateString(),
//         completed: true
//       });
//     }
    
//     if (candidate.interview_scheduled) {
//       events.push({
//         title: 'Interview Scheduled',
//         date: new Date(candidate.interview_date).toLocaleDateString(),
//         completed: new Date(candidate.interview_date) < new Date()
//       });
//     }
    
//     if (candidate.final_status === 'Hired') {
//       events.push({
//         title: 'Hired',
//         date: new Date().toLocaleDateString(),
//         completed: true
//       });
//     }
    
//     return events;
//   };

//   const getAssessmentStats = (candidate) => {
//     if (!candidate.exam_completed) return null;
    
//     return {
//       score: candidate.exam_percentage?.toFixed(0) || 0,
//       correct: candidate.exam_correct_answers || candidate.exam_score || 0,
//       total: candidate.exam_total_questions || 0,
//       timeTaken: candidate.exam_time_taken || 0,
//       completedDate: candidate.exam_completed_date 
//         ? new Date(candidate.exam_completed_date).toLocaleDateString() 
//         : 'N/A'
//     };
//   };

//   const NewPipelineModal = () => {
//     const [jobId, setJobId] = useState('');
//     const [jobTitle, setJobTitle] = useState('');
//     const [jobDesc, setJobDesc] = useState('');

//     const handleStartPipeline = async () => {
//       if (!jobId || !jobTitle) {
//         alert("Please enter both Job ID and Job Title");
//         return;
//       }

//       setPipelineRunning(true);
      
//       try {
//         const response = await fetch(`${BACKEND_URL}/api/run_full_pipeline`, {
//           method: "POST",
//           headers: { 
//             "Content-Type": "application/json",
//             "Accept": "application/json"
//           },
//           body: JSON.stringify({
//             job_id: jobId,
//             job_title: jobTitle,
//             job_desc: jobDesc || ""
//           })
//         });

//         const data = await response.json();

//         if (!response.ok) {
//           throw new Error(data.message || `HTTP ${response.status}: ${response.statusText}`);
//         }

//         setMessage(data.message || "Pipeline started successfully!");
//         setShowNewPipelineModal(false);
        
//         // Refresh data after a delay
//         setTimeout(() => {
//           fetchJobs();
//           fetchCandidates();
//           setMessage('');
//         }, 3000);
        
//       } catch (err) {
//         console.error("Pipeline trigger failed:", err);
//         alert(`Failed to start pipeline: ${err.message}`);
//       } finally {
//         setPipelineRunning(false);
//       }
//     };

//     return (
//       <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
//         <div className="bg-white rounded-lg p-6 w-full max-w-md">
//           <div className="flex justify-between items-center mb-4">
//             <h2 className="text-xl font-bold">Start New Recruitment Pipeline</h2>
//             <button 
//               onClick={() => setShowNewPipelineModal(false)} 
//               className="text-gray-400 hover:text-gray-600"
//             >
//               <X className="w-5 h-5" />
//             </button>
//           </div>
//           <div className="space-y-4">
//             <div>
//               <label className="block text-sm font-medium text-gray-700 mb-1">Job ID</label>
//               <input
//                 type="text"
//                 placeholder="e.g., 12345"
//                 value={jobId}
//                 onChange={(e) => setJobId(e.target.value)}
//                 className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
//               />
//             </div>
//             <div>
//               <label className="block text-sm font-medium text-gray-700 mb-1">Job Title</label>
//               <input
//                 type="text"
//                 placeholder="e.g., Senior Software Engineer"
//                 value={jobTitle}
//                 onChange={(e) => setJobTitle(e.target.value)}
//                 className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
//               />
//             </div>
//             <div>
//               <label className="block text-sm font-medium text-gray-700 mb-1">Job Description (Optional)</label>
//               <textarea
//                 placeholder="Enter job description..."
//                 value={jobDesc}
//                 onChange={(e) => setJobDesc(e.target.value)}
//                 className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 h-32"
//               />
//             </div>
//             <button
//               onClick={handleStartPipeline}
//               disabled={!jobId || !jobTitle || pipelineRunning}
//               className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
//             >
//               {pipelineRunning ? 'Starting Pipeline...' : 'Start Pipeline'}
//             </button>
//           </div>
//         </div>
//       </div>
//     );
//   };

//   const filteredCandidates = getFilteredAndSortedCandidates();

//   return (
//     <div className="flex flex-col min-h-screen bg-gray-50">
//       <Navigation />
      
//       <main className="flex-grow p-6">
//         {/* Header */}
//         <div className="flex items-center justify-between mb-6">
//           <div>
//             <h1 className="text-2xl font-bold text-gray-900">Candidate Screening</h1>
//             {selectedJob && (
//               <p className="text-gray-600 mt-1">
//                 {selectedJob.title} • {selectedJob.location} • {filteredCandidates.length} candidates
//               </p>
//             )}
//           </div>
//           <div className="flex items-center space-x-3">
//             <button
//               onClick={refreshData}
//               className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50"
//               disabled={refreshing}
//             >
//               <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
//             </button>
//             <button
//               onClick={() => setShowNewPipelineModal(true)}
//               className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
//             >
//               <Plus className="w-4 h-4 mr-2" />
//               Run Pipeline
//             </button>
//           </div>
//         </div>

//         {/* Success Message */}
//         {message && (
//           <div className="mb-4 p-4 bg-green-100 text-green-700 rounded-lg flex items-center">
//             <CheckCircle className="w-5 h-5 mr-2" />
//             {message}
//           </div>
//         )}

//         {/* Filters */}
//         <div className="mb-6 flex flex-wrap items-center gap-4">
//           <select
//             value={selectedJob?.id || ''}
//             onChange={(e) => {
//               const job = jobs.find(j => j.id == e.target.value);
//               setSelectedJob(job || null);
//             }}
//             className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
//           >
//             <option value="">All Jobs</option>
//             {jobs.map(job => (
//               <option key={job.id} value={job.id}>
//                 {job.title} ({job.location})
//               </option>
//             ))}
//           </select>
          
//           <div className="relative flex-1 max-w-md">
//             <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
//             <input
//               type="text"
//               placeholder="Search candidates..."
//               value={searchTerm}
//               onChange={(e) => setSearchTerm(e.target.value)}
//               className="pl-10 pr-4 py-2 w-full border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
//             />
//           </div>
          
//           <select
//             value={filterStatus}
//             onChange={(e) => setFilterStatus(e.target.value)}
//             className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
//           >
//             <option value="all">All Status</option>
//             <option value="shortlisted">Shortlisted</option>
//             <option value="assessment_pending">Assessment Pending</option>
//             <option value="assessment_completed">Assessment Completed</option>
//             <option value="interview_scheduled">Interview Scheduled</option>
//             <option value="rejected">Rejected</option>
//           </select>
          
//           <select
//             value={sortBy}
//             onChange={(e) => setSortBy(e.target.value)}
//             className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
//           >
//             <option value="score_desc">Score (High to Low)</option>
//             <option value="score_asc">Score (Low to High)</option>
//             <option value="date_desc">Date (Newest First)</option>
//             <option value="date_asc">Date (Oldest First)</option>
//             <option value="name">Name (A-Z)</option>
//             <option value="status">Status Priority</option>
//           </select>
//         </div>

//         {/* Main Content */}
//         <div className="flex flex-col lg:flex-row gap-6">
//           {/* Candidate List */}
//           <div className="lg:w-1/2 bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
//             <div className="p-4 border-b border-gray-200 bg-gray-50">
//               <h2 className="font-medium text-gray-700">Candidates</h2>
//             </div>
//             <div className="divide-y divide-gray-200 max-h-[calc(100vh-300px)] overflow-y-auto">
//               {loading ? (
//                 <div className="p-8 text-center">
//                   <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
//                   <p className="mt-2 text-gray-500">Loading candidates...</p>
//                 </div>
//               ) : filteredCandidates.length === 0 ? (
//                 <div className="p-8 text-center text-gray-500">
//                   <Users className="w-12 h-12 mx-auto mb-3 text-gray-300" />
//                   <p className="text-lg font-medium">No candidates found</p>
//                   <p className="mt-1">Try adjusting your filters or run a new pipeline</p>
//                   <button
//                     onClick={() => setShowNewPipelineModal(true)}
//                     className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
//                   >
//                     Run New Pipeline
//                   </button>
//                 </div>
//               ) : (
//                 filteredCandidates.map((candidate) => (
//                   <CandidateCard
//                     key={candidate.id}
//                     candidate={candidate}
//                     isSelected={selectedCandidate?.id === candidate.id}
//                     onClick={() => setSelectedCandidate(candidate)}
//                   />
//                 ))
//               )}
//             </div>
//           </div>

//           {/* Candidate Details */}
//           <div className="lg:w-1/2 bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
//             <div className="p-4 border-b border-gray-200 bg-gray-50">
//               <h2 className="font-medium text-gray-700">Candidate Details</h2>
//             </div>
//             <CandidateDetails candidate={selectedCandidate} />
//           </div>
//         </div>
//       </main>
      
//       {/* New Pipeline Modal */}
//       {showNewPipelineModal && <NewPipelineModal />}
//     </div>
//   );
// };

// export default CandidateScreening;

import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { Search, Filter, CheckCircle, XCircle, Clock, Calendar, FileText, Tag, Download, Plus, X, Mail, Eye, ExternalLink, GitBranch, Linkedin, Star, RefreshCw, Send, Users, PlayCircle, AlertCircle } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import Navigation from './Navigation';

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
      const data = await response.json();
      
      if (Array.isArray(data)) {
        setJobs(data);
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

// Utility functions (memoized where possible)
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
            
            <div className="mt-2 flex items-center space-x-4 text-xs">
              {candidate.linkedin && (
                <a href={candidate.linkedin} target="_blank" rel="noopener noreferrer" 
                   className="text-blue-600 hover:text-blue-700 flex items-center"
                   onClick={(e) => e.stopPropagation()}>
                  <Linkedin className="w-3 h-3 mr-1" />
                  LinkedIn
                </a>
              )}
              {candidate.github && (
                <a href={candidate.github} target="_blank" rel="noopener noreferrer"
                   className="text-gray-600 hover:text-gray-700 flex items-center"
                   onClick={(e) => e.stopPropagation()}>
                  <GitBranch className="w-3 h-3 mr-1" />
                  GitHub
                </a>
              )}
            </div>
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
          
          {candidate.exam_completed && (
            <div className="mt-2 text-xs text-gray-500">
              Score: {candidate.exam_percentage?.toFixed(0)}%
            </div>
          )}
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
          <div className="h-3 bg-gray-200 rounded w-1/4"></div>
        </div>
        <div className="space-y-2">
          <div className="h-6 bg-gray-200 rounded w-12"></div>
          <div className="h-6 bg-gray-200 rounded w-20"></div>
        </div>
      </div>
    ))}
  </div>
);

// Error boundary component
const ErrorBoundary = ({ error, onRetry, children }) => {
  if (error) {
    return (
      <div className="p-8 text-center">
        <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-500" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Something went wrong</h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <button 
          onClick={onRetry}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Try Again
        </button>
      </div>
    );
  }
  return children;
};

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
  const [showNewPipelineModal, setShowNewPipelineModal] = useState(false);
  const [pipelineRunning, setPipelineRunning] = useState(false);

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

  // Pipeline completion handler
  useEffect(() => {
    if (currentStatus?.status === 'completed' && 
        pipelineStatus[selectedJob?.id]?.status !== 'completed') {
      setTimeout(() => {
        refetchCandidates();
        setMessage('Pipeline completed! Candidates updated.');
        setTimeout(() => setMessage(''), 3000);
      }, 1000);
    }
  }, [currentStatus, pipelineStatus, selectedJob?.id, refetchCandidates]);

  // Event handlers
  const refreshData = async () => {
    setRefreshing(true);
    await Promise.all([refetchJobs(), refetchCandidates()]);
    setRefreshing(false);
    setMessage('Data refreshed successfully!');
    setTimeout(() => setMessage(''), 3000);
  };

  const handleQuickPipeline = async (job) => {
    updatePipelineStatus(job.id, { status: 'starting', message: 'Starting pipeline...', progress: 0 });

    try {
      const response = await fetch(`${BACKEND_URL}/api/run_full_pipeline`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: job.id,
          job_title: job.title,
          job_desc: job.description || ''
        })
      });
      
      const data = await response.json();
      if (response.ok && data.success) {
        updatePipelineStatus(job.id, { 
          status: 'running', 
          message: 'Pipeline running...', 
          progress: 10,
          estimated_time: data.estimated_time 
        });
        
        setMessage(`Pipeline started for ${job.title}! Check back in 5-10 minutes.`);
        setTimeout(() => setMessage(''), 5000);
        
      } else {
        updatePipelineStatus(job.id, { status: 'error', message: data.message || 'Failed to start pipeline' });
        setMessage(`Failed to start pipeline: ${data.message}`);
        setTimeout(() => setMessage(''), 5000);
      }
    } catch (error) {
      updatePipelineStatus(job.id, { status: 'error', message: 'Network error' });
      setMessage('Network error while starting pipeline');
      setTimeout(() => setMessage(''), 5000);
    }
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
                {candidate.linkedin && (
                  <a href={candidate.linkedin} target="_blank" rel="noopener noreferrer" 
                     className="text-blue-600 hover:text-blue-700">
                    <Linkedin className="w-4 h-4" />
                  </a>
                )}
                {candidate.github && (
                  <a href={candidate.github} target="_blank" rel="noopener noreferrer"
                     className="text-gray-600 hover:text-gray-700">
                    <GitBranch className="w-4 h-4" />
                  </a>
                )}
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

        {/* Assessment Stats */}
        {assessmentStats && (
          <div className="mb-6 grid grid-cols-2 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-blue-600 mb-1">Assessment Score</p>
              <p className="text-2xl font-bold text-blue-900">{assessmentStats.score}%</p>
              <p className="text-xs text-blue-600 mt-1">
                {assessmentStats.correct}/{assessmentStats.total} correct
              </p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <p className="text-sm text-purple-600 mb-1">Time Taken</p>
              <p className="text-2xl font-bold text-purple-900">{assessmentStats.timeTaken}m</p>
              <p className="text-xs text-purple-600 mt-1">
                Completed {assessmentStats.completedDate}
              </p>
            </div>
          </div>
        )}

        {/* Timeline */}
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Recruitment Timeline</h3>
          <div className="space-y-3">
            {timeline.map((event, index) => (
              <div key={index} className="flex items-start">
                <div className={`w-2 h-2 rounded-full mt-1.5 ${event.completed ? 'bg-green-500' : 'bg-gray-300'}`} />
                <div className="ml-3 flex-1">
                  <p className="text-sm font-medium text-gray-900">{event.title}</p>
                  <p className="text-xs text-gray-500">{event.date}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ATS Score Reasoning */}
        {candidate.score_reasoning && (
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-700 mb-2">ATS Analysis</h3>
            <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
              {candidate.score_reasoning}
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="space-y-3">
          {candidate.resume_path && (
            <button className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
              <Download className="w-4 h-4 mr-2" />
              Download Resume
            </button>
          )}
          
          {candidate.assessment_invite_link && (
            <a 
              href={candidate.assessment_invite_link} 
              target="_blank" 
              rel="noopener noreferrer"
              className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              View Assessment
            </a>
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
    
    if (candidate.exam_link_sent) {
      events.push({
        title: 'Assessment Sent',
        date: new Date(candidate.exam_link_sent_date).toLocaleDateString(),
        completed: true
      });
    }
    
    if (candidate.exam_completed) {
      events.push({
        title: `Assessment Completed (${candidate.exam_percentage?.toFixed(0)}%)`,
        date: new Date(candidate.exam_completed_date).toLocaleDateString(),
        completed: true
      });
    }
    
    if (candidate.interview_scheduled) {
      events.push({
        title: 'Interview Scheduled',
        date: new Date(candidate.interview_date).toLocaleDateString(),
        completed: new Date(candidate.interview_date) < new Date()
      });
    }
    
    if (candidate.final_status === 'Hired') {
      events.push({
        title: 'Hired',
        date: new Date().toLocaleDateString(),
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

  const NewPipelineModal = () => {
    const [jobId, setJobId] = useState('');
    const [jobTitle, setJobTitle] = useState('');
    const [jobDesc, setJobDesc] = useState('');

    const handleStartPipeline = async () => {
      if (!jobId || !jobTitle) {
        alert("Please enter both Job ID and Job Title");
        return;
      }

      setPipelineRunning(true);
      
      try {
        const response = await fetch(`${BACKEND_URL}/api/run_full_pipeline`, {
          method: "POST",
          headers: { 
            "Content-Type": "application/json",
            "Accept": "application/json"
          },
          body: JSON.stringify({
            job_id: jobId,
            job_title: jobTitle,
            job_desc: jobDesc || ""
          })
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.message || `HTTP ${response.status}: ${response.statusText}`);
        }

        setMessage(data.message || "Pipeline started successfully!");
        setShowNewPipelineModal(false);
        
        updatePipelineStatus(jobId, { status: 'running', message: 'Pipeline started', progress: 10 });
        
        setTimeout(() => {
          refetchJobs();
          refetchCandidates();
          setMessage('');
        }, 3000);
        
      } catch (err) {
        console.error("Pipeline trigger failed:", err);
        alert(`Failed to start pipeline: ${err.message}`);
      } finally {
        setPipelineRunning(false);
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Start New Recruitment Pipeline</h2>
            <button 
              onClick={() => setShowNewPipelineModal(false)} 
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Job ID</label>
              <input
                type="text"
                placeholder="e.g., 12345"
                value={jobId}
                onChange={(e) => setJobId(e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Job Title</label>
              <input
                type="text"
                placeholder="e.g., Senior Software Engineer"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Job Description (Optional)</label>
              <textarea
                placeholder="Enter job description..."
                value={jobDesc}
                onChange={(e) => setJobDesc(e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 h-32"
              />
            </div>
            <button
              onClick={handleStartPipeline}
              disabled={!jobId || !jobTitle || pipelineRunning}
              className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {pipelineRunning ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Starting Pipeline...
                </>
              ) : (
                <>
                  <PlayCircle className="w-4 h-4 mr-2" />
                  Start Pipeline
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    );
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
                onClick={() => handleQuickPipeline(selectedJob)}
                disabled={currentStatus?.status === 'running'}
                className={`flex items-center px-4 py-2 rounded-lg ${
                  currentStatus?.status === 'running'
                    ? 'bg-yellow-100 text-yellow-800 cursor-not-allowed'
                    : 'bg-green-600 text-white hover:bg-green-700'
                }`}
              >
                {currentStatus?.status === 'running' ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-600 mr-2"></div>
                    Pipeline Running
                  </>
                ) : (
                  <>
                    <PlayCircle className="w-4 h-4 mr-2" />
                    Run Pipeline
                  </>
                )}
              </button>
            )}
            <button
              onClick={() => setShowNewPipelineModal(true)}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Pipeline
            </button>
          </div>
        </div>

        {/* Pipeline Status Alert */}
        {currentStatus && (
          <div className={`mb-6 p-4 rounded-lg border flex items-center justify-between ${
            currentStatus.status === 'running' ? 'bg-yellow-50 border-yellow-200' :
            currentStatus.status === 'completed' ? 'bg-green-50 border-green-200' :
            currentStatus.status === 'error' ? 'bg-red-50 border-red-200' :
            'bg-blue-50 border-blue-200'
          }`}>
            <div className="flex items-center">
              {currentStatus.status === 'running' && (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-yellow-600 mr-3"></div>
              )}
              {currentStatus.status === 'completed' && <CheckCircle className="w-5 h-5 mr-3 text-green-600" />}
              {currentStatus.status === 'error' && <XCircle className="w-5 h-5 mr-3 text-red-600" />}
              <div>
                <span className={
                  currentStatus.status === 'running' ? 'text-yellow-800' :
                  currentStatus.status === 'completed' ? 'text-green-800' :
                  currentStatus.status === 'error' ? 'text-red-800' :
                  'text-blue-800'
                }>
                  {currentStatus.message}
                </span>
                {currentStatus.estimated_time && currentStatus.status === 'running' && (
                  <span className="text-sm ml-2">({currentStatus.estimated_time})</span>
                )}
                {currentStatus.progress !== undefined && (
                  <div className="mt-1 w-32 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                      style={{ width: `${currentStatus.progress}%` }}
                    ></div>
                  </div>
                )}
              </div>
            </div>
            {currentStatus.status === 'completed' && (
              <button
                onClick={refreshData}
                className="px-3 py-1 rounded text-sm font-medium bg-green-600 text-white hover:bg-green-700"
              >
                Refresh Data
              </button>
            )}
          </div>
        )}

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
              <ErrorBoundary error={error} onRetry={refetchCandidates}>
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
                        onClick={() => setShowNewPipelineModal(true)}
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
              </ErrorBoundary>
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
      
      {/* New Pipeline Modal */}
      {showNewPipelineModal && <NewPipelineModal />}
    </div>
  );
};

export default CandidateScreening;