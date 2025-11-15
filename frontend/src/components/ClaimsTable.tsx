import React, { useState, useEffect } from 'react';
import { claimsAPI, Claim } from '../api/claims';
import './ClaimsTable.css';

interface ClaimsTableProps {
  onRefresh: () => void;
}

const ClaimsTable: React.FC<ClaimsTableProps> = ({ onRefresh }) => {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);
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
      setClaims(response.results || response);
      if (response.count) {
        setTotalPages(Math.ceil(response.count / 100));
      }
    } catch (error) {
      console.error('Failed to load claims:', error);
    } finally {
      setLoading(false);
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
          <button onClick={loadClaims}>Refresh</button>
        </div>
      </div>

      <div className="table-wrapper">
        <table className="claims-table">
          <thead>
            <tr>
              <th>Claim ID</th>
              <th>Service Code</th>
              <th>Status</th>
              <th>Error Type</th>
              <th>Paid Amount (AED)</th>
              <th>Error Explanation</th>
              <th>Recommended Action</th>
            </tr>
          </thead>
          <tbody>
            {claims.length === 0 ? (
              <tr>
                <td colSpan={7} className="no-data">
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
                  <td>{claim.paid_amount_aed.toLocaleString()}</td>
                  <td className="explanation-cell">
                    {claim.error_explanation ? (
                      <div style={{ whiteSpace: 'pre-line' }}>
                        {claim.error_explanation}
                      </div>
                    ) : (
                      'N/A'
                    )}
                  </td>
                  <td className="action-cell">
                    {claim.recommended_action ? (
                      <div style={{ whiteSpace: 'pre-line' }}>
                        {claim.recommended_action}
                      </div>
                    ) : (
                      'N/A'
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

