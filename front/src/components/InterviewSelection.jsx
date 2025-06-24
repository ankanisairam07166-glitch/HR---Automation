import React, { useState, useEffect } from 'react';
import { Calendar, CheckCircle, ChevronLeft, Clock, Video, Check } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';
import Navigation from './Navigation';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:5000";

const InterviewSelection = () => {
  const navigate = useNavigate();
  const { candidateId } = useParams();

  // Backend data
  const [candidate, setCandidate] = useState(null);
  const [assessment, setAssessment] = useState(null);

  // UI state
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [selectedTimeSlot, setSelectedTimeSlot] = useState(null);
  const [meetingLink, setMeetingLink] = useState('');
  const [bookingComplete, setBookingComplete] = useState(false);
  const [loading, setLoading] = useState(true);

  // Fetch candidate and assessment from backend
  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch(`${BACKEND_URL}/api/candidates`).then(res => res.json()),
      fetch(`${BACKEND_URL}/api/assessments`).then(res => res.json())
    ]).then(([candidates, assessments]) => {
      const cand = candidates.find(c => c.id === parseInt(candidateId));
      const assess = assessments.find(a => a.candidateId === parseInt(candidateId) && a.status === "Completed");
      setCandidate(cand);
      setAssessment(assess);
      setLoading(false);
    });
  }, [candidateId]);

  // Mock time slots (could be API driven)
  const timeSlots = [
    { id: 1, date: new Date(selectedDate).setHours(9, 0), time: '9:00 AM - 10:00 AM', available: true },
    { id: 2, date: new Date(selectedDate).setHours(10, 30), time: '10:30 AM - 11:30 AM', available: true },
    { id: 3, date: new Date(selectedDate).setHours(12, 0), time: '12:00 PM - 1:00 PM', available: false },
    { id: 4, date: new Date(selectedDate).setHours(14, 0), time: '2:00 PM - 3:00 PM', available: true },
    { id: 5, date: new Date(selectedDate).setHours(15, 30), time: '3:30 PM - 4:30 PM', available: true },
    { id: 6, date: new Date(selectedDate).setHours(17, 0), time: '5:00 PM - 6:00 PM', available: false },
  ];

  const getNextSevenDays = () => {
    const days = [];
    for (let i = 0; i < 7; i++) {
      const date = new Date();
      date.setDate(date.getDate() + i);
      days.push(date);
    }
    return days;
  };
  const availableDates = getNextSevenDays();

  const formatDate = (date) => new Date(date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });

  // Handle slot/date selection
  const handleDateSelect = (date) => {
    setSelectedDate(date);
    setSelectedTimeSlot(null);
  };
  const handleTimeSlotSelect = (slot) => slot.available && setSelectedTimeSlot(slot);

  // Book interview: POST to backend
  const handleBookInterview = () => {
    if (!selectedTimeSlot || !candidate) return;
    fetch(`${BACKEND_URL}/api/schedule-interview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        candidate_id: candidate.id,
        email: candidate.email,
        date: new Date(selectedTimeSlot.date).toISOString(),
        time_slot: selectedTimeSlot.time
      })
    })
    .then(res => res.json())
    .then(data => {
      setMeetingLink(data.meeting_link || '');
      setBookingComplete(true);
    });
  };

  const handleBackToAssessments = () => navigate('/assessments');

  if (loading) return <div>Loading...</div>;
  if (!candidate || !assessment) {
    return (
      <div className="flex flex-col min-h-screen bg-gray-50">
        <Navigation />
        <main className="flex-grow p-6 flex items-center justify-center">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 max-w-md w-full text-center">
            <div className="text-lg font-medium text-gray-900 mb-2">Candidate or Assessment Not Found</div>
            <p className="text-gray-500 mb-4">We couldn't find this candidate or they haven't completed an assessment.</p>
            <button 
              onClick={handleBackToAssessments}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Back to Assessments
            </button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Navigation />

      <main className="flex-grow p-6">
        <div className="max-w-3xl mx-auto">
          {/* Page Header */}
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Schedule Your Interview</h1>
            <button
              onClick={handleBackToAssessments}
              className="flex items-center text-blue-600 hover:text-blue-800"
            >
              <ChevronLeft size={16} className="mr-1" />
              Back to Assessments
            </button>
          </div>

          {/* Content */}
          {bookingComplete ? (
            <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-200">
              <div className="text-center">
                <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-green-100 text-green-600 mb-4">
                  <Check size={32} />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Interview Scheduled!</h2>
                <p className="text-gray-600 mb-6">
                  Your interview has been scheduled for {formatDate(selectedDate)} at {selectedTimeSlot.time}.
                </p>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 text-left">
                  <h3 className="text-lg font-medium text-blue-800 mb-2">Google Meet Details</h3>
                  <p className="text-blue-600 mb-2">
                    Link: <a href={meetingLink} target="_blank" rel="noopener noreferrer" className="underline">{meetingLink}</a>
                  </p>
                  <p className="text-blue-600">
                    We've also sent these details to your email: {candidate.email}
                  </p>
                </div>
                <p className="text-gray-600 mb-6">
                  Please make sure you have a stable internet connection and a quiet environment for your interview.
                </p>
                <div className="flex justify-center space-x-3">
                  <button 
                    onClick={() => navigate('/candidates')}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    Go to Dashboard
                  </button>
                  <a 
                    href={meetingLink} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Join Meeting
                  </a>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              {/* Candidate Info */}
              <div className="flex items-center mb-6 border-b border-gray-200 pb-4">
                <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center text-white flex-shrink-0">
                  {candidate.name.charAt(0)}
                </div>
                <div className="ml-4">
                  <h2 className="text-lg font-medium text-gray-900">{candidate.name}</h2>
                  <p className="text-gray-500">{candidate.role} • Assessment Score: {assessment.score}</p>
                </div>
              </div>

              <h3 className="text-lg font-medium text-gray-900 mb-4">Select a Date</h3>
              {/* Date Selection */}
              <div className="grid grid-cols-3 md:grid-cols-7 gap-2 mb-6">
                {availableDates.map((date, index) => (
                  <div
                    key={index}
                    className={`p-2 border rounded-md text-center cursor-pointer ${
                      selectedDate.toDateString() === date.toDateString() 
                        ? 'border-blue-500 bg-blue-50' 
                        : 'border-gray-200 hover:border-blue-500 hover:bg-blue-50'
                    }`}
                    onClick={() => handleDateSelect(date)}
                  >
                    <div className="text-xs text-gray-500">{date.toLocaleDateString('en-US', { weekday: 'short' })}</div>
                    <div className="text-lg font-medium">{date.getDate()}</div>
                    <div className="text-xs text-gray-500">{date.toLocaleDateString('en-US', { month: 'short' })}</div>
                  </div>
                ))}
              </div>

              <h3 className="text-lg font-medium text-gray-900 mb-4">Select a Time Slot</h3>
              {/* Time Slot Selection */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
                {timeSlots.map((slot) => (
                  <div
                    key={slot.id}
                    className={`p-3 border rounded-md cursor-pointer flex items-center justify-between ${
                      !slot.available 
                        ? 'border-gray-200 bg-gray-100 opacity-60 cursor-not-allowed' 
                        : selectedTimeSlot && selectedTimeSlot.id === slot.id
                          ? 'border-blue-500 bg-blue-50' 
                          : 'border-gray-200 hover:border-blue-500 hover:bg-blue-50'
                    }`}
                    onClick={() => handleTimeSlotSelect(slot)}
                  >
                    <div className="flex items-center">
                      <Clock size={16} className="text-gray-500 mr-2" />
                      <span>{slot.time}</span>
                    </div>
                    {!slot.available && (
                      <span className="text-xs text-gray-500">Unavailable</span>
                    )}
                    {selectedTimeSlot && selectedTimeSlot.id === slot.id && (
                      <CheckCircle size={16} className="text-green-500" />
                    )}
                  </div>
                ))}
              </div>

              {/* Interview Type */}
              <div className="mb-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Interview Method</h3>
                <div className="p-4 border border-blue-200 bg-blue-50 rounded-md flex items-start">
                  <Video size={20} className="text-blue-600 mt-1 mr-3 flex-shrink-0" />
                  <div>
                    <div className="font-medium text-blue-800">Google Meet Video Interview</div>
                    <p className="text-blue-600 text-sm mt-1">
                      Once you select a time slot and book your interview, we'll send you a Google Meet link to join at the scheduled time.
                    </p>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div className="flex justify-end">
                <button
                  onClick={handleBookInterview}
                  disabled={!selectedTimeSlot}
                  className={`px-4 py-2 rounded-md ${
                    !selectedTimeSlot
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  Book Interview
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default InterviewSelection;
