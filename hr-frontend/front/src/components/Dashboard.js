// // import React, { useState, useEffect } from 'react';
// // import { Search, Filter, Calendar, Users, Clock, Award, Bell, ChevronDown, Plus, X, TrendingUp, AlertCircle, CheckCircle, XCircle, BarChart3, Target } from 'lucide-react';
// // import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, Legend } from 'recharts';
// // import { useNavigate } from 'react-router-dom';
// // import Navigation from './Navigation';

// // const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000/api';

// // const Dashboard = () => {
// //   const navigate = useNavigate();
// //   const [loading, setLoading] = useState(true);
// //   const [candidates, setCandidates] = useState([]);
// //   const [jobs, setJobs] = useState([]);
// //   const [stats, setStats] = useState({
// //     totalApplications: 0,
// //     activeInterviews: 0,
// //     timeToHire: 0,
// //     activeAssessments: 0,
// //     shortlistRate: 0,
// //     assessmentCompletionRate: 0,
// //     totalHires: 0,
// //     pendingActions: 0
// //   });
// //   const [recruitmentData, setRecruitmentData] = useState([]);
// //   const [showNewPipelineModal, setShowNewPipelineModal] = useState(false);
// //   const [selectedTimeRange, setSelectedTimeRange] = useState('month');
// //   const [notifications, setNotifications] = useState([]);

// //   useEffect(() => {
// //     fetchDashboardData();
// //     // Refresh data every 30 seconds
// //     const interval = setInterval(fetchDashboardData, 30000);
// //     return () => clearInterval(interval);
// //   }, [selectedTimeRange]);

// //   const fetchDashboardData = async () => {
// //     setLoading(true);
// //     try {
// //       const [jobsRes, candidatesRes, statsRes] = await Promise.all([
// //         fetch(`${API_BASE_URL}/jobs`),
// //         fetch(`${API_BASE_URL}/candidates`),
// //         fetch(`${API_BASE_URL}/recruitment-stats`)
// //       ]);

// //       if (!jobsRes.ok || !candidatesRes.ok || !statsRes.ok) {
// //         throw new Error('Failed to fetch one or more resources');
// //       }

// //       const jobsData = await jobsRes.json();
// //       const candidatesData = await candidatesRes.json();
// //       const statsData = await statsRes.json();

// //       setJobs(Array.isArray(jobsData) ? jobsData : []);
// //       setCandidates(Array.isArray(candidatesData) ? candidatesData : []);
// //       setRecruitmentData(Array.isArray(statsData) ? statsData : []);

// //       // Calculate real-time stats
// //       calculateStats(Array.isArray(candidatesData) ? candidatesData : []);
// //       // Generate notifications
// //       generateNotifications(Array.isArray(candidatesData) ? candidatesData : []);
// //     } catch (error) {
// //       console.error('Error fetching dashboard data:', error);
// //       setJobs([]);
// //       setCandidates([]);
// //       setRecruitmentData([]);
// //     } finally {
// //       setLoading(false);
// //     }
// //   };

// //   const calculateStats = (candidatesData) => {
// //     const total = candidatesData.length;
// //     const shortlisted = candidatesData.filter(c => c.status === 'Shortlisted').length;
// //     const interviews = candidatesData.filter(c => c.interview_scheduled).length;
// //     const assessmentsSent = candidatesData.filter(c => c.exam_link_sent).length;
// //     const assessmentsCompleted = candidatesData.filter(c => c.exam_completed).length;
// //     const hires = candidatesData.filter(c => c.final_status === 'Hired').length;
// //     const pendingAssessments = candidatesData.filter(c => c.exam_link_sent && !c.exam_completed && !c.link_expired).length;
// //     const pendingInterviews = candidatesData.filter(c => c.interview_scheduled && new Date(c.interview_date) > new Date()).length;

// //     setStats({
// //       totalApplications: total,
// //       activeInterviews: interviews,
// //       timeToHire: calculateAverageTimeToHire(candidatesData),
// //       activeAssessments: pendingAssessments,
// //       shortlistRate: total > 0 ? ((shortlisted / total) * 100).toFixed(1) : 0,
// //       assessmentCompletionRate: assessmentsSent > 0 ? ((assessmentsCompleted / assessmentsSent) * 100).toFixed(1) : 0,
// //       totalHires: hires,
// //       pendingActions: pendingAssessments + pendingInterviews
// //     });
// //   };

// //   const calculateAverageTimeToHire = (candidates) => {
// //     const hiredCandidates = candidates.filter(c => c.final_status === 'Hired' && c.processed_date);
// //     if (hiredCandidates.length === 0) return 0;
    
// //     const totalDays = hiredCandidates.reduce((acc, c) => {
// //       const processedDate = new Date(c.processed_date);
// //       const hireDate = new Date(); // Should be actual hire date
// //       const days = Math.floor((hireDate - processedDate) / (1000 * 60 * 60 * 24));
// //       return acc + days;
// //     }, 0);
    
// //     return Math.round(totalDays / hiredCandidates.length);
// //   };

// //   const generateNotifications = (candidatesData) => {
// //     const notifications = [];
    
// //     // Pending assessments
// //     const pendingAssessments = candidatesData.filter(c => 
// //       c.exam_link_sent && !c.exam_completed && !c.link_expired
// //     );
// //     if (pendingAssessments.length > 0) {
// //       notifications.push({
// //         id: 1,
// //         type: 'warning',
// //         message: `${pendingAssessments.length} candidates have pending assessments`,
// //         action: 'View Assessments',
// //         route: '/assessments'
// //       });
// //     }

// //     // Upcoming interviews
// //     const upcomingInterviews = candidatesData.filter(c => {
// //       if (!c.interview_date) return false;
// //       const interviewDate = new Date(c.interview_date);
// //       const now = new Date();
// //       const hoursDiff = (interviewDate - now) / (1000 * 60 * 60);
// //       return hoursDiff > 0 && hoursDiff < 24;
// //     });
    
// //     if (upcomingInterviews.length > 0) {
// //       notifications.push({
// //         id: 2,
// //         type: 'info',
// //         message: `${upcomingInterviews.length} interviews scheduled for today`,
// //         action: 'View Schedule',
// //         route: '/scheduler'
// //       });
// //     }

// //     setNotifications(notifications);
// //   };

// //   const StatCard = ({ title, value, change, icon: Icon, color, subtitle }) => (
// //     <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
// //       <div className="flex items-center justify-between mb-4">
// //         <h3 className="text-gray-500 text-sm font-medium">{title}</h3>
// //         <div className={`p-2 rounded-lg ${color}`}>
// //           <Icon className="w-5 h-5 text-white" />
// //         </div>
// //       </div>
// //       <div className="flex items-baseline">
// //         <p className="text-3xl font-bold text-gray-900">{value}</p>
// //         {change !== undefined && (
// //           <span className={`ml-2 text-sm font-medium flex items-center ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
// //             {change >= 0 ? <TrendingUp className="w-4 h-4 mr-1" /> : null}
// //             {change >= 0 ? '+' : ''}{change}%
// //           </span>
// //         )}
// //       </div>
// //       {subtitle && <p className="text-gray-500 text-xs mt-1">{subtitle}</p>}
// //     </div>
// //   );

// //   const NewPipelineModal = () => {
// //     const [jobId, setJobId] = useState('');
// //     const [selectedJob, setSelectedJob] = useState(null);
// //     const [jobDesc, setJobDesc] = useState('');
// //     const [isSubmitting, setIsSubmitting] = useState(false);

// //     const handleJobSelect = (e) => {
// //       const job = jobs.find(j => j.id === e.target.value);
// //       setSelectedJob(job);
// //       setJobId(job?.id || '');
// //       setJobDesc(job?.description || '');
// //     };

// //     const handleSubmit = async () => {
// //       if (!selectedJob) return;
      
// //       setIsSubmitting(true);
// //       try {
// //         const response = await fetch(`${API_BASE_URL}/run_full_pipeline`, {
// //           method: 'POST',
// //           headers: { 'Content-Type': 'application/json' },
// //           body: JSON.stringify({
// //             job_id: selectedJob.id,
// //             job_title: selectedJob.title,
// //             job_desc: jobDesc
// //           })
// //         });
        
// //         const data = await response.json();
// //         if (data.success) {
// //           alert(data.message || 'Pipeline started successfully!');
// //           setShowNewPipelineModal(false);
// //           setTimeout(fetchDashboardData, 2000);
// //         } else {
// //           alert(data.message || 'Failed to start pipeline');
// //         }
// //       } catch (error) {
// //         alert('Error starting pipeline: ' + error.message);
// //       } finally {
// //         setIsSubmitting(false);
// //       }
// //     };

// //     return (
// //       <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
// //         <div className="bg-white rounded-lg p-6 w-full max-w-md">
// //           <div className="flex justify-between items-center mb-4">
// //             <h2 className="text-xl font-bold">Start Recruitment Pipeline</h2>
// //             <button onClick={() => setShowNewPipelineModal(false)} className="text-gray-400 hover:text-gray-600">
// //               <X className="w-5 h-5" />
// //             </button>
// //           </div>
          
