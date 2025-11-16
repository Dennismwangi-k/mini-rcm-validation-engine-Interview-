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
  Cell,
} from 'recharts';
import { Statistics } from '../api/claims';
import './Charts.css';

interface ChartsProps {
  statistics: Statistics;
}

const Charts: React.FC<ChartsProps> = ({ statistics }) => {

  // Prepare data for waterfall chart - claim counts
  // Waterfall shows cumulative values
  const claimCountsRaw = [
    { category: 'No Error', count: statistics.error_type_counts.no_error, color: '#10b981' },
    { category: 'Medical Error', count: statistics.error_type_counts.medical_error, color: '#f59e0b' },
    { category: 'Technical Error', count: statistics.error_type_counts.technical_error, color: '#ef4444' },
    { category: 'Both', count: statistics.error_type_counts.both, color: '#8b5cf6' },
  ];

  // Calculate cumulative values for waterfall
  let cumulativeCount = 0;
  const claimCountsData = claimCountsRaw.map((item) => {
    const start = cumulativeCount;
    cumulativeCount += item.count;
    return {
      ...item,
      start,
      end: cumulativeCount,
    };
  });

  // Prepare data for waterfall chart - paid amount
  const paidAmountRaw = [
    { category: 'No Error', amount: statistics.paid_amount_by_error.no_error, color: '#10b981' },
    { category: 'Medical Error', amount: statistics.paid_amount_by_error.medical_error, color: '#f59e0b' },
    { category: 'Technical Error', amount: statistics.paid_amount_by_error.technical_error, color: '#ef4444' },
    { category: 'Both', amount: statistics.paid_amount_by_error.both, color: '#8b5cf6' },
  ];

  // Calculate cumulative values for waterfall
  let cumulativeAmount = 0;
  const paidAmountData = paidAmountRaw.map((item) => {
    const start = cumulativeAmount;
    cumulativeAmount += item.amount;
    return {
      ...item,
      start,
      end: cumulativeAmount,
    };
  });

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="chart-tooltip">
          <p className="tooltip-label">{label}</p>
          <p className="tooltip-value">
            {payload[0].name === 'count' 
              ? `${payload[0].value} claims`
              : `AED ${Number(payload[0].value).toLocaleString()}`}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="charts-container">
      <h2>Waterfall Charts</h2>
      
      <div className="charts-grid">
        <div className="chart-card animated-chart">
          <div className="chart-header">
          <h3>Claim Counts by Error Category</h3>
            <div className="chart-icon">📈</div>
          </div>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart 
              data={claimCountsData}
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <defs>
                {claimCountsData.map((entry, index) => (
                  <linearGradient key={`gradient-${index}`} id={`gradientCount-${index}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={entry.color} stopOpacity={1} />
                    <stop offset="100%" stopColor={entry.color} stopOpacity={0.6} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.5} />
              <XAxis 
                dataKey="category" 
                tick={{ fill: '#64748b', fontSize: 12, fontWeight: 500 }}
                axisLine={{ stroke: '#cbd5e1' }}
              />
              <YAxis 
                tick={{ fill: '#64748b', fontSize: 12 }}
                axisLine={{ stroke: '#cbd5e1' }}
              />
              <Tooltip 
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="chart-tooltip">
                        <p className="tooltip-label">{data.category}</p>
                        <p className="tooltip-value">{data.count} claims</p>
                        <p className="tooltip-value" style={{ fontSize: '11px', color: '#64748b' }}>
                          Cumulative: {data.end}
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend 
                wrapperStyle={{ paddingTop: '20px' }}
                iconType="circle"
              />
              <Bar 
                dataKey="count" 
                name="Claims"
                radius={[12, 12, 0, 0]}
                animationDuration={1500}
                animationBegin={0}
                stackId="waterfall"
              >
                {claimCountsData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={`url(#gradientCount-${index})`} />
                ))}
              </Bar>
              {/* Base bars for waterfall effect */}
              <Bar 
                dataKey="start" 
                stackId="waterfall"
                fill="transparent"
              >
                {claimCountsData.map((entry, index) => (
                  <Cell key={`base-${index}`} fill="transparent" />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card animated-chart">
          <div className="chart-header">
          <h3>Paid Amount (AED) by Error Category</h3>
            <div className="chart-icon">💰</div>
          </div>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart 
              data={paidAmountData}
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <defs>
                {paidAmountData.map((entry, index) => (
                  <linearGradient key={`gradient-${index}`} id={`gradientAmount-${index}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={entry.color} stopOpacity={1} />
                    <stop offset="100%" stopColor={entry.color} stopOpacity={0.6} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.5} />
              <XAxis 
                dataKey="category" 
                tick={{ fill: '#64748b', fontSize: 12, fontWeight: 500 }}
                axisLine={{ stroke: '#cbd5e1' }}
              />
              <YAxis 
                tick={{ fill: '#64748b', fontSize: 12 }}
                axisLine={{ stroke: '#cbd5e1' }}
                tickFormatter={(value) => `AED ${(value / 1000).toFixed(0)}k`}
              />
              <Tooltip 
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="chart-tooltip">
                        <p className="tooltip-label">{data.category}</p>
                        <p className="tooltip-value">AED {Number(data.amount).toLocaleString()}</p>
                        <p className="tooltip-value" style={{ fontSize: '11px', color: '#64748b' }}>
                          Cumulative: AED {Number(data.end).toLocaleString()}
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend 
                wrapperStyle={{ paddingTop: '20px' }}
                iconType="circle"
              />
              <Bar 
                dataKey="amount" 
                name="Amount (AED)"
                radius={[12, 12, 0, 0]}
                animationDuration={1500}
                animationBegin={200}
                stackId="waterfall"
              >
                {paidAmountData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={`url(#gradientAmount-${index})`} />
                ))}
              </Bar>
              {/* Base bars for waterfall effect */}
              <Bar 
                dataKey="start" 
                stackId="waterfall"
                fill="transparent"
              >
                {paidAmountData.map((entry, index) => (
                  <Cell key={`base-${index}`} fill="transparent" />
                ))}
              </Bar>
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

