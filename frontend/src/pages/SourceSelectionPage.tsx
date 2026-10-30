import React from 'react';
import { ResourceRankingPage } from './ResourceRankingPage';

/**
 * Re-export ResourceRankingPage for backward compatibility.
 */
export const SourceSelectionPage: React.FC = () => {
  return <ResourceRankingPage />;
};

export default SourceSelectionPage;
