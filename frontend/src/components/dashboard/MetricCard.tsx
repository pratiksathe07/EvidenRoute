import React from 'react';
import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react';
import './MetricCard.css';

interface MetricCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  description: string;
  trend?: {
    value: string;
    isPositive: boolean;
  };
  isAwaitingData?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  icon: Icon,
  description,
  trend,
  isAwaitingData = false,
}) => {
  return (
    <div className={`metric-card ${isAwaitingData ? 'awaiting-data' : ''}`}>
      <div className="metric-card-header">
        <span className="metric-card-label">{label}</span>
        <div className="metric-card-icon-wrapper">
          <Icon size={18} className="metric-card-icon" />
        </div>
      </div>

      <div className="metric-card-body">
        <div className="metric-card-value-row">
          <span className={`metric-card-value ${isAwaitingData ? 'placeholder' : ''}`}>
            {value}
          </span>
          {trend && !isAwaitingData && (
            <span
              className={`metric-card-trend ${trend.isPositive ? 'positive' : 'negative'}`}
            >
              {trend.isPositive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
              {trend.value}
            </span>
          )}
        </div>
        <p className="metric-card-description">{description}</p>
      </div>

      {isAwaitingData && (
        <div className="metric-card-status-pill">
          <span className="status-dot-pending" />
          <span>Awaiting integration</span>
        </div>
      )}
    </div>
  );
};