// //           <div className="space-y-4">
// //             <div>
// //               <label className="block text-sm font-medium text-gray-700 mb-1">Select Job Position</label>
// //               <select
// //                 onChange={handleJobSelect}
// //                 className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
// //               >
// //                 <option value="">Select a job...</option>
// //                 {jobs.map(job => (
// //                   <option key={job.id} value={job.id}>
// //                     {job.title} - {job.location} ({job.applications || 0} applications)
// //                   </option>
// //                 ))}
// //               </select>
// //             </div>
            
// //             {selectedJob && (
// //               <div className="bg-blue-50 p-4 rounded-lg">
// //                 <h4 className="font-medium text-blue-900 mb-1">{selectedJob.title}</h4>
// //                 <p className="text-sm text-blue-700">{selectedJob.department} • {selectedJob.location}</p>
// //               </div>
// //             )}
            
// //             <div>
// //               <label className="block text-sm font-medium text-gray-700 mb-1">Job Description</label>
// //               <textarea
// //                 value={jobDesc}
// //                 onChange={(e) => setJobDesc(e.target.value)}
// //                 className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 h-32"
// //                 placeholder="Enter or modify job description..."
// //               />
// //             </div>
            
// //             <button
// //               onClick={handleSubmit}
// //               disabled={!selectedJob || isSubmitting}
// //               className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
// //             >
// //               {isSubmitting ? 'Starting Pipeline...' : 'Start Pipeline'}
// //             </button>
            
// //             <p className="text-xs text-gray-500 text-center">
// //               This will scrape resumes, create assessments, and start the AI screening process
// //             </p>
// //           </div>
// //         </div>
// //       </div>
// //     );
// //   };

// //   const getPipelineStages = () => {
// //     const stages = [
// //       { name: 'Applied', value: candidates.length, color: '#3B82F6' },
// //       { name: 'Screened', value: candidates.filter(c => c.ats_score > 0).length, color: '#10B981' },
// //       { name: 'Shortlisted', value: candidates.filter(c => c.status === 'Shortlisted').length, color: '#F59E0B' },
// //       { name: 'Assessment', value: candidates.filter(c => c.exam_completed).length, color: '#8B5CF6' },
// //       { name: 'Interview', value: candidates.filter(c => c.interview_scheduled).length, color: '#EF4444' },
// //       { name: 'Hired', value: candidates.filter(c => c.final_status === 'Hired').length, color: '#059669' }
// //     ];
    
// //     return stages;
// //   };

// //   const getAssessmentMetrics = () => {
// //     const sent = candidates.filter(c => c.exam_link_sent).length;
// //     const started = candidates.filter(c => c.exam_started).length;
// //     const completed = candidates.filter(c => c.exam_completed).length;
// //     const passed = candidates.filter(c => c.exam_percentage >= 70).length;
    
// //     return [
// //       { name: 'Sent', value: sent },
// //       { name: 'Started', value: started },
// //       { name: 'Completed', value: completed },
// //       { name: 'Passed', value: passed }
// //     ];
// //   };

// //   if (loading) {
// //     return (
// //       <div className="min-h-screen bg-gray-50 flex items-center justify-center">
// //         <div className="text-center">
// //           <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
// //           <p className="mt-4 text-gray-600">Loading dashboard...</p>
// //         </div>
// //       </div>
// //     );
// //   }

// //   return (
// //     <div className="min-h-screen bg-gray-50">
// //       <Navigation />

// //       <main className="p-6">
// //         {/* Header */}
// //         <div className="flex items-center justify-between mb-6">
// //           <div>
// //             <h1 className="text-2xl font-bold text-gray-900">Recruitment Dashboard</h1>
// //             <p className="text-gray-600 mt-1">Welcome back! Here's your recruitment overview</p>
// //           </div>
// //           <div className="flex items-center space-x-3">
// //             <select
// //               value={selectedTimeRange}
// //               onChange={(e) => setSelectedTimeRange(e.target.value)}
// //               className="border rounded-lg px-4 py-2 text-sm"
// //             >
// //               <option value="week">This Week</option>
// //               <option value="month">This Month</option>
// //               <option value="quarter">This Quarter</option>
// //               <option value="year">This Year</option>
// //             </select>
// //             <button
// //               onClick={() => setShowNewPipelineModal(true)}
// //               className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2"
// //             >
// //               <Plus className="w-4 h-4" />
// //               <span>New Pipeline</span>
// //             </button>
// //           </div>
// //         </div>

// //         {/* Notifications */}
// //         {notifications.length > 0 && (
// //           <div className="mb-6 space-y-2">
// //             {notifications.map(notification => (
// //               <div
// //                 key={notification.id}
// //                 className={`p-4 rounded-lg border flex items-center justify-between ${
// //                   notification.type === 'warning' 
// //                     ? 'bg-yellow-50 border-yellow-200' 
// //                     : 'bg-blue-50 border-blue-200'
// //                 }`}
// //               >
// //                 <div className="flex items-center">
// //                   <AlertCircle className={`w-5 h-5 mr-3 ${
// //                     notification.type === 'warning' ? 'text-yellow-600' : 'text-blue-600'
// //                   }`} />
// //                   <span className={notification.type === 'warning' ? 'text-yellow-800' : 'text-blue-800'}>
// //                     {notification.message}
// //                   </span>
// //                 </div>
// //                 <button
// //                   onClick={() => navigate(notification.route)}
// //                   className={`px-3 py-1 rounded text-sm font-medium ${
// //                     notification.type === 'warning'
// //                       ? 'bg-yellow-600 text-white hover:bg-yellow-700'
// //                       : 'bg-blue-600 text-white hover:bg-blue-700'
// //                   }`}
// //                 >
// //                   {notification.action}
// //                 </button>
// //               </div>
// //             ))}
// //           </div>
// //         )}

// //         {/* Stats Grid */}
// //         <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
// //           <StatCard
// //             title="Total Applications"
// //             value={stats.totalApplications}
// //             change={12.5}
// //             icon={Users}
// //             color="bg-blue-600"
// //             subtitle="All time applications"
// //           />
// //           <StatCard
// //             title="Shortlist Rate"
// //             value={`${stats.shortlistRate}%`}
// //             change={5.2}
// //             icon={Target}
// //             color="bg-green-600"
// //             subtitle="Candidates shortlisted"
// //           />
// //           <StatCard
// //             title="Time-to-Hire"
// //             value={`${stats.timeToHire}d`}
// //             change={-8.3}
// //             icon={Clock}
// //             color="bg-yellow-600"
// //             subtitle="Average days to hire"
// //           />
// //           <StatCard
// //             title="Pending Actions"
// //             value={stats.pendingActions}
// //             icon={Bell}
// //             color="bg-purple-600"
// //             subtitle="Requires attention"
// //           />
// //         </div>

// //         {/* Charts Row */}
// //         <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
// //           {/* Pipeline Funnel */}
// //           <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
// //             <h3 className="text-lg font-semibold mb-4">Recruitment Pipeline</h3>
// //             <ResponsiveContainer width="100%" height={300}>
// //               <BarChart data={getPipelineStages()} layout="horizontal">
// //                 <CartesianGrid strokeDasharray="3 3" />
// //                 <XAxis dataKey="name" />
// //                 <YAxis />
// //                 <Tooltip />
// //                 <Bar dataKey="value" fill="#3B82F6">
// //                   {getPipelineStages().map((entry, index) => (
// //                     <Cell key={`cell-${index}`} fill={entry.color} />
// //                   ))}
// //                 </Bar>
// //               </BarChart>
// //             </ResponsiveContainer>
// //           </div>

// //           {/* Activity Trend */}
// //           <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
// //             <h3 className="text-lg font-semibold mb-4">Recruitment Activity</h3>
// //             <ResponsiveContainer width="100%" height={300}>
// //               <LineChart data={recruitmentData}>
// //                 <CartesianGrid strokeDasharray="3 3" />
// //                 <XAxis dataKey="month" />
// //                 <YAxis />
// //                 <Tooltip />
// //                 <Legend />
// //                 <Line type="monotone" dataKey="applications" stroke="#3B82F6" strokeWidth={2} name="Applications" />
// //                 <Line type="monotone" dataKey="interviews" stroke="#10B981" strokeWidth={2} name="Interviews" />
// //                 <Line type="monotone" dataKey="hires" stroke="#EF4444" strokeWidth={2} name="Hires" />
// //               </LineChart>
// //             </ResponsiveContainer>
// //           </div>
// //         </div>

// //         {/* Active Jobs Table */}
// //         <div className="bg-white rounded-lg shadow-sm border border-gray-100 mb-8">
// //           <div className="p-6 border-b border-gray-200">
// //             <div className="flex items-center justify-between">
// //               <h3 className="text-lg font-semibold">Active Job Positions</h3>
// //               <button
// //                 onClick={() => navigate('/candidates')}
// //                 className="text-blue-600 hover:text-blue-700 text-sm font-medium"
// //               >
// //                 View All Candidates →
// //               </button>
// //             </div>
// //           </div>
// //           <div className="overflow-x-auto">
// //             <table className="w-full">
// //               <thead>
// //                 <tr className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
// //                   <th className="px-6 py-3">Position</th>
// //                   <th className="px-6 py-3">Department</th>
// //                   <th className="px-6 py-3">Location</th>
// //                   <th className="px-6 py-3">Applications</th>
// //                   <th className="px-6 py-3">Shortlisted</th>
// //                   <th className="px-6 py-3">In Progress</th>
// //                   <th className="px-6 py-3">Status</th>
// //                   <th className="px-6 py-3">Actions</th>
// //                 </tr>
// //               </thead>
// //               <tbody className="divide-y divide-gray-200">
// //                 {jobs.map((job) => {
// //                   const jobCandidates = candidates.filter(c => c.job_id === job.id);
// //                   const shortlisted = jobCandidates.filter(c => c.status === 'Shortlisted').length;
// //                   const inProgress = jobCandidates.filter(c => c.exam_link_sent || c.interview_scheduled).length;
                  
