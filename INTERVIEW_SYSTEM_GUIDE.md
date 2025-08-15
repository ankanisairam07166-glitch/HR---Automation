# Complete Interview Recording and Storage System Guide

## Overview

This system provides a complete interview management solution that includes:

1. **Interview Recording** - Full video/audio recording of interviews
2. **Question Tracking** - Track all questions asked by the avatar
3. **Answer Storage** - Store all candidate responses with metadata
4. **AI Analysis** - Automatic scoring and feedback generation
5. **Database Storage** - Complete persistence of all interview data

## System Architecture

### Database Schema

The system extends the `Candidate` model with comprehensive interview fields:

```python
# Interview Recording and Session Management
interview_session_id = Column(String(200))  # Unique session identifier
interview_recording_file = Column(String(500))  # Local recording file path
interview_recording_duration = Column(Integer)  # Duration in seconds
interview_recording_size = Column(Integer)  # File size in bytes
interview_recording_format = Column(String(50))  # mp4, webm, etc.
interview_recording_quality = Column(String(50))  # HD, SD, etc.

# Interview Questions and Answers
interview_questions_asked = Column(Text)  # JSON array of questions asked by avatar
interview_answers_given = Column(Text)  # JSON array of candidate answers
interview_question_timestamps = Column(Text)  # JSON array of question timestamps
interview_answer_timestamps = Column(Text)  # JSON array of answer timestamps
interview_total_questions = Column(Integer, default=0)  # Total questions asked
interview_answered_questions = Column(Integer, default=0)  # Questions answered

# Interview AI Analysis
interview_ai_questions_analysis = Column(Text)  # AI analysis of each question/answer
interview_ai_overall_feedback = Column(Text)  # Overall AI feedback
interview_ai_technical_score = Column(Float)  # Technical skills score (0-100)
interview_ai_communication_score = Column(Float)  # Communication score (0-100)
interview_ai_problem_solving_score = Column(Float)  # Problem solving score (0-100)
interview_ai_cultural_fit_score = Column(Float)  # Cultural fit score (0-100)

# Interview Session Details
interview_browser_info = Column(String(500))  # Browser and device info
interview_network_quality = Column(String(100))  # Network quality during interview
interview_technical_issues = Column(Text)  # Any technical issues encountered
interview_session_logs = Column(Text)  # Detailed session logs
interview_avatar_used = Column(String(100))  # Which avatar was used
interview_avatar_settings = Column(Text)  # Avatar configuration used

# Interview Status Tracking
interview_recording_status = Column(String(50))  # not_started/recording/completed/failed
interview_processing_status = Column(String(50))  # pending/processing/completed/failed
interview_ai_analysis_status = Column(String(50))  # pending/processing/completed/failed
interview_final_status = Column(String(50))  # passed/failed/needs_review
```

## API Endpoints

### 1. Start Interview Session

**Endpoint:** `POST /api/interview/session/start`

**Purpose:** Start a new interview session with recording

**Request Body:**
```json
{
  "interview_token": "uuid-of-interview",
  "recording_config": {
    "format": "webm",
    "quality": "HD",
    "audio": true,
    "video": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "session-uuid",
  "recording_started": true,
  "message": "Interview session started successfully"
}
```

### 2. Add Interview Question

**Endpoint:** `POST /api/interview/question/add`

**Purpose:** Track a question asked by the avatar

**Request Body:**
```json
{
  "session_id": "session-uuid",
  "question_data": {
    "text": "Tell me about your experience with Python programming.",
    "type": "technical",
    "avatar": "default",
    "keywords": ["python", "programming", "experience"],
    "difficulty": "medium"
  }
}
```

**Response:**
```json
{
  "success": true,
  "question_id": "question-uuid",
  "message": "Question added successfully"
}
```

### 3. Add Interview Answer

**Endpoint:** `POST /api/interview/answer/add`

**Purpose:** Store a candidate's answer to a question

**Request Body:**
```json
{
  "session_id": "session-uuid",
  "question_id": "question-uuid",
  "answer_data": {
    "text": "I have been working with Python for over 3 years...",
    "duration": 45,
    "audio_quality": "excellent",
    "confidence": 0.9
  }
}
```

**Response:**
```json
{
  "success": true,
  "answer_id": "answer-uuid",
  "message": "Answer added successfully"
}
```

### 4. End Interview Session

**Endpoint:** `POST /api/interview/session/end`

**Purpose:** End the interview session and start AI analysis

**Request Body:**
```json
{
  "session_id": "session-uuid"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Interview session ended successfully. Analysis started."
}
```

### 5. Get Interview Analysis

**Endpoint:** `GET /api/interview/analysis/{candidate_id}`

**Purpose:** Retrieve AI analysis results

**Response:**
```json
{
  "success": true,
  "candidate_id": 123,
  "analysis": {
    "technical_score": 85.5,
    "communication_score": 78.2,
    "problem_solving_score": 68.4,
    "cultural_fit_score": 70.4,
    "overall_score": 75.6,
    "overall_feedback": "Good interview performance. Shows potential with some areas for improvement.",
    "question_analysis": [...],
    "analysis_status": "completed",
    "final_status": "passed"
  }
}
```

### 6. Get Interview Recording Info

**Endpoint:** `GET /api/interview/recording/{candidate_id}`

**Purpose:** Get recording information

**Response:**
```json
{
  "success": true,
  "candidate_id": 123,
  "recording_info": {
    "recording_file": "recordings/interview_session_123_1234567890.webm",
    "recording_duration": 1800,
    "recording_size": 52428800,
    "recording_format": "webm",
    "recording_quality": "HD",
    "recording_status": "completed",
    "session_id": "session-uuid",
    "started_at": "2024-01-15T10:00:00Z",
    "completed_at": "2024-01-15T10:30:00Z"
  }
}
```

