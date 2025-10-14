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
      // For now, use the existing simple API endpoint
      // This can be enhanced to support interactive steps later
      const response = await fetch(`${BACKEND_URL}/api/run_full_pipeline`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: job.id || 'new',
          job_title: job.title || 'New Position',
          job_desc: job.description || '',
          create_assessment: createAssessment
        })
      });

      const data = await response.json();
      
      if (response.ok && data.success) {
        // Simulate progress updates
        const steps = createAssessment 
          ? ['SCRAPING', 'SCREENING', 'ASSESSMENT_SETUP', 'ASSESSMENT_CREATE', 'SENDING_INVITES', 'COMPLETE']
          : ['SCRAPING', 'SCREENING', 'COMPLETE'];
        
        for (let i = 0; i < steps.length; i++) {
          const step = steps[i];
          setCurrentStep(step);
          setStatus(PIPELINE_STEPS[step]);
          setProgress(Math.min(100, (i + 1) * (100 / steps.length)));
          
          // Simulate step processing time
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
        
        setIsRunning(false);
        setStatus('Pipeline completed successfully!');
        
        setTimeout(() => {
          if (onPipelineComplete) onPipelineComplete();
          if (onClose) onClose();
        }, 2000);
      } else {
        throw new Error(data.message || 'Pipeline failed');
      }
    } catch (error) {
      console.error('Pipeline error:', error);
      setStatus(`Error: ${error.message}`);
      setIsRunning(false);
      setInteractionRequired(false);
    }
  };

  const getStepOrder = (step) => {
    const order = ['INIT', 'SCRAPING', 'SCREENING', 'ASSESSMENT_SETUP', 'ASSESSMENT_CREATE', 'SENDING_INVITES', 'COMPLETE'];
    return order.indexOf(step);
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
                    Full Pipeline with Assessment
                  </h4>
                  <p className="text-sm text-gray-500 mt-1">
                    • Scrape resumes<br/>
                    • Create Testlify assessment<br/>
                    • AI screening & scoring
                  </p>
                  <p className="text-xs text-blue-600 mt-2">
                    ~5-10 minutes
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
                    • Scrape resumes<br/>
                    • AI screening & scoring only
                  </p>
                  <p className="text-xs text-green-600 mt-2">
                    ~3-5 minutes
                  </p>
                </div>
              </div>
            </button>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <div className="flex">
              <AlertCircle className="w-5 h-5 text-yellow-600 mr-2 flex-shrink-0" />
              <div className="text-sm text-yellow-800">
                <p className="font-medium">Note:</p>
                <p>You can create assessments manually later from the Assessments page if you skip it now.</p>
              </div>
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <button 
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
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