// //                   return (
// //                     <tr key={job.id} className="hover:bg-gray-50">
// //                       <td className="px-6 py-4">
// //                         <div className="text-sm font-medium text-gray-900">{job.title}</div>
// //                       </td>
// //                       <td className="px-6 py-4 text-sm text-gray-500">{job.department}</td>
// //                       <td className="px-6 py-4 text-sm text-gray-500">{job.location}</td>
// //                       <td className="px-6 py-4">
// //                         <div className="flex items-center">
// //                           <span className="text-sm font-medium text-gray-900">{jobCandidates.length}</span>
// //                         </div>
// //                       </td>
// //                       <td className="px-6 py-4">
// //                         <div className="flex items-center">
// //                           <span className="text-sm font-medium text-green-600">{shortlisted}</span>
// //                         </div>
// //                       </td>
// //                       <td className="px-6 py-4">
// //                         <div className="flex items-center">
// //                           <span className="text-sm font-medium text-blue-600">{inProgress}</span>
// //                         </div>
// //                       </td>
// //                       <td className="px-6 py-4">
// //                         <span className="inline-flex px-2 py-1 text-xs font-semibold leading-5 text-green-800 bg-green-100 rounded-full">
// //                           Active
// //                         </span>
// //                       </td>
// //                       <td className="px-6 py-4 text-sm">
// //                         <div className="flex space-x-2">
// //                           <button
// //                             onClick={() => navigate(`/candidates?job_id=${job.id}`)}
// //                             className="text-blue-600 hover:text-blue-900"
// //                           >
// //                             View
// //                           </button>
// //                           <button
// //                             onClick={() => {
// //                               setShowNewPipelineModal(true);
// //                             }}
// //                             className="text-green-600 hover:text-green-900"
// //                           >
// //                             Run Pipeline
// //                           </button>
// //                         </div>
// //                       </td>
// //                     </tr>
// //                   );
// //                 })}
// //               </tbody>
// //             </table>
// //           </div>
// //         </div>

// //         {/* Assessment Metrics */}
// //         <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
// //           {/* Assessment Completion */}
// //           <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
// //             <h3 className="text-lg font-semibold mb-4">Assessment Metrics</h3>
// //             <ResponsiveContainer width="100%" height={200}>
// //               <BarChart data={getAssessmentMetrics()}>
// //                 <CartesianGrid strokeDasharray="3 3" />
// //                 <XAxis dataKey="name" />
// //                 <YAxis />
// //                 <Tooltip />
// //                 <Bar dataKey="value" fill="#8B5CF6" />
// //               </BarChart>
// //             </ResponsiveContainer>
// //             <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
// //               <div>
// //                 <p className="text-gray-500">Completion Rate</p>
// //                 <p className="text-xl font-semibold">{stats.assessmentCompletionRate}%</p>
// //               </div>
// //               <div>
// //                 <p className="text-gray-500">Pass Rate</p>
// //                 <p className="text-xl font-semibold">
// //                   {candidates.filter(c => c.exam_completed).length > 0
// //                     ? ((candidates.filter(c => c.exam_percentage >= 70).length / candidates.filter(c => c.exam_completed).length) * 100).toFixed(1)
// //                     : 0}%
// //                 </p>
// //               </div>
// //             </div>
// //           </div>

// //           {/* Quick Actions */}
// //           <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
// //             <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
// //             <div className="space-y-3">
// //               <button
// //                 onClick={() => navigate('/assessments')}
// //                 className="w-full p-4 border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center justify-between"
// //               >
// //                 <div className="flex items-center">
// //                   <Award className="w-5 h-5 text-purple-600 mr-3" />
// //                   <span className="font-medium">Manage Assessments</span>
// //                 </div>
// //                 <span className="text-sm text-gray-500">{stats.activeAssessments} pending</span>
// //               </button>
              
// //               <button
// //                 onClick={() => navigate('/scheduler')}
// //                 className="w-full p-4 border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center justify-between"
// //               >
// //                 <div className="flex items-center">
// //                   <Calendar className="w-5 h-5 text-blue-600 mr-3" />
// //                   <span className="font-medium">Schedule Interviews</span>
// //                 </div>
// //                 <span className="text-sm text-gray-500">{stats.activeInterviews} scheduled</span>
// //               </button>
              
// //               <button
// //                 onClick={() => setShowNewPipelineModal(true)}
// //                 className="w-full p-4 border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center justify-between"
// //               >
// //                 <div className="flex items-center">
// //                   <Users className="w-5 h-5 text-green-600 mr-3" />
// //                   <span className="font-medium">Start New Recruitment</span>
// //                 </div>
// //                 <Plus className="w-4 h-4 text-gray-400" />
// //               </button>
// //             </div>
// //           </div>
// //         </div>
// //       </main>

// //       {/* New Pipeline Modal */}
// //       {showNewPipelineModal && <NewPipelineModal />}
// //     </div>
// //   );
// // };

// // export default Dashboard;
// // import React, { useState, useEffect } from 'react';
// // import { Search, Filter, Calendar, Users, Clock, Award, Bell, ChevronDown, Plus, X, TrendingUp, AlertCircle, CheckCircle, XCircle, BarChart3, Target } from 'lucide-react';
// // import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, Legend } from 'recharts';
// // import { useNavigate } from 'react-router-dom';
// // import Navigation from './Navigation';

// // const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://127.0.0.1:5000';

// // const Dashboard = () => {
// //   const navigate = useNavigate();
// //   const [loading, setLoading] = useState(true);
// //   const [candidates, setCandidates] = useState([]);
// //   const [jobs, setJobs] = useState([]);
// //   const [stats, setStats] = useState({
// //     totalApplications: 0,
// //     activeInterviews: 0,
// //     timeToHire: 0,
// //     activeAssessments: 0,
// //     shortlistRate: 0,
// //     assessmentCompletionRate: 0,
// //     totalHires: 0,
// //     pendingActions: 0
// //   });
// //   const [recruitmentData, setRecruitmentData] = useState([]);
// //   const [showNewPipelineModal, setShowNewPipelineModal] = useState(false);
// //   const [selectedTimeRange, setSelectedTimeRange] = useState('month');
// //   const [notifications, setNotifications] = useState([]);

// //   useEffect(() => {
// //     fetchDashboardData();
// //     // Refresh data every 30 seconds
// //     const interval = setInterval(fetchDashboardData, 30000);
// //     return () => clearInterval(interval);
// //   }, [selectedTimeRange]);

// //   const fetchDashboardData = async () => {
// //     setLoading(true);
// //     try {
// //       const [jobsRes, candidatesRes, statsRes] = await Promise.all([
// //         fetch(`${BACKEND_URL}/api/jobs`).catch(() => ({ ok: false, json: () => [] })),
// //         fetch(`${BACKEND_URL}/api/candidates`).catch(() => ({ ok: false, json: () => [] })),
// //         fetch(`${BACKEND_URL}/api/recruitment-stats`).catch(() => ({ ok: false, json: () => [] }))
// //       ]);

// //       let jobsData = [];
// //       let candidatesData = [];
// //       let statsData = [];

// //       // Handle jobs response
// //       if (jobsRes.ok) {
// //         try {
// //           jobsData = await jobsRes.json();
// //         } catch (e) {
// //           console.error('Error parsing jobs data:', e);
// //           jobsData = [];
// //         }
// //       }

// //       // Handle candidates response
// //       if (candidatesRes.ok) {
// //         try {
// //           candidatesData = await candidatesRes.json();
// //         } catch (e) {
// //           console.error('Error parsing candidates data:', e);
// //           candidatesData = [];
// //         }
// //       }

// //       // Handle stats response
// //       if (statsRes.ok) {
// //         try {
// //           statsData = await statsRes.json();
// //         } catch (e) {
// //           console.error('Error parsing stats data:', e);
// //           statsData = [];
// //         }
// //       }

// //       // Ensure data is arrays
// //       setJobs(Array.isArray(jobsData) ? jobsData : []);
// //       setCandidates(Array.isArray(candidatesData) ? candidatesData : []);
// //       setRecruitmentData(Array.isArray(statsData) ? statsData : []);

// //       // Calculate real-time stats
// //       calculateStats(Array.isArray(candidatesData) ? candidatesData : []);
// //       // Generate notifications
// //       generateNotifications(Array.isArray(candidatesData) ? candidatesData : []);
// //     } catch (error) {
// //       console.error('Error fetching dashboard data:', error);
// //       setJobs([]);
// //       setCandidates([]);
// //       setRecruitmentData([]);
// //     } finally {
// //       setLoading(false);
// //     }
// //   };

