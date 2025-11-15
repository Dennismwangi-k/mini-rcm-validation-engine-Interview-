import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import UploadModal from './UploadModal';
import Charts from './Charts';
import ClaimsTable from './ClaimsTable';
import { claimsAPI, Statistics } from '../api/claims';
import './Dashboard.css';
import './Responsive.css';

const Dashboard: React.FC = () => {
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadStatistics();
  }, []);

  const loadStatistics = async () => {
    try {
      const stats = await claimsAPI.getStatistics();
      setStatistics(stats);
    } catch (error) {
      console.error('Failed to load statistics:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const user = JSON.parse(localStorage.getItem('user') || '{}');

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>RCM Validation Engine</h1>
        <div className="header-actions">
          <div className="user-profile">
            <div className="user-avatar">
              {user.username ? user.username.charAt(0).toUpperCase() : 'U'}
            </div>
            <span className="user-name">{user.username || 'User'}</span>
          </div>
          <button className="logout-button" onClick={handleLogout}>Logout</button>
        </div>
      </header>

      <div className="dashboard-content">
        <div className="dashboard-header-actions">
          <h2 className="dashboard-title">📊 Validation Results</h2>
          <button 
            className="upload-button-main"
            onClick={() => setUploadModalOpen(true)}
            title="Upload and validate claims"
          >
            <span>📤</span>
            <span>Upload</span>
          </button>
        </div>

        <div className="results-container">
          {loading ? (
            <div className="loading">Loading statistics...</div>
          ) : statistics ? (
            <>
              <Charts statistics={statistics} />
              <ClaimsTable onRefresh={loadStatistics} />
            </>
          ) : (
            <div className="no-data">
              <div className="no-data-icon">📭</div>
              <h3>No data available</h3>
              <p>Click "Upload & Validate" to start processing claims</p>
              <button 
                className="upload-button-main"
                onClick={() => setUploadModalOpen(true)}
                title="Upload and validate claims"
              >
                <span>📤</span>
                <span>Upload</span>
              </button>
            </div>
          )}
        </div>
      </div>

      <UploadModal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        onUploadComplete={loadStatistics}
      />
    </div>
  );
};

export default Dashboard;

