/**
 * Axios instance configured for API requests with credentials
 * This ensures cookies (JWT tokens) are sent with all requests
 */
import axios from 'axios';

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, '') ?? 'http://localhost:8000';

// Create axios instance with credentials enabled
export const apiClient = axios.create({
  baseURL: API_BASE,
  withCredentials: true, // Important: Send cookies with all requests
  headers: {
    'Content-Type': 'application/json',
  },
});

export default apiClient;
export { API_BASE };