// //   const calculateStats = (candidatesData) => {
// //     // Add safety checks for undefined data
// //     if (!Array.isArray(candidatesData)) {
// //       candidatesData = [];
// //     }

// //     const total = candidatesData.length;
// //     const shortlisted = candidatesData.filter(c => c && c.status === 'Shortlisted').length;
// //     const interviews = candidatesData.filter(c => c && c.interview_scheduled).length;
// //     const assessmentsSent = candidatesData.filter(c => c && c.exam_link_sent).length;
// //     const assessmentsCompleted = candidatesData.filter(c => c && c.exam_completed).length;
// //     const hires = candidatesData.filter(c => c && c.final_status === 'Hired').length;
// //     const pendingAssessments = candidatesData.filter(c => 
// //       c && c.exam_link_sent && !c.exam_completed && !c.link_expired
// //     ).length;
// //     const pendingInterviews = candidatesData.filter(c => {
// //       if (!c || !c.interview_scheduled || !c.interview_date) return false;
// //       try {
// //         return new Date(c.interview_date) > new Date();
// //       } catch {
// //         return false;
// //       }
// //     }).length;

// //     setStats({
// //       totalApplications: total,
// //       activeInterviews: interviews,
// //       timeToHire: calculateAverageTimeToHire(candidatesData),
// //       activeAssessments: pendingAssessments,
// //       shortlistRate: total > 0 ? ((shortlisted / total) * 100).toFixed(1) : 0,
// //       assessmentCompletionRate: assessmentsSent > 0 ? ((assessmentsCompleted / assessmentsSent) * 100).toFixed(1) : 0,
// //       totalHires: hires,
// //       pendingActions: pendingAssessments + pendingInterviews
// //     });
// //   };

// //   const calculateAverageTimeToHire = (candidates) => {
// //     if (!Array.isArray(candidates)) return 0;
    
// //     const hiredCandidates = candidates.filter(c => 
// //       c && c.final_status === 'Hired' && c.processed_date
// //     );
    
// //     if (hiredCandidates.length === 0) return 0;
    
// //     const totalDays = hiredCandidates.reduce((acc, c) => {
// //       try {
// //         const processedDate = new Date(c.processed_date);
// //         const hireDate = new Date(); // Should be actual hire date
// //         const days = Math.floor((hireDate - processedDate) / (1000 * 60 * 60 * 24));
// //         return acc + Math.max(days, 0);
// //       } catch {
// //         return acc;
// //       }
// //     }, 0);
    
// //     return Math.round(totalDays / hiredCandidates.length);
// //   };

// //   const generateNotifications = (candidatesData) => {
// //     if (!Array.isArray(candidatesData)) {
// //       setNotifications([]);
// //       return;
// //     }

// //     const notifications = [];
    
// //     // Pending assessments
// //     const pendingAssessments = candidatesData.filter(c => 
// //       c && c.exam_link_sent && !c.exam_completed && !c.link_expired
// //     );
    
// //     if (pendingAssessments.length > 0) {
// //       notifications.push({
// //         id: 1,
// //         type: 'warning',
// //         message: `${pendingAssessments.length} candidates have pending assessments`,
// //         action: 'View Assessments',
// //         route: '/assessments'
// //       });
// //     }

// //     // Upcoming interviews
// //     const upcomingInterviews = candidatesData.filter(c => {
// //       if (!c || !c.interview_date) return false;
// //       try {
// //         const interviewDate = new Date(c.interview_date);
// //         const now = new Date();
// //         const hoursDiff = (interviewDate - now) / (1000 * 60 * 60);
// //         return hoursDiff > 0 && hoursDiff < 24;
// //       } catch {
// //         return false;
// //       }
// //     });
    
// //     if (upcomingInterviews.length > 0) {
// //       notifications.push({
// //         id: 2,
// //         type: 'info',
// //         message: `${upcomingInterviews.length} interviews scheduled for today`,
// //         action: 'View Schedule',
// //         route: '/scheduler'
// //       });
// //     }

// //     setNotifications(notifications);
// //   };

// //   const StatCard = ({ title, value, change, icon: Icon, color, subtitle }) => (
// //     <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
// //       <div className="flex items-center justify-between mb-4">
// //         <h3 className="text-gray-500 text-sm font-medium">{title}</h3>
// //         <div className={`p-2 rounded-lg ${color}`}>
// //           <Icon className="w-5 h-5 text-white" />
// //         </div>
// //       </div>
// //       <div className="flex items-baseline">
// //         <p className="text-3xl font-bold text-gray-900">{value}</p>
// //         {change !== undefined && (
// //           <span className={`ml-2 text-sm font-medium flex items-center ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
// //             {change >= 0 ? <TrendingUp className="w-4 h-4 mr-1" /> : null}
// //             {change >= 0 ? '+' : ''}{change}%
// //           </span>
// //         )}
// //       </div>
// //       {subtitle && <p className="text-gray-500 text-xs mt-1">{subtitle}</p>}
// //     </div>
// //   );

// //   const NewPipelineModal = () => {
// //     const [selectedJob, setSelectedJob] = useState(null);
// //     const [jobDesc, setJobDesc] = useState('');
// //     const [isSubmitting, setIsSubmitting] = useState(false);

// //     const handleJobSelect = (e) => {
// //       const job = jobs.find(j => j.id === e.target.value);
// //       setSelectedJob(job);
// //       setJobDesc(job?.description || '');
// //     };

// //     const handleSubmit = async () => {
// //       if (!selectedJob) return;
      
// //       setIsSubmitting(true);
// //       try {
// //         const response = await fetch(`${BACKEND_URL}/api/run_full_pipeline`, {
// //           method: 'POST',
// //           headers: { 'Content-Type': 'application/json' },
// //           body: JSON.stringify({
// //             job_id: selectedJob.id,
// //             job_title: selectedJob.title,
// //             job_desc: jobDesc
// //           })
// //         });
        
// //         const data = await response.json();
// //         if (response.ok && data.success) {
// //           alert(data.message || 'Pipeline started successfully!');
// //           setShowNewPipelineModal(false);
// //           setTimeout(fetchDashboardData, 2000);
// //         } else {
// //           alert(data.message || 'Failed to start pipeline');
// //         }
// //       } catch (error) {
// //         console.error('Pipeline error:', error);
// //         alert('Error starting pipeline: ' + error.message);
// //       } finally {
// //         setIsSubmitting(false);
// //       }
// //     };

// //     return (
// //       <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
// //         <div className="bg-white rounded-lg p-6 w-full max-w-md">
// //           <div className="flex justify-between items-center mb-4">
// //             <h2 className="text-xl font-bold">Start Recruitment Pipeline</h2>
// //             <button onClick={() => setShowNewPipelineModal(false)} className="text-gray-400 hover:text-gray-600">
// //               <X className="w-5 h-5" />
// //             </button>
// //           </div>
          
// //           <div className="space-y-4">
// //             <div>
// //               <label className="block text-sm font-medium text-gray-700 mb-1">Select Job Position</label>
// //               <select
// //                 onChange={handleJobSelect}
// //                 className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
// //                 value={selectedJob?.id || ''}
// //               >
// //                 <option value="">Select a job...</option>
// //                 {jobs.map(job => (
// //                   <option key={job.id} value={job.id}>
// //                     {job.title} - {job.location} ({job.applications || 0} applications)
// //                   </option>
// //                 ))}
// //               </select>
// //             </div>
            
// //             {selectedJob && (
// //               <div className="bg-blue-50 p-4 rounded-lg">
// //                 <h4 className="font-medium text-blue-900 mb-1">{selectedJob.title}</h4>
// //                 <p className="text-sm text-blue-700">{selectedJob.department} • {selectedJob.location}</p>
// //               </div>
// //             )}
            
// //             <div>
// //               <label className="block text-sm font-medium text-gray-700 mb-1">Job Description</label>
// //               <textarea
// //                 value={jobDesc}
// //                 onChange={(e) => setJobDesc(e.target.value)}
// //                 className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 h-32"
// //                 placeholder="Enter or modify job description..."
// //               />
// //             </div>
            
// //             <button
// //               onClick={handleSubmit}
// //               disabled={!selectedJob || isSubmitting}
// //               className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
// //             >
// //               {isSubmitting ? 'Starting Pipeline...' : 'Start Pipeline'}
// //             </button>
            
// //             <p className="text-xs text-gray-500 text-center">
// //               This will scrape resumes, create assessments, and start the AI screening process
// //             </p>
// //           </div>
// //         </div>
// //       </div>
// //     );
// //   };

// //   const getPipelineStages = () => {
// //     const stages = [
// //       { name: 'Applied', value: candidates.length, color: '#3B82F6' },
// //       { name: 'Screened', value: candidates.filter(c => c && c.ats_score > 0).length, color: '#10B981' },
// //       { name: 'Shortlisted', value: candidates.filter(c => c && c.status === 'Shortlisted').length, color: '#F59E0B' },
// //       { name: 'Assessment', value: candidates.filter(c => c && c.exam_completed).length, color: '#8B5CF6' },
// //       { name: 'Interview', value: candidates.filter(c => c && c.interview_scheduled).length, color: '#EF4444' },
// //       { name: 'Hired', value: candidates.filter(c => c && c.final_status === 'Hired').length, color: '#059669' }
// //     ];
    
