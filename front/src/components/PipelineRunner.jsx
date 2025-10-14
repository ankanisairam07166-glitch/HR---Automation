import React, { useState, useEffect } from 'react';
import { Play, AlertCircle, X, FileText, Zap, CheckCircle, XCircle, ChevronRight, FileSearch, ClipboardList, Users, Settings } from 'lucide-react';

const InteractivePipelineRunner = ({ job, onPipelineStart, onPipelineComplete, onClose, showButton = false }) => {
  const [showConfirmModal, setShowConfirmModal] = useState(!showButton);
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState(null);
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);
  const [interactionRequired, setInteractionRequired] = useState(false);
  const [interactionData, setInteractionData] = useState(null);
  const [pipelineState, setPipelineState] = useState({});

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://127.0.0.1:5000';

  const PIPELINE_STEPS = {
    INIT: 'Initializing pipeline',
    SCRAPING: 'Scraping resumes',
    SCREENING: 'AI screening resumes',
    ASSESSMENT_SETUP: 'Setting up assessment',
    ASSESSMENT_CREATE: 'Creating Testlify assessment',
    SENDING_INVITES: 'Sending assessment invitations',
    COMPLETE: 'Pipeline completed'
  };

  const handleRunPipeline = () => {
    setShowConfirmModal(true);
  };

  const startPipeline = async (createAssessment) => {
    setShowConfirmModal(false);
    setIsRunning(true);
    setCurrentStep('INIT');
    setStatus(PIPELINE_STEPS.INIT);
    setProgress(5);
    
    if (onPipelineStart) onPipelineStart();

    try {
      // Step 1: Initialize Pipeline
      const initResponse = await fetch(`${BACKEND_URL}/api/pipeline/initialize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: job.id,
          job_title: job.title,
          job_desc: job.description || '',
          create_assessment: createAssessment
        }),
      });

      const initData = await initResponse.json();
      if (!initResponse.ok) throw new Error(initData.message);
      
      const sessionId = initData.session_id;
      setPipelineState({ sessionId, createAssessment });

      // Step 2: Scrape Resumes
      await scrapeResumes(sessionId);
      
      // Step 3: Screen Resumes
      await screenResumes(sessionId);
      
      // Step 4: Create Assessment if requested
      if (createAssessment) {
        await createAssessment(sessionId);
      }
      
      // Step 5: Complete Pipeline
      completePipeline(sessionId);
      
    } catch (error) {
      console.error('Pipeline error:', error);
      setStatus(`Error: ${error.message}`);
      setIsRunning(false);
      setInteractionRequired(false);
    }
  };

  const scrapeResumes = async (sessionId) => {
    setCurrentStep('SCRAPING');
    setStatus(PIPELINE_STEPS.SCRAPING);
    setProgress(20);

    // Check if user interaction needed for scraping sources
    const response = await fetch(`${BACKEND_URL}/api/pipeline/scrape/options`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
    });

    const data = await response.json();
    
    if (data.requires_interaction) {
      // Show source selection popup
      setInteractionRequired(true);
      setInteractionData({
        type: 'SCRAPING_SOURCES',
        title: 'Select Resume Sources',
        message: 'Choose which job boards to scrape resumes from:',
        options: data.options || [
          { id: 'naukri', label: 'Naukri.com', description: 'Leading Indian job portal', checked: true },
          { id: 'linkedin', label: 'LinkedIn', description: 'Professional networking site', checked: false },
          { id: 'indeed', label: 'Indeed', description: 'Global job search engine', checked: false },
          { id: 'glassdoor', label: 'Glassdoor', description: 'Jobs and company reviews', checked: false }
        ],
        callback: (selectedOptions) => {
          proceedWithScraping(sessionId, selectedOptions);
        }
      });
    } else {
      // Auto-proceed with default sources
      await proceedWithScraping(sessionId, ['naukri']);
    }
  };

  const proceedWithScraping = async (sessionId, sources) => {
    setInteractionRequired(false);
    setStatus(`${PIPELINE_STEPS.SCRAPING} from ${sources.length} source(s)`);
    
    const response = await fetch(`${BACKEND_URL}/api/pipeline/scrape/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        session_id: sessionId,
        sources: sources
      }),
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.message);
    
    setProgress(40);
    setStatus(`Scraped ${data.resumes_count || 0} resumes`);
  };

  const screenResumes = async (sessionId) => {
    setCurrentStep('SCREENING');
    setStatus(PIPELINE_STEPS.SCREENING);
    setProgress(50);

    const response = await fetch(`${BACKEND_URL}/api/pipeline/screen`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.message);
    
    setProgress(60);
    setStatus(`Screened ${data.screened_count || 0} candidates`);
  };

  const createAssessment = async (sessionId) => {
    setCurrentStep('ASSESSMENT_SETUP');
    setStatus(PIPELINE_STEPS.ASSESSMENT_SETUP);
    setProgress(70);

    // Check for assessment options
    const response = await fetch(`${BACKEND_URL}/api/pipeline/assessment/options`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        session_id: sessionId,
        job_id: job.id
      }),
    });

    const data = await response.json();
    
    if (data.requires_interaction) {
      // Show assessment type selection popup
      setInteractionRequired(true);
      setInteractionData({
        type: 'ASSESSMENT_TYPE',
        title: 'Select Assessment Type',
        message: 'Choose the type of assessment to create:',
        options: data.options || [
          { 
            id: 'technical', 
            label: 'Technical Assessment',
            description: 'Coding challenges and technical questions',
            duration: '90 minutes',
            questions: '20-25 questions'
          },
          { 
            id: 'aptitude', 
            label: 'Aptitude Test',
            description: 'Logical reasoning and problem solving',
            duration: '60 minutes',
            questions: '30-35 questions'
          },
          { 
            id: 'combined', 
            label: 'Combined Assessment',
            description: 'Technical + Aptitude + Domain specific',
            duration: '120 minutes',
            questions: '40-50 questions'
          },
          { 
            id: 'custom', 
            label: 'Custom Assessment',
            description: 'Create your own custom assessment',
            duration: 'Variable',
            questions: 'Customizable'
          }
        ],
        callback: (selectedType) => {
          proceedWithAssessmentCreation(sessionId, selectedType);
        }
      });
    } else {
      // Auto-create with default type
      await proceedWithAssessmentCreation(sessionId, 'technical');
    }
  };

  const proceedWithAssessmentCreation = async (sessionId, assessmentType) => {
    setInteractionRequired(false);
    setCurrentStep('ASSESSMENT_CREATE');
    setStatus(`Creating ${assessmentType} assessment...`);
    setProgress(80);
    
    const response = await fetch(`${BACKEND_URL}/api/pipeline/assessment/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        session_id: sessionId,
        assessment_type: assessmentType,
        job_id: job.id
      }),
    });

    const data = await response.json();
    
    if (data.requires_difficulty_selection) {
      // Show difficulty selection
      setInteractionRequired(true);
      setInteractionData({
        type: 'ASSESSMENT_DIFFICULTY',
        title: 'Select Assessment Difficulty',
        message: 'Choose the difficulty level for the assessment:',
        options: [
          { id: 'easy', label: 'Easy', description: 'Entry level positions' },
          { id: 'medium', label: 'Medium', description: 'Mid-level positions' },
          { id: 'hard', label: 'Hard', description: 'Senior positions' },
          { id: 'mixed', label: 'Mixed', description: 'Combination of all levels' }
        ],
        callback: (difficulty) => {
          finalizeAssessment(sessionId, assessmentType, difficulty);
        }
      });
    } else {
      await finalizeAssessment(sessionId, assessmentType, 'medium');
    }
  };

  const finalizeAssessment = async (sessionId, assessmentType, difficulty) => {
    setInteractionRequired(false);
    setStatus(`Finalizing ${assessmentType} assessment (${difficulty} level)...`);
    
    const response = await fetch(`${BACKEND_URL}/api/pipeline/assessment/finalize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        session_id: sessionId,
        assessment_type: assessmentType,
        difficulty: difficulty
      }),
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.message);
    
    setProgress(90);
    setStatus(`Assessment created: ${data.assessment_id}`);
    
    // Send invitations
    await sendInvitations(sessionId, data.assessment_id);
  };

  const sendInvitations = async (sessionId, assessmentId) => {
    setCurrentStep('SENDING_INVITES');
    setStatus(PIPELINE_STEPS.SENDING_INVITES);
    setProgress(95);
    
    const response = await fetch(`${BACKEND_URL}/api/pipeline/invitations/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        session_id: sessionId,
        assessment_id: assessmentId
      }),
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.message);
    
    setStatus(`Sent ${data.invitations_sent || 0} assessment invitations`);
  };

  const completePipeline = (sessionId) => {
    setCurrentStep('COMPLETE');
    setStatus(PIPELINE_STEPS.COMPLETE);
    setProgress(100);
    setIsRunning(false);
    
    setTimeout(() => {
      if (onPipelineComplete) onPipelineComplete();
      if (onClose) onClose();
    }, 2000);
  };

  // Interaction Modal Component
  const InteractionModal = () => {
    const [selectedOptions, setSelectedOptions] = useState([]);
    const [selectedSingle, setSelectedSingle] = useState(null);

    useEffect(() => {
      if (interactionData?.options) {
        if (interactionData.type === 'SCRAPING_SOURCES') {
          // Multi-select for sources
          const defaultSelected = interactionData.options
            .filter(opt => opt.checked)
            .map(opt => opt.id);
          setSelectedOptions(defaultSelected);
        }
      }
    }, [interactionData]);

    const handleMultiSelect = (optionId) => {
      setSelectedOptions(prev => 
        prev.includes(optionId)
          ? prev.filter(id => id !== optionId)
          : [...prev, optionId]
      );
    };

    const handleSingleSelect = (optionId) => {
      setSelectedSingle(optionId);
    };

    const handleProceed = () => {
      if (interactionData.type === 'SCRAPING_SOURCES') {
        interactionData.callback(selectedOptions);
      } else {
        interactionData.callback(selectedSingle);
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {interactionData.title}
          </h3>
          <p className="text-gray-600 mb-6">{interactionData.message}</p>

          <div className="space-y-3 mb-6">
            {interactionData.options.map(option => (
              <div
                key={option.id}
                onClick={() => {
                  if (interactionData.type === 'SCRAPING_SOURCES') {
                    handleMultiSelect(option.id);
                  } else {
                    handleSingleSelect(option.id);
                  }
                }}
                className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  (interactionData.type === 'SCRAPING_SOURCES' && selectedOptions.includes(option.id)) ||
                  (interactionData.type !== 'SCRAPING_SOURCES' && selectedSingle === option.id)
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-start">
                  {interactionData.type === 'SCRAPING_SOURCES' ? (
                    <input
                      type="checkbox"
                      checked={selectedOptions.includes(option.id)}
                      onChange={() => {}}
                      className="mt-1 mr-3"
                    />
                  ) : (
                    <input
                      type="radio"
                      checked={selectedSingle === option.id}
                      onChange={() => {}}
                      className="mt-1 mr-3"
                    />
                  )}
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{option.label}</h4>
                    <p className="text-sm text-gray-500 mt-1">{option.description}</p>
                    {option.duration && (
                      <div className="mt-2 flex space-x-4 text-xs text-gray-500">
                        <span>Duration: {option.duration}</span>
                        {option.questions && <span>Questions: {option.questions}</span>}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end space-x-3">
            <button
              onClick={() => {
                setInteractionRequired(false);
                setIsRunning(false);
                setStatus('Pipeline cancelled by user');
              }}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel Pipeline
            </button>
            <button
              onClick={handleProceed}
              disabled={
                (interactionData.type === 'SCRAPING_SOURCES' && selectedOptions.length === 0) ||
                (interactionData.type !== 'SCRAPING_SOURCES' && !selectedSingle)
              }
              className={`px-4 py-2 rounded-lg ${
                ((interactionData.type === 'SCRAPING_SOURCES' && selectedOptions.length > 0) ||
                (interactionData.type !== 'SCRAPING_SOURCES' && selectedSingle))
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              Continue
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Pipeline Progress Display
  const PipelineProgress = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Pipeline in Progress
        </h3>
        
        <div className="space-y-4">
          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div 
              className="bg-blue-600 h-3 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          
          {/* Current Status */}
          <div className="flex items-center">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-3"></div>
            <span className="text-gray-700">{status}</span>
          </div>
          
          {/* Steps Progress */}
          <div className="space-y-2 mt-4">
            {Object.entries(PIPELINE_STEPS).map(([key, label]) => {
              const isCompleted = getStepOrder(key) < getStepOrder(currentStep);
              const isCurrent = key === currentStep;
              
              return (
                <div key={key} className="flex items-center">
                  {isCompleted ? (
                    <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                  ) : isCurrent ? (
                    <div className="w-5 h-5 border-2 border-blue-600 rounded-full mr-2 animate-pulse" />
                  ) : (
                    <div className="w-5 h-5 border-2 border-gray-300 rounded-full mr-2" />
                  )}
                  <span className={`text-sm ${
                    isCompleted ? 'text-green-600' : 
                    isCurrent ? 'text-blue-600 font-medium' : 
                    'text-gray-400'
                  }`}>
                    {label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
        
        {!interactionRequired && (
          <div className="mt-6 text-center">
            <button
              onClick={() => {
                setIsRunning(false);
                setStatus('Pipeline cancelled');
                if (onClose) onClose();
              }}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Cancel Pipeline
            </button>
          </div>
        )}
      </div>
    </div>
  );

  const getStepOrder = (step) => {
    const order = ['INIT', 'SCRAPING', 'SCREENING', 'ASSESSMENT_SETUP', 'ASSESSMENT_CREATE', 'SENDING_INVITES', 'COMPLETE'];
    return order.indexOf(step);
  };

  // Initial Configuration Modal
  if (showConfirmModal) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Configure Pipeline
            </h3>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="mb-6">
            <p className="text-gray-600 mb-4">
              Choose how you want to run the recruitment pipeline:
            </p>
            <div className="bg-gray-50 p-3 rounded-lg">
              <p className="font-medium text-gray-900">{job.title}</p>
              <p className="text-sm text-gray-500">{job.location}</p>
            </div>
          </div>

          <div className="space-y-3 mb-6">
            <button
              onClick={() => startPipeline(true)}
              className="w-full p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all group"
            >
              <div className="flex items-start">
                <FileText className="w-5 h-5 text-blue-600 mt-0.5 mr-3" />
                <div className="text-left flex-1">
                  <h4 className="font-medium text-gray-900 group-hover:text-blue-600">
                    Full Interactive Pipeline
                  </h4>
                  <p className="text-sm text-gray-500 mt-1">
                    • Choose resume sources<br/>
                    • Select assessment type<br/>
                    • Configure difficulty level
                  </p>
                </div>
              </div>
            </button>

            <button
              onClick={() => startPipeline(false)}
              className="w-full p-4 border-2 border-gray-200 rounded-lg hover:border-green-500 hover:bg-green-50 transition-all group"
            >
              <div className="flex items-start">
                <Zap className="w-5 h-5 text-green-600 mt-0.5 mr-3" />
                <div className="text-left flex-1">
                  <h4 className="font-medium text-gray-900 group-hover:text-green-600">
                    Quick Pipeline (No Assessment)
                  </h4>
                  <p className="text-sm text-gray-500 mt-1">
                    • Auto-select best sources<br/>
                    • Skip assessment creation
                  </p>
                </div>
              </div>
            </button>
          </div>

          <button onClick={onClose} className="w-full px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
            Cancel
          </button>
        </div>
      </div>
    );
  }

  // Show interaction modal when required
  if (interactionRequired && interactionData) {
    return <InteractionModal />;
  }

  // Show progress when running
  if (isRunning) {
    return <PipelineProgress />;
  }

  // Button mode
  if (showButton) {
    return (
      <button
        onClick={handleRunPipeline}
        disabled={isRunning}
        className={`flex items-center px-4 py-2 rounded-lg ${
          isRunning 
            ? 'bg-gray-300 cursor-not-allowed' 
            : 'bg-blue-600 hover:bg-blue-700 text-white'
        }`}
      >
        <Play className="w-4 h-4 mr-2" />
        Run Pipeline
      </button>
    );
  }

  return null;
};

export default InteractivePipelineRunner;