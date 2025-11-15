import React, { useState, useEffect } from 'react';
import { claimsAPI, Claim } from '../api/claims';
import './ClaimsTable.css';
import '../components/Responsive.css';

interface ClaimsTableProps {
  onRefresh: () => void;
}

const ClaimsTable: React.FC<ClaimsTableProps> = ({ onRefresh }) => {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);
  const [revalidating, setRevalidating] = useState(false);
  const [revalidateMessage, setRevalidateMessage] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({
    status: '',
    error_type: '',
  });

  useEffect(() => {
    loadClaims();
  }, [page, filters]);

  const loadClaims = async () => {
    setLoading(true);
    try {
      const params: any = { page };
      if (filters.status) params.status = filters.status;
      if (filters.error_type) params.error_type = filters.error_type;

      const response = await claimsAPI.getClaims(params);
      console.log('Claims API Response:', response); // Debug log
      
      // Handle both paginated and non-paginated responses
      let claimsData: Claim[] = [];
      
      if (Array.isArray(response)) {
        claimsData = response;
        setTotalPages(1);
      } else if (response.results && Array.isArray(response.results)) {
        claimsData = response.results;
        setTotalPages(Math.ceil((response.count || response.results.length) / 100));
      } else if (response && typeof response === 'object') {
        // Try to extract claims from various possible response formats
        const possibleKeys = ['data', 'claims', 'items'];
        for (const key of possibleKeys) {
          if (Array.isArray(response[key])) {
            claimsData = response[key];
            break;
          }
        }
        setTotalPages(1);
      }
      
      // Ensure paid_amount_aed is a number
      claimsData = claimsData.map(claim => ({
        ...claim,
        paid_amount_aed: typeof claim.paid_amount_aed === 'string' 
          ? parseFloat(claim.paid_amount_aed) 
          : claim.paid_amount_aed || 0
      }));
      
      setClaims(claimsData);
      console.log('Processed claims:', claimsData.length, claimsData);
    } catch (error) {
      console.error('Failed to load claims:', error);
      setClaims([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRevalidate = async () => {
    if (!window.confirm('Are you sure you want to revalidate all claims? This will update all validation results with current rules.')) {
      return;
    }

    setRevalidating(true);
    setRevalidateMessage('');
    
    try {
      const result = await claimsAPI.revalidateAll();
      
      if (result.status === 'completed') {
        setRevalidateMessage(`✅ Revalidation completed! ${result.processed} claims processed, ${result.validated} validated, ${result.errors} errors.`);
        
        // Reload claims after a short delay
        setTimeout(() => {
          loadClaims();
          onRefresh();
        }, 1000);
      } else if (result.status === 'processing') {
        setRevalidateMessage(`🔄 Revalidation started! Processing ${result.total} claims...`);
        
        // Poll for completion (simple polling for now)
        const checkInterval = setInterval(async () => {
          try {
            // Check if claims have changed by reloading
            await loadClaims();
            onRefresh();
            
            // After a delay, stop polling
            setTimeout(() => {
              clearInterval(checkInterval);
              setRevalidateMessage('✅ Revalidation completed!');
              setRevalidating(false);
            }, 5000);
          } catch (error) {
            console.error('Failed to check revalidation status:', error);
          }
        }, 2000);
      }
    } catch (error: any) {
      console.error('Revalidation error:', error);
      setRevalidateMessage(`❌ Error: ${error.response?.data?.detail || error.message || 'Failed to revalidate claims'}`);
    } finally {
      setTimeout(() => {
        setRevalidating(false);
      }, 2000);
    }
  };

  const getErrorTypeBadge = (errorType: string) => {
    const classes: { [key: string]: string } = {
      no_error: 'badge-success',
      medical_error: 'badge-warning',
      technical_error: 'badge-danger',
      both: 'badge-danger',
    };
    return classes[errorType] || 'badge-secondary';
  };

  const getStatusBadge = (status: string) => {
    return status === 'validated' ? 'badge-success' : 'badge-danger';
  };

  const formatStatus = (status: string) => {
    const statusMap: { [key: string]: string } = {
      'validated': 'Validated',
      'not_validated': 'Not Validated',
    };
    return statusMap[status] || status;
  };

  const formatErrorType = (errorType: string) => {
    const errorMap: { [key: string]: string } = {
      'no_error': 'No Error',
      'medical_error': 'Medical Error',
      'technical_error': 'Technical Error',
      'both': 'Both',
    };
    return errorMap[errorType] || errorType;
  };

  if (loading) {
    return <div className="loading">Loading claims...</div>;
  }

  return (
    <div className="claims-table-container">
      <div className="table-header">
        <h2>Claims Details</h2>
        <div className="filters">
          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          >
            <option value="">All Statuses</option>
            <option value="validated">Validated</option>
            <option value="not_validated">Not Validated</option>
          </select>
          <select
            value={filters.error_type}
            onChange={(e) => setFilters({ ...filters, error_type: e.target.value })}
          >
            <option value="">All Error Types</option>
            <option value="no_error">No Error</option>
            <option value="medical_error">Medical Error</option>
            <option value="technical_error">Technical Error</option>
            <option value="both">Both</option>
          </select>
          <button onClick={loadClaims} title="Refresh claims">
            <span>🔄</span>
            <span>Refresh</span>
          </button>
          <button 
            onClick={handleRevalidate} 
            disabled={revalidating}
            className="revalidate-button"
            title="Revalidate all claims with current rules"
          >
            {revalidating ? (
              <>
                <span className="button-spinner"></span>
                <span>Revalidate</span>
              </>
            ) : (
              <>
                <span>🔄</span>
                <span>Revalidate</span>
              </>
            )}
          </button>
        </div>
      </div>

      {revalidateMessage && (
        <div className={`alert-message ${revalidateMessage.includes('✅') ? 'success-message' : revalidateMessage.includes('❌') ? 'error-message' : 'info-message'}`}>
          <span className="alert-icon">{revalidateMessage.includes('✅') ? '✅' : revalidateMessage.includes('❌') ? '❌' : '🔄'}</span>
          <span>{revalidateMessage}</span>
        </div>
      )}

      <div className="table-wrapper">
        <table className="claims-table">
          <thead>
            <tr>
              <th>Claim ID</th>
              <th>Service Code</th>
              <th>Status</th>
              <th>Error Type</th>
              <th>Paid Amount (AED)</th>
              <th>Validated By</th>
              <th>Error Explanation</th>
              <th>Recommended Action</th>
            </tr>
          </thead>
          <tbody>
            {claims.length === 0 ? (
              <tr>
                <td colSpan={8} className="no-data">
                  No claims found
                </td>
              </tr>
            ) : (
              claims.map((claim) => (
                <tr key={claim.id}>
                  <td>{claim.claim_id}</td>
                  <td>{claim.service_code}</td>
                  <td>
                    <span className={`badge ${getStatusBadge(claim.status)}`}>
                      {formatStatus(claim.status)}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${getErrorTypeBadge(claim.error_type)}`}>
                      {formatErrorType(claim.error_type)}
                    </span>
                  </td>
                  <td>{typeof claim.paid_amount_aed === 'number' 
                    ? claim.paid_amount_aed.toFixed(2) 
                    : parseFloat(claim.paid_amount_aed || '0').toFixed(2)}</td>
                  <td>
                    <div className="validator-info">
                      {claim.validated_by_username ? (
                        <>
                          <span className="validator-avatar">
                            {claim.validated_by_username.charAt(0).toUpperCase()}
                          </span>
                          <span className="validator-name">{claim.validated_by_username}</span>
                        </>
                      ) : (
                        <span className="validator-name">System</span>
                      )}
                    </div>
                  </td>
                  <td className="explanation-cell">
                    {claim.error_explanation ? (
                      <div style={{ whiteSpace: 'pre-line' }}>
                        {claim.error_explanation}
                      </div>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td className="action-cell">
                    {claim.recommended_action ? (
                      <div style={{ whiteSpace: 'pre-line' }}>
                        {claim.recommended_action}
                      </div>
                    ) : (
                      '-'
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button
            onClick={() => setPage(page - 1)}
            disabled={page === 1}
          >
            Previous
          </button>
          <span>
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={page === totalPages}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default ClaimsTable;