// //     return stages;
// //   };

// //   const getAssessmentMetrics = () => {
// //     const sent = candidates.filter(c => c && c.exam_link_sent).length;
// //     const started = candidates.filter(c => c && c.exam_started).length;
// //     const completed = candidates.filter(c => c && c.exam_completed).length;
// //     const passed = candidates.filter(c => c && c.exam_percentage >= 70).length;
    
// //     return [
// //       { name: 'Sent', value: sent },
// //       { name: 'Started', value: started },
// //       { name: 'Completed', value: completed },
// //       { name: 'Passed', value: passed }
// //     ];
// //   };

// //   if (loading) {
// //     return (
// //       <div className="min-h-screen bg-gray-50 flex items-center justify-center">
// //         <div className="text-center">
// //           <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
// //           <p className="mt-4 text-gray-600">Loading dashboard...</p>
// import React, { useState, useEffect } from 'react';
// import { Search, Filter, Calendar, Users, Clock, Award, Bell, ChevronDown, Plus, X, TrendingUp, AlertCircle, CheckCircle, XCircle, BarChart3, Target } from 'lucide-react';
// import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, Legend } from 'recharts';
// import { useNavigate } from 'react-router-dom';
// import Navigation from './Navigation';

// const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://127.0.0.1:5000';

// const Dashboard = () => {
//   const navigate = useNavigate();
//   const [loading, setLoading] = useState(true);
//   const [candidates, setCandidates] = useState([]);
//   const [jobs, setJobs] = useState([]);
//   const [stats, setStats] = useState({
//     totalApplications: 0,
//     activeInterviews: 0,
//     timeToHire: 0,
//     activeAssessments: 0,
//     shortlistRate: 0,
//     assessmentCompletionRate: 0,
//     totalHires: 0,
//     pendingActions: 0
//   });
//   const [recruitmentData, setRecruitmentData] = useState([]);
//   const [showNewPipelineModal, setShowNewPipelineModal] = useState(false);
//   const [selectedTimeRange, setSelectedTimeRange] = useState('month');
//   const [notifications, setNotifications] = useState([]);

//   useEffect(() => {
//     fetchDashboardData();
//     // Refresh data every 30 seconds
//     const interval = setInterval(fetchDashboardData, 30000);
//     return () => clearInterval(interval);
//   }, [selectedTimeRange]);

//   const fetchDashboardData = async () => {
//     setLoading(true);
//     try {
//       const [jobsRes, candidatesRes, statsRes] = await Promise.all([
//         fetch(`${BACKEND_URL}/api/jobs`).catch(() => ({ ok: false, json: () => [] })),
//         fetch(`${BACKEND_URL}/api/candidates`).catch(() => ({ ok: false, json: () => [] })),
//         fetch(`${BACKEND_URL}/api/recruitment-stats`).catch(() => ({ ok: false, json: () => [] }))
//       ]);

//       let jobsData = [];
//       let candidatesData = [];
//       let statsData = [];

//       // Handle jobs response
//       if (jobsRes.ok) {
//         try {
//           jobsData = await jobsRes.json();
//         } catch (e) {
//           console.error('Error parsing jobs data:', e);
//           jobsData = [];
//         }
//       }

//       // Handle candidates response
//       if (candidatesRes.ok) {
//         try {
//           candidatesData = await candidatesRes.json();
//         } catch (e) {
//           console.error('Error parsing candidates data:', e);
//           candidatesData = [];
//         }
//       }

//       // Handle stats response
//       if (statsRes.ok) {
//         try {
//           statsData = await statsRes.json();
//         } catch (e) {
//           console.error('Error parsing stats data:', e);
//           statsData = [];
//         }
//       }

//       // Ensure data is arrays
//       setJobs(Array.isArray(jobsData) ? jobsData : []);
//       setCandidates(Array.isArray(candidatesData) ? candidatesData : []);
//       setRecruitmentData(Array.isArray(statsData) ? statsData : []);

//       // Calculate real-time stats
//       calculateStats(Array.isArray(candidatesData) ? candidatesData : []);
//       // Generate notifications
//       generateNotifications(Array.isArray(candidatesData) ? candidatesData : []);
//     } catch (error) {
//       console.error('Error fetching dashboard data:', error);
//       setJobs([]);
//       setCandidates([]);
//       setRecruitmentData([]);
//     } finally {
//       setLoading(false);
//     }
//   };

//   const calculateStats = (candidatesData) => {
//     // Add safety checks for undefined data
//     if (!Array.isArray(candidatesData)) {
//       candidatesData = [];
//     }

//     const total = candidatesData.length;
//     const shortlisted = candidatesData.filter(c => c && c.status === 'Shortlisted').length;
//     const interviews = candidatesData.filter(c => c && c.interview_scheduled).length;
//     const assessmentsSent = candidatesData.filter(c => c && c.exam_link_sent).length;
//     const assessmentsCompleted = candidatesData.filter(c => c && c.exam_completed).length;
//     const hires = candidatesData.filter(c => c && c.final_status === 'Hired').length;
//     const pendingAssessments = candidatesData.filter(c => 
//       c && c.exam_link_sent && !c.exam_completed && !c.link_expired
//     ).length;
//     const pendingInterviews = candidatesData.filter(c => {
//       if (!c || !c.interview_scheduled || !c.interview_date) return false;
//       try {
//         return new Date(c.interview_date) > new Date();
//       } catch {
//         return false;
//       }
//     }).length;

//     setStats({
//       totalApplications: total,
//       activeInterviews: interviews,
//       timeToHire: calculateAverageTimeToHire(candidatesData),
//       activeAssessments: pendingAssessments,
//       shortlistRate: total > 0 ? ((shortlisted / total) * 100).toFixed(1) : 0,
//       assessmentCompletionRate: assessmentsSent > 0 ? ((assessmentsCompleted / assessmentsSent) * 100).toFixed(1) : 0,
//       totalHires: hires,
//       pendingActions: pendingAssessments + pendingInterviews
//     });
//   };

//   const calculateAverageTimeToHire = (candidates) => {
//     if (!Array.isArray(candidates)) return 0;
    
//     const hiredCandidates = candidates.filter(c => 
//       c && c.final_status === 'Hired' && c.processed_date
//     );
    
//     if (hiredCandidates.length === 0) return 0;
    
//     const totalDays = hiredCandidates.reduce((acc, c) => {
//       try {
//         const processedDate = new Date(c.processed_date);
//         const hireDate = new Date(); // Should be actual hire date
//         const days = Math.floor((hireDate - processedDate) / (1000 * 60 * 60 * 24));
//         return acc + Math.max(days, 0);
//       } catch {
//         return acc;
//       }
//     }, 0);
    
//     return Math.round(totalDays / hiredCandidates.length);
//   };

//   const generateNotifications = (candidatesData) => {
//     if (!Array.isArray(candidatesData)) {
//       setNotifications([]);
//       return;
//     }

//     const notifications = [];
    
//     // Pending assessments
//     const pendingAssessments = candidatesData.filter(c => 
//       c && c.exam_link_sent && !c.exam_completed && !c.link_expired
//     );
    
//     if (pendingAssessments.length > 0) {
//       notifications.push({
//         id: 1,
//         type: 'warning',
//         message: `${pendingAssessments.length} candidates have pending assessments`,
//         action: 'View Assessments',
//         route: '/assessments'
//       });
//     }

//     // Upcoming interviews
//     const upcomingInterviews = candidatesData.filter(c => {
//       if (!c || !c.interview_date) return false;
//       try {
//         const interviewDate = new Date(c.interview_date);
//         const now = new Date();
//         const hoursDiff = (interviewDate - now) / (1000 * 60 * 60);
//         return hoursDiff > 0 && hoursDiff < 24;
//       } catch {
//         return false;
//       }
//     });
    
//     if (upcomingInterviews.length > 0) {
//       notifications.push({
//         id: 2,
//         type: 'info',
//         message: `${upcomingInterviews.length} interviews scheduled for today`,
//         action: 'View Schedule',
//         route: '/scheduler'
//       });
//     }

//     setNotifications(notifications);
//   };

//   const StatCard = ({ title, value, change, icon: Icon, color, subtitle }) => (
//     <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
//       <div className="flex items-center justify-between mb-4">
//         <h3 className="text-gray-500 text-sm font-medium">{title}</h3>
//         <div className={`p-2 rounded-lg ${color}`}>
//           <Icon className="w-5 h-5 text-white" />
//         </div>
//       </div>
//       <div className="flex items-baseline">
//         <p className="text-3xl font-bold text-gray-900">{value}</p>
//         {change !== undefined && (
//           <span className={`ml-2 text-sm font-medium flex items-center ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
//             {change >= 0 ? <TrendingUp className="w-4 h-4 mr-1" /> : null}
//             {change >= 0 ? '+' : ''}{change}%
//           </span>
//         )}
//       </div>
//       {subtitle && <p className="text-gray-500 text-xs mt-1">{subtitle}</p>}
//     </div>
//   );

