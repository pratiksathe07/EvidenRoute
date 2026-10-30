import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Activity, Clock } from 'lucide-react';
import { RetrievalActivityPoint } from '../../types/dashboard';
import './ActivityChart.css';

interface ActivityChartProps {
  data: RetrievalActivityPoint[];
  isLoading?: boolean;
}

export const ActivityChart: React.FC<ActivityChartProps> = ({
  data,
  isLoading = false,
}) => {
  const hasData = data && data.length > 0;

  return (
    <div className="activity-chart-card">
      <div className="activity-chart-header">
        <div>
          <h3 className="activity-chart-title">Retrieval Activity Over Time</h3>
          <p className="activity-chart-subtitle">
            Monitors context selection frequency, evidence counts, and token budget expenditure.
          </p>
        </div>
        <div className="activity-chart-period-badge">
          <Clock size={13} />
          <span>Live Window</span>
        </div>
      </div>

      <div className="activity-chart-content">
        {isLoading ? (
          <div className="chart-loading-state">
            <span className="chart-spinner" />
            <p>Loading activity stream...</p>
          </div>
        ) : hasData ? (
          <div className="chart-responsive-wrapper">
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart
                data={data}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="colorEvidence" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00B871" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#00B871" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
                <XAxis
                  dataKey="time"
                  stroke="#94A3B8"
                  fontSize={12}
                  tickLine={false}
                  axisLine={{ stroke: '#E2E8F0' }}
                />
                <YAxis
                  stroke="#94A3B8"
                  fontSize={12}
                  tickLine={false}
                  axisLine={{ stroke: '#E2E8F0' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#E2E8F0',
                    borderRadius: '8px',
                    boxShadow: '0 4px 12px rgba(15, 23, 42, 0.08)',
                    fontSize: '12px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="evidence"
                  name="Evidence Items"
                  stroke="#00B871"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorEvidence)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : (
          /* High-polish Empty State when no real historical queries exist yet */
          <div className="chart-empty-state">
            <div className="chart-empty-illustration">
              <div className="chart-grid-mockup">
                <div className="grid-line line-1" />
                <div className="grid-line line-2" />
                <div className="grid-line line-3" />
                <div className="grid-axis" />
              </div>
              <div className="chart-empty-icon-circle">
                <Activity size={22} className="chart-empty-icon" />
              </div>
            </div>
            <h4 className="chart-empty-title">Awaiting Retrieval Telemetry</h4>
            <p className="chart-empty-text">
              Retrieval throughput, evidence volume, and token budget consumption will automatically plot in real time as queries are orchestrated.
            </p>
            <div className="chart-empty-badge">
              <span className="empty-status-dot" />
              <span>Telemetry Stream: Ready (0 query events recorded)</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
