import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Statistics } from '../api/claims';
import './Charts.css';

interface ChartsProps {
  statistics: Statistics;
}

const Charts: React.FC<ChartsProps> = ({ statistics }) => {
  // Prepare data for claim counts chart
  const claimCountsData = [
    {
      category: 'No Error',
      count: statistics.error_type_counts.no_error,
    },
    {
      category: 'Medical Error',
      count: statistics.error_type_counts.medical_error,
    },
    {
      category: 'Technical Error',
      count: statistics.error_type_counts.technical_error,
    },
    {
      category: 'Both',
      count: statistics.error_type_counts.both,
    },
  ];

  // Prepare data for paid amount chart
  const paidAmountData = [
    {
      category: 'No Error',
      amount: statistics.paid_amount_by_error.no_error,
    },
    {
      category: 'Medical Error',
      amount: statistics.paid_amount_by_error.medical_error,
    },
    {
      category: 'Technical Error',
      amount: statistics.paid_amount_by_error.technical_error,
    },
    {
      category: 'Both',
      amount: statistics.paid_amount_by_error.both,
    },
  ];

  return (
    <div className="charts-container">
      <h2>Validation Results</h2>
      
      <div className="charts-grid">
        <div className="chart-card">
          <h3>Claim Counts by Error Category</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={claimCountsData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="category" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#2563eb" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Paid Amount (AED) by Error Category</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={paidAmountData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="category" />
              <YAxis />
              <Tooltip formatter={(value: number) => `AED ${value.toLocaleString()}`} />
              <Legend />
              <Bar dataKey="amount" fill="#3b82f6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="summary-stats">
        <div className="stat-card">
          <h4>Total Claims</h4>
          <p className="stat-value">{statistics.total_claims}</p>
        </div>
        <div className="stat-card">
          <h4>Validated</h4>
          <p className="stat-value success">{statistics.validated}</p>
        </div>
        <div className="stat-card">
          <h4>Not Validated</h4>
          <p className="stat-value error">{statistics.not_validated}</p>
        </div>
        <div className="stat-card">
          <h4>Validation Rate</h4>
          <p className="stat-value">
            {statistics.total_claims > 0
              ? ((statistics.validated / statistics.total_claims) * 100).toFixed(1)
              : 0}%
          </p>
        </div>
      </div>
    </div>
  );
};

export default Charts;