//   const NewPipelineModal = () => {
//     const [selectedJob, setSelectedJob] = useState(null);
//     const [jobDesc, setJobDesc] = useState('');
//     const [isSubmitting, setIsSubmitting] = useState(false);

//     const handleJobSelect = (e) => {
//       const job = jobs.find(j => j.id === e.target.value);
//       setSelectedJob(job);
//       setJobDesc(job?.description || '');
//     };

//     const handleSubmit = async () => {
//       if (!selectedJob) return;
      
//       setIsSubmitting(true);
//       try {
//         const response = await fetch(`${BACKEND_URL}/api/run_full_pipeline`, {
//           method: 'POST',
//           headers: { 'Content-Type': 'application/json' },
//           body: JSON.stringify({
//             job_id: selectedJob.id,
//             job_title: selectedJob.title,
//             job_desc: jobDesc
//           })
//         });
        
//         const data = await response.json();
//         if (response.ok && data.success) {
//           alert(data.message || 'Pipeline started successfully!');
//           setShowNewPipelineModal(false);
//           setTimeout(fetchDashboardData, 2000);
//         } else {
//           alert(data.message || 'Failed to start pipeline');
//         }
//       } catch (error) {
//         console.error('Pipeline error:', error);
//         alert('Error starting pipeline: ' + error.message);
//       } finally {
//         setIsSubmitting(false);
//       }
//     };

//     return (
//       <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
//         <div className="bg-white rounded-lg p-6 w-full max-w-md">
//           <div className="flex justify-between items-center mb-4">
//             <h2 className="text-xl font-bold">Start Recruitment Pipeline</h2>
//             <button onClick={() => setShowNewPipelineModal(false)} className="text-gray-400 hover:text-gray-600">
//               <X className="w-5 h-5" />
//             </button>
//           </div>
          
//           <div className="space-y-4">
//             <div>
//               <label className="block text-sm font-medium text-gray-700 mb-1">Select Job Position</label>
//               <select
//                 onChange={handleJobSelect}
//                 className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
//                 value={selectedJob?.id || ''}
//               >
//                 <option value="">Select a job...</option>
//                 {jobs.map(job => (
//                   <option key={job.id} value={job.id}>
//                     {job.title} - {job.location} ({job.applications || 0} applications)
//                   </option>
//                 ))}
//               </select>
//             </div>
            
//             {selectedJob && (
//               <div className="bg-blue-50 p-4 rounded-lg">
//                 <h4 className="font-medium text-blue-900 mb-1">{selectedJob.title}</h4>
//                 <p className="text-sm text-blue-700">{selectedJob.department} • {selectedJob.location}</p>
//               </div>
//             )}
            
//             <div>
//               <label className="block text-sm font-medium text-gray-700 mb-1">Job Description</label>
//               <textarea
//                 value={jobDesc}
//                 onChange={(e) => setJobDesc(e.target.value)}
//                 className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 h-32"
//                 placeholder="Enter or modify job description..."
//               />
//             </div>
            
//             <button
//               onClick={handleSubmit}
//               disabled={!selectedJob || isSubmitting}
//               className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
//             >
//               {isSubmitting ? 'Starting Pipeline...' : 'Start Pipeline'}
//             </button>
            
//             <p className="text-xs text-gray-500 text-center">
//               This will scrape resumes, create assessments, and start the AI screening process
//             </p>
//           </div>
//         </div>
//       </div>
//     );
//   };

//   const getPipelineStages = () => {
//     const stages = [
//       { name: 'Applied', value: candidates.length, color: '#3B82F6' },
//       { name: 'Screened', value: candidates.filter(c => c && c.ats_score > 0).length, color: '#10B981' },
//       { name: 'Shortlisted', value: candidates.filter(c => c && c.status === 'Shortlisted').length, color: '#F59E0B' },
//       { name: 'Assessment', value: candidates.filter(c => c && c.exam_completed).length, color: '#8B5CF6' },
//       { name: 'Interview', value: candidates.filter(c => c && c.interview_scheduled).length, color: '#EF4444' },
//       { name: 'Hired', value: candidates.filter(c => c && c.final_status === 'Hired').length, color: '#059669' }
//     ];
    
//     return stages;
//   };

//   const getAssessmentMetrics = () => {
//     const sent = candidates.filter(c => c && c.exam_link_sent).length;
//     const started = candidates.filter(c => c && c.exam_started).length;
//     const completed = candidates.filter(c => c && c.exam_completed).length;
//     const passed = candidates.filter(c => c && c.exam_percentage >= 70).length;
    
//     return [
//       { name: 'Sent', value: sent },
//       { name: 'Started', value: started },
//       { name: 'Completed', value: completed },
//       { name: 'Passed', value: passed }
//     ];
//   };

//   if (loading) {
//     return (
//       <div className="min-h-screen bg-gray-50 flex items-center justify-center">
//         <div className="text-center">
//           <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
//           <p className="mt-4 text-gray-600">Loading dashboard...</p>
//         </div>
//       </div>
//     );
//   }

//   return (
//     <div className="min-h-screen bg-gray-50">
//       <Navigation />

//       <main className="p-6">
//         {/* Header */}
//         <div className="flex items-center justify-between mb-6">
//           <div>
//             <h1 className="text-2xl font-bold text-gray-900">Recruitment Dashboard</h1>
//             <p className="text-gray-600 mt-1">Welcome back! Here's your recruitment overview</p>
//           </div>
//           <div className="flex items-center space-x-3">
//             <select
//               value={selectedTimeRange}
//               onChange={(e) => setSelectedTimeRange(e.target.value)}
//               className="border rounded-lg px-4 py-2 text-sm"
//             >
//               <option value="week">This Week</option>
//               <option value="month">This Month</option>
//               <option value="quarter">This Quarter</option>
//               <option value="year">This Year</option>
//             </select>
//             <button
//               onClick={() => setShowNewPipelineModal(true)}
//               className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2"
//             >
//               <Plus className="w-4 h-4" />
//               <span>New Pipeline</span>
//             </button>
//           </div>
//         </div>

//         {/* Notifications */}
//         {notifications.length > 0 && (
//           <div className="mb-6 space-y-2">
//             {notifications.map(notification => (
//               <div
//                 key={notification.id}
//                 className={`p-4 rounded-lg border flex items-center justify-between ${
//                   notification.type === 'warning' 
//                     ? 'bg-yellow-50 border-yellow-200' 
//                     : 'bg-blue-50 border-blue-200'
//                 }`}
//               >
//                 <div className="flex items-center">
//                   <AlertCircle className={`w-5 h-5 mr-3 ${
//                     notification.type === 'warning' ? 'text-yellow-600' : 'text-blue-600'
//                   }`} />
//                   <span className={notification.type === 'warning' ? 'text-yellow-800' : 'text-blue-800'}>
//                     {notification.message}
//                   </span>
//                 </div>
//                 <button
//                   onClick={() => navigate(notification.route)}
//                   className={`px-3 py-1 rounded text-sm font-medium ${
//                     notification.type === 'warning'
//                       ? 'bg-yellow-600 text-white hover:bg-yellow-700'
//                       : 'bg-blue-600 text-white hover:bg-blue-700'
//                   }`}
//                 >
//                   {notification.action}
//                 </button>
//               </div>
//             ))}
//           </div>
//         )}

//         {/* Stats Grid */}
//         <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
//           <StatCard
//             title="Total Applications"
//             value={stats.totalApplications}
//             change={12.5}
//             icon={Users}
//             color="bg-blue-600"
//             subtitle="All time applications"
//           />
//           <StatCard
//             title="Shortlist Rate"
//             value={`${stats.shortlistRate}%`}
//             change={5.2}
//             icon={Target}
//             color="bg-green-600"
//             subtitle="Candidates shortlisted"
//           />
//           <StatCard
//             title="Time-to-Hire"
//             value={`${stats.timeToHire}d`}
//             change={-8.3}
//             icon={Clock}
//             color="bg-yellow-600"
//             subtitle="Average days to hire"
//           />
//           <StatCard
//             title="Pending Actions"
//             value={stats.pendingActions}
//             icon={Bell}
//             color="bg-purple-600"
//             subtitle="Requires attention"
//           />
//         </div>

//         {/* Charts Row */}
//         <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
//           {/* Pipeline Funnel */}
//           <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
//             <h3 className="text-lg font-semibold mb-4">Recruitment Pipeline</h3>
//             <ResponsiveContainer width="100%" height={300}>
//               <BarChart data={getPipelineStages()}>
//                 <CartesianGrid strokeDasharray="3 3" />
//                 <XAxis dataKey="name" />
//                 <YAxis />
//                 <Tooltip />
//                 <Bar dataKey="value" fill="#3B82F6">
//                   {getPipelineStages().map((entry, index) => (
//                     <Cell key={`cell-${index}`} fill={entry.color} />
//                   ))}
//                 </Bar>
//               </BarChart>
//             </ResponsiveContainer>
//           </div>

