import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import FileUpload from './FileUpload';
import Charts from './Charts';
import ClaimsTable from './ClaimsTable';
import { claimsAPI, Statistics } from '../api/claims';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'upload' | 'results'>('upload');
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
          <span>Welcome, {user.username}</span>
          <button onClick={handleLogout}>Logout</button>
        </div>
      </header>

      <div className="dashboard-content">
        <div className="tabs-wrapper">
          <div className={`tabs ${activeTab === 'results' ? 'results-active' : ''}`}>
            <button
              className={activeTab === 'upload' ? 'active' : ''}
              onClick={() => setActiveTab('upload')}
            >
              Upload Files
            </button>
            <button
              className={activeTab === 'results' ? 'active' : ''}
              onClick={() => setActiveTab('results')}
            >
              Results
            </button>
          </div>
        </div>

        {activeTab === 'upload' && (
          <FileUpload onUploadComplete={loadStatistics} />
        )}

        {activeTab === 'results' && (
          <div className="results-container">
            {loading ? (
              <div className="loading">Loading statistics...</div>
            ) : statistics ? (
              <>
                <Charts statistics={statistics} />
                <ClaimsTable onRefresh={loadStatistics} />
              </>
            ) : (
              <div className="no-data">No data available. Please upload a claims file.</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;