### 7. Get Session Data

**Endpoint:** `GET /api/interview/session/{session_id}`

**Purpose:** Get complete session data including all questions and answers

**Response:**
```json
{
  "success": true,
  "session_data": {
    "session_id": "session-uuid",
    "candidate_id": 123,
    "interview_token": "interview-uuid",
    "start_time": "2024-01-15T10:00:00Z",
    "end_time": "2024-01-15T10:30:00Z",
    "duration_seconds": 1800,
    "questions": [...],
    "answers": [...],
    "recording_file": "recordings/interview_session_123_1234567890.webm",
    "status": "completed",
    "technical_issues": [],
    "session_logs": [...]
  }
}
```

## Usage Examples

### Frontend Integration

```javascript
// Start interview session
async function startInterview(interviewToken) {
  const response = await fetch('/api/interview/session/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      interview_token: interviewToken,
      recording_config: {
        format: 'webm',
        quality: 'HD',
        audio: true,
        video: true
      }
    })
  });
  
  const result = await response.json();
  return result.session_id;
}

// Add question when avatar asks
async function addQuestion(sessionId, questionText, questionType) {
  const response = await fetch('/api/interview/question/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      question_data: {
        text: questionText,
        type: questionType,
        avatar: 'default',
        keywords: [],
        difficulty: 'medium'
      }
    })
  });
  
  const result = await response.json();
  return result.question_id;
}

// Add answer when candidate responds
async function addAnswer(sessionId, questionId, answerText, duration) {
  const response = await fetch('/api/interview/answer/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      question_id: questionId,
      answer_data: {
        text: answerText,
        duration: duration,
        audio_quality: 'good',
        confidence: 0.8
      }
    })
  });
  
  const result = await response.json();
  return result.answer_id;
}

// End interview session
async function endInterview(sessionId) {
  const response = await fetch('/api/interview/session/end', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId
    })
  });
  
  const result = await response.json();
  return result.success;
}
```

### Python Integration

```python
import requests

# Start interview session
def start_interview_session(interview_token):
    response = requests.post('http://localhost:5000/api/interview/session/start', json={
        'interview_token': interview_token,
        'recording_config': {
            'format': 'webm',
            'quality': 'HD',
            'audio': True,
            'video': True
        }
    })
    return response.json()['session_id']

# Add question
def add_question(session_id, question_text, question_type='general'):
    response = requests.post('http://localhost:5000/api/interview/question/add', json={
        'session_id': session_id,
        'question_data': {
            'text': question_text,
            'type': question_type,
            'avatar': 'default',
            'keywords': [],
            'difficulty': 'medium'
        }
    })
    return response.json()['question_id']

# Add answer
def add_answer(session_id, question_id, answer_text, duration=0):
    response = requests.post('http://localhost:5000/api/interview/answer/add', json={
        'session_id': session_id,
        'question_id': question_id,
        'answer_data': {
            'text': answer_text,
            'duration': duration,
            'audio_quality': 'good',
            'confidence': 0.8
        }
    })
    return response.json()['answer_id']

# End session
def end_interview_session(session_id):
    response = requests.post('http://localhost:5000/api/interview/session/end', json={
        'session_id': session_id
    })
    return response.json()['success']

# Get analysis results
def get_interview_analysis(candidate_id):
    response = requests.get(f'http://localhost:5000/api/interview/analysis/{candidate_id}')
    return response.json()['analysis']
```

## AI Analysis Features

The system provides comprehensive AI analysis including:

1. **Technical Score** - Assessment of technical knowledge and skills
2. **Communication Score** - Evaluation of communication clarity and effectiveness
3. **Problem Solving Score** - Analysis of problem-solving approach and methodology
4. **Cultural Fit Score** - Assessment of alignment with company culture
5. **Overall Score** - Combined weighted score from all categories
6. **Question-Level Analysis** - Detailed feedback for each question-answer pair
7. **Overall Feedback** - Comprehensive summary and recommendations

## Recording Features

The recording system supports:

1. **Multiple Formats** - WebM, MP4, and other formats
2. **Quality Settings** - HD, SD, and custom quality options
3. **Audio/Video Control** - Separate control for audio and video recording
4. **File Management** - Automatic file naming and organization
5. **Metadata Storage** - Duration, size, format, and quality information

## Testing the System

Use the provided test script to verify the complete system:

```bash
python test_interview_recording_system.py
```

This script will:
1. Find a candidate with a scheduled interview
2. Start an interview session
3. Simulate questions and answers
4. End the session
5. Wait for AI analysis
6. Display all results

## Database Migration

To add the new interview fields to your existing database:

```python
from db import add_interview_automation_fields

# Run migration
add_interview_automation_fields()
```

## Security Considerations

1. **Session Management** - Each interview session has a unique ID
2. **Token Validation** - Interview tokens are validated for each request
3. **Rate Limiting** - API endpoints have rate limiting to prevent abuse
4. **Data Privacy** - Interview recordings and data are stored securely
5. **Access Control** - Only authorized users can access interview data

## Troubleshooting

### Common Issues

1. **Session Not Found** - Ensure the session_id is correct and the session exists
2. **Recording Failed** - Check recording configuration and file permissions
3. **Analysis Not Complete** - Wait for background processing to complete
4. **Database Errors** - Verify database connection and schema

### Logs

Check the application logs for detailed error information:

```bash
tail -f logs/talentflow.log
```

## Support

For technical support or questions about the interview system, please refer to the system documentation or contact the development team. 