//           {/* Activity Trend */}
//           <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
//             <h3 className="text-lg font-semibold mb-4">Recruitment Activity</h3>
//             <ResponsiveContainer width="100%" height={300}>
//               <LineChart data={recruitmentData}>
//                 <CartesianGrid strokeDasharray="3 3" />
//                 <XAxis dataKey="month" />
//                 <YAxis />
//                 <Tooltip />
//                 <Legend />
//                 <Line type="monotone" dataKey="applications" stroke="#3B82F6" strokeWidth={2} name="Applications" />
//                 <Line type="monotone" dataKey="interviews" stroke="#10B981" strokeWidth={2} name="Interviews" />
//                 <Line type="monotone" dataKey="hires" stroke="#EF4444" strokeWidth={2} name="Hires" />
//               </LineChart>
//             </ResponsiveContainer>
//           </div>
//         </div>

//         {/* Active Jobs Table */}
//         <div className="bg-white rounded-lg shadow-sm border border-gray-100 mb-8">
//           <div className="p-6 border-b border-gray-200">
//             <div className="flex items-center justify-between">
//               <h3 className="text-lg font-semibold">Active Job Positions</h3>
//               <button
//                 onClick={() => navigate('/candidates')}
//                 className="text-blue-600 hover:text-blue-700 text-sm font-medium"
//               >
//                 View All Candidates →
//               </button>
//             </div>
//           </div>
//           <div className="overflow-x-auto">
//             <table className="w-full">
//               <thead>
//                 <tr className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
//                   <th className="px-6 py-3">Position</th>
//                   <th className="px-6 py-3">Department</th>
//                   <th className="px-6 py-3">Location</th>
//                   <th className="px-6 py-3">Applications</th>
//                   <th className="px-6 py-3">Shortlisted</th>
//                   <th className="px-6 py-3">In Progress</th>
//                   <th className="px-6 py-3">Status</th>
//                   <th className="px-6 py-3">Actions</th>
//                 </tr>
//               </thead>
//               <tbody className="divide-y divide-gray-200">
//                 {jobs.length === 0 ? (
//                   <tr>
//                     <td colSpan="8" className="px-6 py-8 text-center text-gray-500">
//                       <Users className="w-12 h-12 mx-auto mb-3 text-gray-300" />
//                       <p className="text-lg font-medium">No job positions found</p>
//                       <p className="mt-1">Start a new recruitment pipeline to begin</p>
//                       <button
//                         onClick={() => setShowNewPipelineModal(true)}
//                         className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
//                       >
//                         Start New Pipeline
//                       </button>
//                     </td>
//                   </tr>
//                 ) : (
//                   jobs.map((job) => {
//                     const jobCandidates = candidates.filter(c => c && c.job_id === job.id);
//                     const shortlisted = jobCandidates.filter(c => c.status === 'Shortlisted').length;
//                     const inProgress = jobCandidates.filter(c => c.exam_link_sent || c.interview_scheduled).length;
                    
//                     return (
//                       <tr key={job.id} className="hover:bg-gray-50">
//                         <td className="px-6 py-4">
//                           <div className="text-sm font-medium text-gray-900">{job.title}</div>
//                         </td>
//                         <td className="px-6 py-4 text-sm text-gray-500">{job.department}</td>
//                         <td className="px-6 py-4 text-sm text-gray-500">{job.location}</td>
//                         <td className="px-6 py-4">
//                           <div className="flex items-center">
//                             <span className="text-sm font-medium text-gray-900">{jobCandidates.length}</span>
//                           </div>
//                         </td>
//                         <td className="px-6 py-4">
//                           <div className="flex items-center">
//                             <span className="text-sm font-medium text-green-600">{shortlisted}</span>
//                           </div>
//                         </td>
//                         <td className="px-6 py-4">
//                           <div className="flex items-center">
//                             <span className="text-sm font-medium text-blue-600">{inProgress}</span>
//                           </div>
//                         </td>
//                         <td className="px-6 py-4">
//                           <span className="inline-flex px-2 py-1 text-xs font-semibold leading-5 text-green-800 bg-green-100 rounded-full">
//                             Active
//                           </span>
//                         </td>
//                         <td className="px-6 py-4 text-sm">
//                           <div className="flex space-x-2">
//                             <button
//                               onClick={() => navigate(`/candidates?job_id=${job.id}`)}
//                               className="text-blue-600 hover:text-blue-900"
//                             >
//                               View
//                             </button>
//                             <button
//                               onClick={() => {
//                                 setShowNewPipelineModal(true);
//                               }}
//                               className="text-green-600 hover:text-green-900"
//                             >
//                               Run Pipeline
//                             </button>
//                           </div>
//                         </td>
//                       </tr>
//                     );
//                   })
//                 )}
//               </tbody>
//             </table>
//           </div>
//         </div>

//         {/* Assessment Metrics */}
//         <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
//           {/* Assessment Completion */}
//           <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
//             <h3 className="text-lg font-semibold mb-4">Assessment Metrics</h3>
//             <ResponsiveContainer width="100%" height={200}>
//               <BarChart data={getAssessmentMetrics()}>
//                 <CartesianGrid strokeDasharray="3 3" />
//                 <XAxis dataKey="name" />
//                 <YAxis />
//                 <Tooltip />
//                 <Bar dataKey="value" fill="#8B5CF6" />
//               </BarChart>
//             </ResponsiveContainer>
//             <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
//               <div>
//                 <p className="text-gray-500">Completion Rate</p>
//                 <p className="text-xl font-semibold">{stats.assessmentCompletionRate}%</p>
//               </div>
//               <div>
//                 <p className="text-gray-500">Pass Rate</p>
//                 <p className="text-xl font-semibold">
//                   {candidates.filter(c => c && c.exam_completed).length > 0
//                     ? ((candidates.filter(c => c && c.exam_percentage >= 70).length / candidates.filter(c => c && c.exam_completed).length) * 100).toFixed(1)
//                     : 0}%
//                 </p>
//               </div>
//             </div>
//           </div>

//           {/* Quick Actions */}
//           <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
//             <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
//             <div className="space-y-3">
//               <button
//                 onClick={() => navigate('/assessments')}
//                 className="w-full p-4 border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center justify-between"
//               >
//                 <div className="flex items-center">
//                   <Award className="w-5 h-5 text-purple-600 mr-3" />
//                   <span className="font-medium">Manage Assessments</span>
//                 </div>
//                 <span className="text-sm text-gray-500">{stats.activeAssessments} pending</span>
//               </button>
              
//               <button
//                 onClick={() => navigate('/scheduler')}
//                 className="w-full p-4 border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center justify-between"
//               >
//                 <div className="flex items-center">
//                   <Calendar className="w-5 h-5 text-blue-600 mr-3" />
//                   <span className="font-medium">Schedule Interviews</span>
//                 </div>
//                 <span className="text-sm text-gray-500">{stats.activeInterviews} scheduled</span>
//               </button>
              
//               <button
//                 onClick={() => setShowNewPipelineModal(true)}
//                 className="w-full p-4 border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center justify-between"
//               >
//                 <div className="flex items-center">
//                   <Users className="w-5 h-5 text-green-600 mr-3" />
//                   <span className="font-medium">Start New Recruitment</span>
//                 </div>
//                 <Plus className="w-4 h-4 text-gray-400" />
//               </button>
//             </div>
//           </div>
//         </div>
//       </main>

//       {/* New Pipeline Modal */}
//       {showNewPipelineModal && <NewPipelineModal />}
//     </div>
//   );
// };

