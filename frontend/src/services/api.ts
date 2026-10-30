import axios from 'axios';

/**
 * Shared Axios HTTP Client configured for EvidenRoute backend communication.
 * Coordinates with backend API running on configured port or localhost:8000.
 */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 4000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

export default apiClient;
