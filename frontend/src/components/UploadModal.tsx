import React, { useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { claimsAPI } from '../api/claims';
import './UploadModal.css';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadComplete: () => void;
}

const UploadModal: React.FC<UploadModalProps> = ({ isOpen, onClose, onUploadComplete }) => {
  const [claimsFile, setClaimsFile] = useState<File | null>(null);
  const [technicalRulesFile, setTechnicalRulesFile] = useState<File | null>(null);
  const [medicalRulesFile, setMedicalRulesFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validationProgress, setValidationProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState<'upload' | 'validating' | 'complete'>('upload');
  const [error, setError] = useState('');
  const [jobStatus, setJobStatus] = useState<any>(null);

  const onClaimsDrop = (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setClaimsFile(acceptedFiles[0]);
      setError('');
    }
  };

  const onTechnicalRulesDrop = (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setTechnicalRulesFile(acceptedFiles[0]);
    }
  };

  const onMedicalRulesDrop = (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setMedicalRulesFile(acceptedFiles[0]);
    }
  };

  const claimsDropzone = useDropzone({
    onDrop: onClaimsDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    disabled: uploading || validating,
  });

  const technicalRulesDropzone = useDropzone({
    onDrop: onTechnicalRulesDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    disabled: uploading || validating,
  });

  const medicalRulesDropzone = useDropzone({
    onDrop: onMedicalRulesDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    disabled: uploading || validating,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!claimsFile) {
      setError('Please upload a claims file');
      return;
    }

    setUploading(true);
    setError('');
    setCurrentStep('upload');

    try {
      const formData = new FormData();
      formData.append('claims_file', claimsFile);
      if (technicalRulesFile) {
        formData.append('technical_rules_file', technicalRulesFile);
      }
      if (medicalRulesFile) {
        formData.append('medical_rules_file', medicalRulesFile);
      }

      const job = await claimsAPI.uploadFile(formData);
      setUploading(false);
      setValidating(true);
      setCurrentStep('validating');
      setJobStatus(job);

      // Poll for job status
      if (job.id) {
        pollJobStatus(job.id);
      }
    } catch (err: any) {
      console.error('Upload error:', err);
      let errorMessage = 'Upload failed';
      
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          errorMessage = err.response.data;
        } else if (err.response.data.error) {
          errorMessage = err.response.data.error;
        } else if (err.response.data.detail) {
          errorMessage = err.response.data.detail;
        }
      }
      
      setError(errorMessage);
      setUploading(false);
      setValidating(false);
      setCurrentStep('upload');
    }
  };

  const pollJobStatus = async (jobId: number) => {
    const interval = setInterval(async () => {
      try {
        const status = await claimsAPI.getJobStatus(jobId);
        setJobStatus(status);
        
        if (status.progress) {
          const percentage = status.progress.percentage || 0;
          setValidationProgress(percentage);
        }

        if (status.status === 'completed') {
          clearInterval(interval);
          setValidating(false);
          setCurrentStep('complete');
          
          // Show completion for 2 seconds, then close
          setTimeout(() => {
            onUploadComplete();
            handleClose();
          }, 2000);
        } else if (status.status === 'failed') {
          clearInterval(interval);
          setError('Validation failed. Please try again.');
          setValidating(false);
          setCurrentStep('upload');
        }
      } catch (error) {
        console.error('Failed to get job status:', error);
        clearInterval(interval);
      }
    }, 1000);

    setTimeout(() => clearInterval(interval), 300000); // Stop after 5 minutes
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const handleClose = () => {
    if (!validating && !uploading) {
      setClaimsFile(null);
      setTechnicalRulesFile(null);
      setMedicalRulesFile(null);
      setError('');
      setValidationProgress(0);
      setCurrentStep('upload');
      setJobStatus(null);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="upload-modal-overlay" onClick={handleClose}>
      <div className="upload-modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={handleClose} disabled={validating || uploading}>
          ×
        </button>

        {currentStep === 'upload' && (
          <div className="upload-step">
            <div className="modal-header">
              <h2>📤 Upload Files</h2>
              <p className="modal-description">Upload your claims file and optional rule documents</p>
            </div>
            
            <form onSubmit={handleSubmit}>
              <div className="upload-sections-grid-modal">
                <div className="upload-section-modal">
                  <div className="section-header-modal">
                    <div className="section-icon claims-icon">📊</div>
                    <div>
                      <h3>Claims File</h3>
                      <span className="required-badge">Required</span>
                    </div>
                  </div>
                  <div
                    {...claimsDropzone.getRootProps()}
                    className={`dropzone-modal ${claimsDropzone.isDragActive ? 'active' : ''} ${claimsFile ? 'has-file' : ''}`}
                  >
                    <input {...claimsDropzone.getInputProps()} />
                    {claimsFile ? (
                      <div className="file-preview-modal">
                        <div className="file-icon">📄</div>
                        <div className="file-info">
                          <p className="file-name">{claimsFile.name}</p>
                          <p className="file-size">{formatFileSize(claimsFile.size)}</p>
                        </div>
                        <button
                          type="button"
                          className="remove-file"
                          onClick={(e) => {
                            e.stopPropagation();
                            setClaimsFile(null);
                          }}
                        >
                          ×
                        </button>
                      </div>
                    ) : (
                      <div className="dropzone-content">
                        <div className="upload-icon">📤</div>
                        <p className="dropzone-text">Drag & drop Excel file</p>
                        <p className="dropzone-subtext">or click to browse</p>
                        <p className="file-types">.xlsx, .xls</p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="upload-section-modal">
                  <div className="section-header-modal">
                    <div className="section-icon technical-icon">⚙️</div>
                    <div>
                      <h3>Technical Rules</h3>
                      <span className="optional-badge">Optional</span>
                    </div>
                  </div>
                  <div
                    {...technicalRulesDropzone.getRootProps()}
                    className={`dropzone-modal ${technicalRulesDropzone.isDragActive ? 'active' : ''} ${technicalRulesFile ? 'has-file' : ''}`}
                  >
                    <input {...technicalRulesDropzone.getInputProps()} />
                    {technicalRulesFile ? (
                      <div className="file-preview-modal">
                        <div className="file-icon">📄</div>
                        <div className="file-info">
                          <p className="file-name">{technicalRulesFile.name}</p>
                          <p className="file-size">{formatFileSize(technicalRulesFile.size)}</p>
                        </div>
                        <button
                          type="button"
                          className="remove-file"
                          onClick={(e) => {
                            e.stopPropagation();
                            setTechnicalRulesFile(null);
                          }}
                        >
                          ×
                        </button>
                      </div>
                    ) : (
                      <div className="dropzone-content">
                        <div className="upload-icon">📤</div>
                        <p className="dropzone-text">Drag & drop PDF</p>
                        <p className="dropzone-subtext">or click to browse</p>
                        <p className="file-types">.pdf</p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="upload-section-modal">
                  <div className="section-header-modal">
                    <div className="section-icon medical-icon">🏥</div>
                    <div>
                      <h3>Medical Rules</h3>
                      <span className="optional-badge">Optional</span>
                    </div>
                  </div>
                  <div
                    {...medicalRulesDropzone.getRootProps()}
                    className={`dropzone-modal ${medicalRulesDropzone.isDragActive ? 'active' : ''} ${medicalRulesFile ? 'has-file' : ''}`}
                  >
                    <input {...medicalRulesDropzone.getInputProps()} />
                    {medicalRulesFile ? (
                      <div className="file-preview-modal">
                        <div className="file-icon">📄</div>
                        <div className="file-info">
                          <p className="file-name">{medicalRulesFile.name}</p>
                          <p className="file-size">{formatFileSize(medicalRulesFile.size)}</p>
                        </div>
                        <button
                          type="button"
                          className="remove-file"
                          onClick={(e) => {
                            e.stopPropagation();
                            setMedicalRulesFile(null);
                          }}
                        >
                          ×
                        </button>
                      </div>
                    ) : (
                      <div className="dropzone-content">
                        <div className="upload-icon">📤</div>
                        <p className="dropzone-text">Drag & drop PDF</p>
                        <p className="dropzone-subtext">or click to browse</p>
                        <p className="file-types">.pdf</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {error && (
                <div className="alert-message error-message">
                  <span className="alert-icon">⚠️</span>
                  <span>{error}</span>
                </div>
              )}

              <div className="submit-section-modal">
                <button type="submit" className="submit-button-modal" disabled={uploading || !claimsFile}>
                  {uploading ? (
                    <>
                      <span className="button-spinner"></span>
                      <span>Uploading...</span>
                    </>
                  ) : (
                    <>
                      <span>🚀</span>
                      <span>Validate Claims</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        )}

        {currentStep === 'validating' && (
          <ValidationAnimation 
            progress={validationProgress}
            jobStatus={jobStatus}
          />
        )}

        {currentStep === 'complete' && (
          <div className="complete-step">
            <div className="success-animation">
              <div className="success-icon">✅</div>
              <h2>Validation Complete!</h2>
              <p>Your claims have been successfully validated.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const ValidationAnimation: React.FC<{ progress: number; jobStatus: any }> = ({ progress, jobStatus }) => {
  const [animatedProgress, setAnimatedProgress] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setAnimatedProgress((prev) => {
        if (prev < progress) {
          return Math.min(prev + 1, progress);
        }
        return prev;
      });
    }, 50);
    return () => clearInterval(interval);
  }, [progress]);

  return (
    <div className="validation-animation">
      <div className="validation-patterns">
        <div className="pattern-circle circle-1"></div>
        <div className="pattern-circle circle-2"></div>
        <div className="pattern-circle circle-3"></div>
        <div className="pattern-circle circle-4"></div>
        <div className="pattern-grid"></div>
      </div>
      
      <div className="validation-content">
        <div className="validation-icon-container">
          <div className="validation-icon">⚡</div>
          <div className="pulse-ring"></div>
        </div>
        
        <h2>Validating Claims</h2>
        <p className="validation-subtitle">Analyzing your data with advanced validation rules...</p>
        
        <div className="progress-container-animated">
          <div className="progress-bar-animated">
            <div 
              className="progress-fill-animated"
              style={{ width: `${animatedProgress}%` }}
            >
              <div className="progress-shine"></div>
            </div>
          </div>
          <div className="progress-stats">
            <span className="progress-number">{Math.round(animatedProgress)}%</span>
            <span className="progress-text">
              {jobStatus?.progress?.processed || 0} of {jobStatus?.progress?.total || 0} claims
            </span>
          </div>
        </div>

        <div className="validation-steps">
          <div className={`validation-step ${animatedProgress > 20 ? 'active' : ''}`}>
            <span className="step-icon">📊</span>
            <span>Loading Rules</span>
          </div>
          <div className={`validation-step ${animatedProgress > 40 ? 'active' : ''}`}>
            <span className="step-icon">🔍</span>
            <span>Checking Claims</span>
          </div>
          <div className={`validation-step ${animatedProgress > 60 ? 'active' : ''}`}>
            <span className="step-icon">⚖️</span>
            <span>Validating Rules</span>
          </div>
          <div className={`validation-step ${animatedProgress > 80 ? 'active' : ''}`}>
            <span className="step-icon">✨</span>
            <span>Finalizing</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadModal;