// export default Dashboard;
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Search, Filter, Calendar, Users, Clock, Award, Bell, ChevronDown, Plus, X, TrendingUp, AlertCircle, CheckCircle, XCircle, BarChart3, Target, RefreshCw, PlayCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, Legend } from 'recharts';
import { useNavigate } from 'react-router-dom';
import Navigation from './Navigation';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://127.0.0.1:5000';

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
  const [showNewPipelineModal, setShowNewPipelineModal] = useState(false);
  const [selectedTimeRange, setSelectedTimeRange] = useState('month');
  const [notifications, setNotifications] = useState([]);
  const [pipelineStatus, setPipelineStatus] = useState({});
  const [lastFetchTime, setLastFetchTime] = useState(null);

  // Performance optimization: Use refs for caching
  const dataCache = useRef({});
  const abortController = useRef(null);

  // Optimized fetch with caching and abort controller
  const fetchDashboardData = useCallback(async (forceRefresh = false) => {
    // Check cache first (5 minute cache)
    const cacheKey = `dashboard_${selectedTimeRange}`;
    const now = Date.now();
    
    if (!forceRefresh && dataCache.current[cacheKey] && 
        (now - dataCache.current[cacheKey].timestamp) < 300000) { // 5 minutes
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

    // Cancel previous request
    if (abortController.current) {
      abortController.current.abort();
    }
    abortController.current = new AbortController();

    try {
      // Optimized parallel requests with timeout
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

      // Ensure data is arrays
      const safeJobs = Array.isArray(jobsData) ? jobsData : [];
      const safeCandidates = Array.isArray(candidatesData) ? candidatesData : [];
      const safeStats = Array.isArray(statsData) ? statsData : [];

      // Cache the results
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

      // Calculate real-time stats
      calculateStats(safeCandidates);
      generateNotifications(safeCandidates);

    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('Error fetching dashboard data:', error);
        // Don't show error if we have cached data
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

  // Initial load and periodic refresh
  useEffect(() => {
    fetchDashboardData();
    
    // Refresh every 2 minutes instead of 30 seconds
    const interval = setInterval(() => fetchDashboardData(true), 120000);
    return () => {
      clearInterval(interval);
      if (abortController.current) {
        abortController.current.abort();
      }
    };
  }, [fetchDashboardData]);

  // Manual refresh
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

  const NewPipelineModal = () => {
    const [selectedJob, setSelectedJob] = useState(null);
    const [jobDesc, setJobDesc] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleJobSelect = (e) => {
      const job = jobs.find(j => j.id === e.target.value);
      setSelectedJob(job);
      setJobDesc(job?.description || '');
    };

    const handleSubmit = async () => {
      if (!selectedJob) return;
      
      setIsSubmitting(true);
      setPipelineStatus(prev => ({
        ...prev,
        [selectedJob.id]: { status: 'starting', message: 'Initializing pipeline...' }
      }));

      try {
        const response = await fetch(`${BACKEND_URL}/api/run_full_pipeline`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            job_id: selectedJob.id,
            job_title: selectedJob.title,
            job_desc: jobDesc
          })
        });
        
        const data = await response.json();
        if (response.ok && data.success) {
          setPipelineStatus(prev => ({
            ...prev,
            [selectedJob.id]: { 
              status: 'running', 
              message: data.message,
              estimated_time: data.estimated_time 
            }
          }));
          
          setShowNewPipelineModal(false);
          
          // Show success message and refresh after delay
          setTimeout(() => {
            fetchDashboardData(true);
            setPipelineStatus(prev => ({
              ...prev,
              [selectedJob.id]: { status: 'completed', message: 'Pipeline completed successfully!' }
            }));
          }, 5000);
          
        } else {
          setPipelineStatus(prev => ({
            ...prev,
            [selectedJob.id]: { status: 'error', message: data.message || 'Failed to start pipeline' }
          }));
        }
      } catch (error) {
        console.error('Pipeline error:', error);
        setPipelineStatus(prev => ({
          ...prev,
          [selectedJob.id]: { status: 'error', message: 'Network error: ' + error.message }
        }));
      } finally {
        setIsSubmitting(false);
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Start Recruitment Pipeline</h2>
            <button onClick={() => setShowNewPipelineModal(false)} className="text-gray-400 hover:text-gray-600">
              <X className="w-5 h-5" />
            </button>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Select Job Position</label>
              <select
                onChange={handleJobSelect}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={selectedJob?.id || ''}
              >
                <option value="">Select a job...</option>
                {jobs.map(job => (
                  <option key={job.id} value={job.id}>
                    {job.title} - {job.location} ({job.applications || 0} applications)
                  </option>
                ))}
              </select>
            </div>
            
            {selectedJob && (
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-1">{selectedJob.title}</h4>
                <p className="text-sm text-blue-700">{selectedJob.department} • {selectedJob.location}</p>
                {pipelineStatus[selectedJob.id] && (
                  <div className={`mt-2 p-2 rounded text-sm ${
                    pipelineStatus[selectedJob.id].status === 'running' ? 'bg-yellow-100 text-yellow-800' :
                    pipelineStatus[selectedJob.id].status === 'completed' ? 'bg-green-100 text-green-800' :
                    pipelineStatus[selectedJob.id].status === 'error' ? 'bg-red-100 text-red-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {pipelineStatus[selectedJob.id].message}
                  </div>
                )}
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Job Description</label>
              <textarea
                value={jobDesc}
                onChange={(e) => setJobDesc(e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 h-32"
                placeholder="Enter or modify job description..."
              />
            </div>
            
            <button
              onClick={handleSubmit}
              disabled={!selectedJob || isSubmitting}
              className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {isSubmitting ? (
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
            
            <p className="text-xs text-gray-500 text-center">
              This will scrape resumes, create assessments, and start the AI screening process
            </p>
          </div>
        </div>
      </div>
    );
  };

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

  // Quick pipeline action for specific job
  const handleQuickPipeline = async (job) => {
    setPipelineStatus(prev => ({
      ...prev,
      [job.id]: { status: 'starting', message: 'Starting pipeline...' }
    }));

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
        setPipelineStatus(prev => ({
          ...prev,
          [job.id]: { status: 'running', message: 'Pipeline running...', estimated_time: data.estimated_time }
        }));
        
        // Refresh data after delay
        setTimeout(() => {
          fetchDashboardData(true);
          setPipelineStatus(prev => ({
            ...prev,
            [job.id]: { status: 'completed', message: 'Pipeline completed!' }
          }));
        }, 5000);
      } else {
        setPipelineStatus(prev => ({
          ...prev,
          [job.id]: { status: 'error', message: data.message || 'Failed to start pipeline' }
        }));
      }
    } catch (error) {
      setPipelineStatus(prev => ({
        ...prev,
        [job.id]: { status: 'error', message: 'Network error' }
      }));
    }
  };

  if (loading && !lastFetchTime) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
          <p className="text-sm text-gray-500">Optimizing data fetching...</p>
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
              onClick={() => setShowNewPipelineModal(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2"
            >
              <Plus className="w-4 h-4" />
              <span>New Pipeline</span>
            </button>
          </div>
        </div>

        {/* Pipeline Status Alerts */}
        {Object.entries(pipelineStatus).map(([jobId, status]) => (
          <div
            key={jobId}
            className={`mb-4 p-4 rounded-lg border flex items-center justify-between ${
              status.status === 'running' ? 'bg-yellow-50 border-yellow-200' :
              status.status === 'completed' ? 'bg-green-50 border-green-200' :
              status.status === 'error' ? 'bg-red-50 border-red-200' :
              'bg-blue-50 border-blue-200'
            }`}
          >
            <div className="flex items-center">
              {status.status === 'running' && (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-yellow-600 mr-3"></div>
              )}
              {status.status === 'completed' && <CheckCircle className="w-5 h-5 mr-3 text-green-600" />}
              {status.status === 'error' && <XCircle className="w-5 h-5 mr-3 text-red-600" />}
              <span className={
                status.status === 'running' ? 'text-yellow-800' :
                status.status === 'completed' ? 'text-green-800' :
                status.status === 'error' ? 'text-red-800' :
                'text-blue-800'
              }>
                {status.message}
                {status.estimated_time && status.status === 'running' && (
                  <span className="text-sm ml-2">({status.estimated_time})</span>
                )}
              </span>
            </div>
            {status.status === 'completed' && (
              <button
                onClick={() => navigate('/candidates')}
                className="px-3 py-1 rounded text-sm font-medium bg-green-600 text-white hover:bg-green-700"
              >
                View Candidates
              </button>
            )}
          </div>
        ))}

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
            {loading && !recruitmentData.length ? (
              <div className="animate-pulse h-64 bg-gray-200 rounded"></div>
            ) : (
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
            )}
          </div>

          {/* Activity Trend */}
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold mb-4">Recruitment Activity</h3>
            {loading && !recruitmentData.length ? (
              <div className="animate-pulse h-64 bg-gray-200 rounded"></div>
            ) : (
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
            )}
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
                {loading && jobs.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="px-6 py-8 text-center">
                      <div className="animate-pulse space-y-2">
                        <div className="h-4 bg-gray-200 rounded w-3/4 mx-auto"></div>
                        <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto"></div>
                      </div>
                    </td>
                  </tr>
                ) : jobs.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="px-6 py-8 text-center text-gray-500">
                      <Users className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                      <p className="text-lg font-medium">No job positions found</p>
                      <p className="mt-1">Start a new recruitment pipeline to begin</p>
                      <button
                        onClick={() => setShowNewPipelineModal(true)}
                        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                      >
                        Start New Pipeline
                      </button>
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
                          {currentPipelineStatus && (
                            <div className={`text-xs mt-1 ${
                              currentPipelineStatus.status === 'running' ? 'text-yellow-600' :
                              currentPipelineStatus.status === 'completed' ? 'text-green-600' :
                              currentPipelineStatus.status === 'error' ? 'text-red-600' :
                              'text-blue-600'
                            }`}>
                              {currentPipelineStatus.status === 'running' && '🔄 Pipeline Running'}
                              {currentPipelineStatus.status === 'completed' && '✅ Pipeline Complete'}
                              {currentPipelineStatus.status === 'error' && '❌ Pipeline Failed'}
                            </div>
                          )}
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
                              onClick={() => handleQuickPipeline(job)}
                              disabled={currentPipelineStatus?.status === 'running'}
                              className={`font-medium ${
                                currentPipelineStatus?.status === 'running'
                                  ? 'text-gray-400 cursor-not-allowed'
                                  : 'text-green-600 hover:text-green-900'
                              }`}
                            >
                              {currentPipelineStatus?.status === 'running' ? 'Running...' : 'Run Pipeline'}
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
            {loading && !candidates.length ? (
              <div className="animate-pulse h-48 bg-gray-200 rounded"></div>
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={getAssessmentMetrics()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#8B5CF6" />
                </BarChart>
              </ResponsiveContainer>
            )}
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
                onClick={() => setShowNewPipelineModal(true)}
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

      {/* New Pipeline Modal */}
      {showNewPipelineModal && <NewPipelineModal />}
    </div>
  );
};

export default Dashboard;