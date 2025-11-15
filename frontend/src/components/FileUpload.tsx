import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { claimsAPI } from '../api/claims';
import './FileUpload.css';

interface FileUploadProps {
  onUploadComplete: () => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onUploadComplete }) => {
  const [claimsFile, setClaimsFile] = useState<File | null>(null);
  const [technicalRulesFile, setTechnicalRulesFile] = useState<File | null>(null);
  const [medicalRulesFile, setMedicalRulesFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [jobStatus, setJobStatus] = useState<any>(null);

  const onClaimsDrop = (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setClaimsFile(acceptedFiles[0]);
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
  });

  const technicalRulesDropzone = useDropzone({
    onDrop: onTechnicalRulesDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
  });

  const medicalRulesDropzone = useDropzone({
    onDrop: onMedicalRulesDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!claimsFile) {
      setError('Please upload a claims file');
      return;
    }

    setUploading(true);
    setError('');
    setSuccess('');

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
      setSuccess('File uploaded successfully! Processing started...');
      setJobStatus(job);

      // Poll for job status
      if (job.id) {
        pollJobStatus(job.id);
      }

      // Reset form
      setClaimsFile(null);
      setTechnicalRulesFile(null);
      setMedicalRulesFile(null);
    } catch (err: any) {
      console.error('Upload error:', err);
      let errorMessage = 'Upload failed';
      
      if (err.response) {
        // Server responded with error
        if (err.response.data) {
          if (typeof err.response.data === 'string') {
            errorMessage = err.response.data;
          } else if (err.response.data.error) {
            errorMessage = err.response.data.error;
          } else if (err.response.data.detail) {
            errorMessage = err.response.data.detail;
          } else if (err.response.data.message) {
            errorMessage = err.response.data.message;
          } else {
            // Try to extract error from non_field_errors or first field error
            const data = err.response.data;
            if (data.non_field_errors && data.non_field_errors.length > 0) {
              errorMessage = data.non_field_errors[0];
            } else {
              const firstKey = Object.keys(data)[0];
              if (firstKey && Array.isArray(data[firstKey]) && data[firstKey].length > 0) {
                errorMessage = `${firstKey}: ${data[firstKey][0]}`;
              }
            }
          }
        } else {
          errorMessage = `Server error: ${err.response.status} ${err.response.statusText}`;
        }
      } else if (err.request) {
        errorMessage = 'Network error: Could not connect to server. Please check if the backend is running.';
      } else {
        errorMessage = err.message || 'Upload failed';
      }
      
      setError(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  const pollJobStatus = async (jobId: number) => {
    const interval = setInterval(async () => {
      try {
        const status = await claimsAPI.getJobStatus(jobId);
        setJobStatus(status);

        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(interval);
          if (status.status === 'completed') {
            onUploadComplete();
          }
        }
      } catch (error) {
        console.error('Failed to get job status:', error);
        clearInterval(interval);
      }
    }, 2000);

    // Stop polling after 5 minutes
    setTimeout(() => clearInterval(interval), 300000);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="file-upload-container">
      <div className="upload-header">
        <h2>Upload Files</h2>
        <p className="upload-description">Upload your claims file and optional rule documents to begin validation</p>
      </div>
      
      <form onSubmit={handleSubmit}>
        <div className="upload-sections-grid">
          <div className="upload-section">
            <div className="section-header">
              <div className="section-icon claims-icon">📊</div>
              <div>
                <h3>Claims File</h3>
                <span className="required-badge">Required</span>
              </div>
            </div>
            <div
              {...claimsDropzone.getRootProps()}
              className={`dropzone ${claimsDropzone.isDragActive ? 'active' : ''} ${claimsFile ? 'has-file' : ''}`}
            >
              <input {...claimsDropzone.getInputProps()} />
              {claimsFile ? (
                <div className="file-preview">
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
                  <p className="dropzone-text">Drag & drop an Excel file here</p>
                  <p className="dropzone-subtext">or click to browse</p>
                  <p className="file-types">Supports .xlsx, .xls</p>
                </div>
              )}
            </div>
          </div>

          <div className="upload-section">
            <div className="section-header">
              <div className="section-icon technical-icon">⚙️</div>
              <div>
                <h3>Technical Rules File</h3>
                <span className="optional-badge">Optional</span>
              </div>
            </div>
            <div
              {...technicalRulesDropzone.getRootProps()}
              className={`dropzone ${technicalRulesDropzone.isDragActive ? 'active' : ''} ${technicalRulesFile ? 'has-file' : ''}`}
            >
              <input {...technicalRulesDropzone.getInputProps()} />
              {technicalRulesFile ? (
                <div className="file-preview">
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
                  <p className="dropzone-text">Drag & drop a PDF file here</p>
                  <p className="dropzone-subtext">or click to browse</p>
                  <p className="file-types">Supports .pdf</p>
                </div>
              )}
            </div>
          </div>

          <div className="upload-section">
            <div className="section-header">
              <div className="section-icon medical-icon">🏥</div>
              <div>
                <h3>Medical Rules File</h3>
                <span className="optional-badge">Optional</span>
              </div>
            </div>
            <div
              {...medicalRulesDropzone.getRootProps()}
              className={`dropzone ${medicalRulesDropzone.isDragActive ? 'active' : ''} ${medicalRulesFile ? 'has-file' : ''}`}
            >
              <input {...medicalRulesDropzone.getInputProps()} />
              {medicalRulesFile ? (
                <div className="file-preview">
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
                  <p className="dropzone-text">Drag & drop a PDF file here</p>
                  <p className="dropzone-subtext">or click to browse</p>
                  <p className="file-types">Supports .pdf</p>
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
        
        {success && (
          <div className="alert-message success-message">
            <span className="alert-icon">✓</span>
            <span>{success}</span>
          </div>
        )}

        {jobStatus && jobStatus.status === 'processing' && (
          <div className="job-status">
            <div className="job-status-header">
              <div className="spinner"></div>
              <span>Processing your files...</span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${jobStatus.progress?.percentage || 0}%` }}
              ></div>
            </div>
            <p className="progress-text">
              Processed {jobStatus.progress?.processed || 0} of {jobStatus.progress?.total || 0} claims
              <span className="progress-percentage">({jobStatus.progress?.percentage?.toFixed(1) || 0}%)</span>
            </p>
          </div>
        )}

        <div className="submit-section">
          <button type="submit" className="submit-button" disabled={uploading || !claimsFile}>
            {uploading ? (
              <>
                <span className="button-spinner"></span>
                <span>Uploading...</span>
              </>
            ) : (
              <>
                <span>🚀</span>
                <span>Upload and Process</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default FileUpload;

