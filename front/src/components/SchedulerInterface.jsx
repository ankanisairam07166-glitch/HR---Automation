import React, { useState, useEffect } from 'react';
import { Calendar, CheckCircle, ChevronLeft, ChevronRight, Clock, Users, Video, MapPin, X, Plus, User, Search, FileText } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAppContext } from '../context/AppContext';
import Navigation from './Navigation';

// Add BACKEND_URL constant
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:5000";

const SchedulerInterface = () => {
  const navigate = useNavigate();
  const { selectedCandidate, candidates, scheduleInterview } = useAppContext();
  
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [selectedTimeSlot, setSelectedTimeSlot] = useState(null);
  const [selectedCandidateLocal, setSelectedCandidateLocal] = useState(selectedCandidate || null);
  const [step, setStep] = useState(1); // 1: Select Date, 2: Select Time, 3: Confirm
  const [candidatesList, setCandidatesList] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // ADD: State for job description
  const [jobDescription, setJobDescription] = useState('');
  const [showJobDescriptionModal, setShowJobDescriptionModal] = useState(false);

  // Add useEffect to fetch candidates with full data
  useEffect(() => {
    const fetchCandidates = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/candidates`);
        if (response.ok) {
          const data = await response.json();
          setCandidatesList(data);
        } else {
          // Fallback to context candidates or mock data
          setCandidatesList(candidates && candidates.length > 0 ? candidates : [
            { id: 1, name: 'Emily Johnson', role: 'Senior Software Engineer', photo: null },
            { id: 2, name: 'Michael Chen', role: 'Senior Software Engineer', photo: null },
            { id: 3, name: 'Sophia Williams', role: 'Senior Software Engineer', photo: null }
          ]);
        }
      } catch (error) {
        console.error('Error fetching candidates:', error);
        // Fallback to context candidates or mock data
        setCandidatesList(candidates && candidates.length > 0 ? candidates : [
          { id: 1, name: 'Emily Johnson', role: 'Senior Software Engineer', photo: null },
          { id: 2, name: 'Michael Chen', role: 'Senior Software Engineer', photo: null },
          { id: 3, name: 'Sophia Williams', role: 'Senior Software Engineer', photo: null }
        ]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchCandidates();
  }, [candidates]);

  // Mock data for calendar
  const daysInMonth = new Date(
    selectedDate.getFullYear(),
    selectedDate.getMonth() + 1,
    0
  ).getDate();
  
  const firstDayOfMonth = new Date(
    selectedDate.getFullYear(),
    selectedDate.getMonth(),
    1
  ).getDay();

  // Mock time slots
  const morningSlots = [
    { id: 1, time: '9:00 AM', available: true },
    { id: 2, time: '9:30 AM', available: true },
    { id: 3, time: '10:00 AM', available: true },
    { id: 4, time: '10:30 AM', available: false },
    { id: 5, time: '11:00 AM', available: true },
    { id: 6, time: '11:30 AM', available: true }
  ];

  const afternoonSlots = [
    { id: 7, time: '1:00 PM', available: true },
    { id: 8, time: '1:30 PM', available: false },
    { id: 9, time: '2:00 PM', available: true },
    { id: 10, time: '2:30 PM', available: true },
    { id: 11, time: '3:00 PM', available: false },
    { id: 12, time: '3:30 PM', available: true },
    { id: 13, time: '4:00 PM', available: true },
    { id: 14, time: '4:30 PM', available: true }
  ];

  // Mock interviewers
  const interviewers = [
    { id: 1, name: 'Alex Rodriguez', role: 'Engineering Manager', checked: true },
    { id: 2, name: 'Sarah Kim', role: 'Senior Engineer', checked: true },
    { id: 3, name: 'David Wilson', role: 'Product Manager', checked: false }
  ];

  const handlePrevMonth = () => {
    setSelectedDate(
      new Date(selectedDate.getFullYear(), selectedDate.getMonth() - 1, 1)
    );
  };

  const handleNextMonth = () => {
    setSelectedDate(
      new Date(selectedDate.getFullYear(), selectedDate.getMonth() + 1, 1)
    );
  };

  const handleDateClick = (day) => {
    setSelectedDate(
      new Date(selectedDate.getFullYear(), selectedDate.getMonth(), day)
    );
    setStep(2);
  };

  const handleTimeSlotClick = (slot) => {
    if (slot.available) {
      setSelectedTimeSlot(slot);
      setStep(3);
    }
  };

  const handleCandidateSelect = (candidate) => {
    setSelectedCandidateLocal(candidate);
    // ADDED: Pre-fill job description if candidate has one
    if (candidate.job_description) {
      setJobDescription(candidate.job_description);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  // UPDATE: Modified handleSchedule function to include job_description
  const handleSchedule = async () => {
    // Validate candidate selection
    if (!selectedCandidateLocal) {
        alert('Please select a candidate');
        return;
    }

    // If candidate doesn't have email, fetch full candidate data
    let candidateWithEmail = selectedCandidateLocal;
    
    if (!selectedCandidateLocal.email) {
        try {
            const response = await fetch(`${BACKEND_URL}/api/candidates?job_id=${selectedCandidateLocal.job_id || ''}`);
            if (response.ok) {
                const candidates = await response.json();
                candidateWithEmail = candidates.find(c => c.id === selectedCandidateLocal.id);
                
                if (!candidateWithEmail || !candidateWithEmail.email) {
                    alert('Cannot schedule interview: Candidate email not found in database.');
                    return;
                }
            }
        } catch (error) {
            console.error('Error fetching candidate details:', error);
            alert('Error fetching candidate information. Please try again.');
            return;
        }
    }

    // Get the selected interviewers
    const selectedInterviewers = interviewers.filter(interviewer => interviewer.checked);
    
    // Create a datetime from the selected date and time slot
    const hours = parseInt(selectedTimeSlot.time.split(':')[0]);
    const minutes = parseInt(selectedTimeSlot.time.split(':')[1]);
    const isPM = selectedTimeSlot.time.includes('PM');
    
    const interviewDate = new Date(selectedDate);
    interviewDate.setHours(isPM && hours !== 12 ? hours + 12 : hours);
    interviewDate.setMinutes(minutes);
    
    try {
        const response = await fetch(`${BACKEND_URL}/api/schedule-interview`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                candidate_id: candidateWithEmail.id,
                email: candidateWithEmail.email,
                date: interviewDate.toISOString(),
                time_slot: selectedTimeSlot.time,
                job_description: jobDescription || null // ADDED: Include job description
            })
        });

        const data = await response.json();
        
        if (data.success) {
            if (data.already_scheduled) {
                alert(`Interview was already scheduled for this candidate.\nInterview Link: ${data.interview_link}`);
            } else {
                // Show success message with the interview link
                const message = `Interview scheduled successfully!\n\n` +
                              `Candidate: ${candidateWithEmail.name}\n` +
                              `Email: ${candidateWithEmail.email}\n` +
                              `Interview Link: ${data.interview_link}\n` +
                              `Knowledge Base ID: ${data.knowledge_base_id}\n` +
                              `Resume Used: ${data.resume_extracted ? '✅ Yes' : '❌ No'}\n` +
                              `Job Description: ${data.job_description_used ? '✅ Provided' : '📝 Auto-generated'}\n\n` +
                              `${data.email_sent ? '✅ Email sent to candidate.' : '⚠️ Note: Email sending failed, but interview is scheduled.'}`;
                alert(message);
                
                // Copy link to clipboard
                if (navigator.clipboard && data.interview_link) {
                    navigator.clipboard.writeText(data.interview_link)
                        .then(() => console.log('Interview link copied to clipboard'))
                        .catch(err => console.error('Failed to copy link:', err));
                }
            }
            
            // Call the context function to update state if available
            if (scheduleInterview) {
                scheduleInterview(candidateWithEmail.id, interviewDate.toISOString(), selectedInterviewers);
            }
            
            navigate('/candidates');
        } else {
            alert(`Failed to schedule interview: ${data.message}`);
        }
    } catch (error) {
        console.error('Error scheduling interview:', error);
        alert('Failed to schedule interview. Please try again.');
    }
  };

  const renderDays = () => {
    const days = [];
    const weekdays = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];

    // Render weekday headers
    weekdays.forEach((day, index) => {
      days.push(
        <div key={`weekday-${index}`} className="text-center text-gray-500 text-sm py-2">
          {day}
        </div>
      );
    });

    // Empty cells for days before the first day of month
    for (let i = 0; i < firstDayOfMonth; i++) {
      days.push(<div key={`empty-${i}`} className="p-2 border border-gray-100"></div>);
    }

    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const isToday =
        new Date().getDate() === day &&
        new Date().getMonth() === selectedDate.getMonth() &&
        new Date().getFullYear() === selectedDate.getFullYear();

      const isSelected =
        selectedDate.getDate() === day &&
        selectedDate.getMonth() === selectedDate.getMonth() &&
        selectedDate.getFullYear() === selectedDate.getFullYear();

      days.push(
        <div
          key={`day-${day}`}
          className={`p-2 border border-gray-100 text-center cursor-pointer hover:bg-blue-50 ${
            isToday ? 'bg-blue-50' : ''
          } ${isSelected ? 'bg-blue-500 text-white hover:bg-blue-600' : ''}`}
          onClick={() => handleDateClick(day)}
        >
          <div className="text-sm">{day}</div>
          {day % 3 === 0 && (
            <div className="mt-1 h-1 w-1 rounded-full bg-green-500 mx-auto"></div>
          )}
        </div>
      );
    }

    return days;
  };

  const formatDate = (date) => {
    const options = { weekday: 'long', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
  };

  const renderTimeSlots = (slots) => {
    return slots.map((slot) => (
      <div
        key={slot.id}
        className={`p-3 border rounded-md mb-2 cursor-pointer flex items-center justify-between ${
          slot.available
            ? 'border-gray-200 hover:border-blue-500 hover:bg-blue-50'
            : 'border-gray-200 bg-gray-100 opacity-50 cursor-not-allowed'
        } ${selectedTimeSlot && selectedTimeSlot.id === slot.id ? 'border-blue-500 bg-blue-50' : ''}`}
        onClick={() => handleTimeSlotClick(slot)}
      >
        <div className="flex items-center">
          <Clock size={16} className="text-gray-500 mr-2" />
          <span>{slot.time}</span>
        </div>
        {!slot.available && <span className="text-xs text-gray-500">Unavailable</span>}
        {selectedTimeSlot && selectedTimeSlot.id === slot.id && (
          <CheckCircle size={16} className="text-green-500" />
        )}
      </div>
    ));
  };

  if (loading) {
    return (
      <div className="flex flex-col min-h-screen bg-gray-50">
        <Navigation />
        <main className="flex-grow p-6 flex items-center justify-center">
          <div>Loading candidates...</div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Navigation />

      {/* Main Content */}
      <main className="flex-grow p-6">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Interview Scheduler</h1>
          <div className="flex items-center space-x-3">
            <div className="relative">
              <Search size={18} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search..."
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Scheduling Process */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden mb-6">
          <div className="p-4 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between">
              <h2 className="font-medium text-gray-700">Schedule an Interview</h2>
              <div className="flex items-center">
                <div className={`flex items-center ${step >= 1 ? 'text-blue-600' : 'text-gray-400'}`}>
                  <div className={`h-6 w-6 rounded-full flex items-center justify-center border-2 ${step >= 1 ? 'border-blue-600 bg-blue-600 text-white' : 'border-gray-300'}`}>
                    1
                  </div>
                  <span className="ml-2 text-sm font-medium">Select Date</span>
                </div>
                <div className={`w-8 h-1 ${step >= 2 ? 'bg-blue-600' : 'bg-gray-200'} mx-2`}></div>
                <div className={`flex items-center ${step >= 2 ? 'text-blue-600' : 'text-gray-400'}`}>
                  <div className={`h-6 w-6 rounded-full flex items-center justify-center border-2 ${step >= 2 ? 'border-blue-600 bg-blue-600 text-white' : 'border-gray-300'}`}>
                    2
                  </div>
                  <span className="ml-2 text-sm font-medium">Select Time</span>
                </div>
                <div className={`w-8 h-1 ${step >= 3 ? 'bg-blue-600' : 'bg-gray-200'} mx-2`}></div>
                <div className={`flex items-center ${step >= 3 ? 'text-blue-600' : 'text-gray-400'}`}>
                  <div className={`h-6 w-6 rounded-full flex items-center justify-center border-2 ${step >= 3 ? 'border-blue-600 bg-blue-600 text-white' : 'border-gray-300'}`}>
                    3
                  </div>
                  <span className="ml-2 text-sm font-medium">Confirm</span>
                </div>
              </div>
            </div>
          </div>

          <div className="p-6">
            {/* Step 1: Select Date */}
            {step === 1 && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Select Interview Date</h3>
                  <div className="flex space-x-2">
                    <button
                      onClick={handlePrevMonth}
                      className="p-2 rounded-md hover:bg-gray-100"
                    >
                      <ChevronLeft size={20} />
                    </button>
                    <div className="text-lg font-medium">
                      {selectedDate.toLocaleString('default', {
                        month: 'long',
                        year: 'numeric',
                      })}
                    </div>
                    <button
                      onClick={handleNextMonth}
                      className="p-2 rounded-md hover:bg-gray-100"
                    >
                      <ChevronRight size={20} />
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-7 gap-1">{renderDays()}</div>

                <div className="mt-6 flex items-center text-sm text-gray-500">
                  <div className="flex items-center mr-4">
                    <div className="h-3 w-3 rounded-full bg-green-500 mr-2"></div>
                    <span>Available slots</span>
                  </div>
                  <div className="flex items-center">
                    <div className="h-3 w-3 rounded-full bg-blue-500 mr-2"></div>
                    <span>Selected date</span>
                  </div>
                </div>
              </div>
            )}

            {/* Step 2: Select Time */}
            {step === 2 && (
              <div>
                <button
                  onClick={handleBack}
                  className="flex items-center text-blue-600 mb-4"
                >
                  <ChevronLeft size={16} />
                  <span>Back to calendar</span>
                </button>

                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Select a time on {formatDate(selectedDate)}
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium text-gray-700 mb-3">Morning</h4>
                    {renderTimeSlots(morningSlots)}
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-700 mb-3">Afternoon</h4>
                    {renderTimeSlots(afternoonSlots)}
                  </div>
                </div>
              </div>
            )}

            {/* Step 3: Confirm */}
            {step === 3 && (
              <div>
                <button
                  onClick={handleBack}
                  className="flex items-center text-blue-600 mb-4"
                >
                  <ChevronLeft size={16} />
                  <span>Back to time selection</span>
                </button>

                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Confirm Interview Details
                </h3>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                  <div className="flex items-start">
                    <Calendar size={24} className="text-blue-600 mr-3 flex-shrink-0 mt-1" />
                    <div>
                      <h4 className="font-medium text-blue-800">Interview Summary</h4>
                      <p className="text-blue-700">
                        {formatDate(selectedDate)} at {selectedTimeSlot?.time}
                      </p>
                      <div className="mt-2 text-blue-700 text-sm">
                        Position: {selectedCandidateLocal ? selectedCandidateLocal.job_title || selectedCandidateLocal.role : 'Senior Software Engineer'}
                      </div>
                      <div className="mt-1 text-blue-700 text-sm">
                        Candidate: {selectedCandidateLocal ? selectedCandidateLocal.name : 'Please select a candidate'}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <div>
                    <h4 className="font-medium text-gray-700 mb-3">Select Candidate</h4>
                    <div className="space-y-2">
                      {candidatesList.map((candidate) => (
                        <div
                          key={candidate.id}
                          className={`p-3 border rounded-md flex items-center justify-between cursor-pointer ${
                            selectedCandidateLocal && selectedCandidateLocal.id === candidate.id
                              ? 'border-blue-500 bg-blue-50'
                              : 'border-gray-200 hover:border-blue-500 hover:bg-blue-50'
                          }`}
                          onClick={() => handleCandidateSelect(candidate)}
                        >
                          <div className="flex items-center">
                            <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white mr-3">
                              {candidate.photo ? (
                                <img
                                  src={candidate.photo}
                                  alt={candidate.name}
                                  className="w-10 h-10 rounded-full"
                                />
                              ) : (
                                candidate.name?.charAt(0) || '?'
                              )}
                            </div>
                            <div>
                              <div className="font-medium">{candidate.name || 'Unknown'}</div>
                              <div className="text-sm text-gray-500">{candidate.job_title || candidate.role || 'Position not specified'}</div>
                              {candidate.email && (
                                <div className="text-xs text-gray-400">{candidate.email}</div>
                              )}
                              {/* ADDED: Show if candidate has resume */}
                              {candidate.resume_path && (
                                <div className="text-xs text-green-600 flex items-center mt-1">
                                  <FileText size={12} className="mr-1" />
                                  Resume available
                                </div>
                              )}
                            </div>
                          </div>
                          {selectedCandidateLocal && selectedCandidateLocal.id === candidate.id && (
                            <CheckCircle size={16} className="text-green-500" />
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-700 mb-3">Interviewers</h4>
                    <div className="space-y-2">
                      {interviewers.map((interviewer) => (
                        <div
                          key={interviewer.id}
                          className="p-3 border border-gray-200 rounded-md flex items-center justify-between"
                        >
                          <div className="flex items-center">
                            <div className="w-10 h-10 rounded-full bg-gray-600 flex items-center justify-center text-white mr-3">
                              {interviewer.name.charAt(0)}
                            </div>
                            <div>
                              <div className="font-medium">{interviewer.name}</div>
                              <div className="text-sm text-gray-500">{interviewer.role}</div>
                            </div>
                          </div>
                          <input
                            type="checkbox"
                            className="h-4 w-4 text-blue-600 rounded border-gray-300"
                            checked={interviewer.checked}
                            onChange={() => {
                              // In a real app, you would update the interviewer selection state here
                              console.log(`Toggling interviewer ${interviewer.name}`);
                            }}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* ADDED: Job Description Section */}
                <div className="border-t border-gray-200 pt-4 mb-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium text-gray-700">Job Description (Optional)</h4>
                    <button
                      onClick={() => setShowJobDescriptionModal(true)}
                      className="text-blue-600 text-sm hover:underline flex items-center"
                    >
                      <FileText size={16} className="mr-1" />
                      {jobDescription ? 'Edit' : 'Add'} Job Description
                    </button>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-md">
                    <p className="text-sm text-gray-600">
                      {jobDescription ? (
                        <span>{jobDescription.substring(0, 100)}...</span>
                      ) : (
                        <span className="italic">
                          No job description provided. The system will use a generic description or candidate's profile.
                        </span>
                      )}
                    </p>
                  </div>
                </div>

                <div className="border-t border-gray-200 pt-4">
                  <h4 className="font-medium text-gray-700 mb-3">Interview Method</h4>
                  <div className="flex space-x-4">
                    <div className="flex-1 p-4 border border-gray-200 rounded-md cursor-pointer hover:border-blue-500 hover:bg-blue-50 bg-blue-50 border-blue-500">
                      <div className="flex items-center">
                        <Video size={20} className="text-blue-600 mr-3" />
                        <div>
                          <div className="font-medium">AI-Powered Video Interview</div>
                          <div className="text-sm text-gray-500">Secure interview link will be sent automatically</div>
                          <div className="text-xs text-green-600 mt-1">
                            ✓ Knowledge base will be created from resume
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="flex-1 p-4 border border-gray-200 rounded-md cursor-pointer hover:border-blue-500 hover:bg-blue-50">
                      <div className="flex items-center">
                        <MapPin size={20} className="text-gray-600 mr-3" />
                        <div>
                          <div className="font-medium">In-Person</div>
                          <div className="text-sm text-gray-500">Office location details will be shared</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-6 flex justify-end space-x-3">
                  <button
                    onClick={() => setStep(1)}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSchedule}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    disabled={!selectedCandidateLocal}
                  >
                    Schedule Interview
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* ADDED: Job Description Modal */}
      {showJobDescriptionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Add/Edit Job Description</h3>
              <button
                onClick={() => setShowJobDescriptionModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Job Description
              </label>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={10}
                placeholder={`Enter job description for ${selectedCandidateLocal?.job_title || 'the position'}...

Example:
We are seeking a talented ${selectedCandidateLocal?.job_title || 'professional'} to join our team.

Key Responsibilities:
- Develop and maintain software applications
- Collaborate with cross-functional teams
- Participate in code reviews

Requirements:
- Bachelor's degree in Computer Science or related field
- 3+ years of experience
- Strong problem-solving skills`}
              />
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowJobDescriptionModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowJobDescriptionModal(false);
                  // Job description is already saved in state
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Save Job Description
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SchedulerInterface;