/**
 * Axios instance configured for API requests with credentials
 * This ensures cookies (JWT tokens) are sent with all requests
 */
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { updateActivity } from './auth';

// Support both NEXT_PUBLIC_BACKEND_URL and NEXT_PUBLIC_API_BASE for flexibility
const API_BASE =
  (process.env.NEXT_PUBLIC_BACKEND_URL || process.env.NEXT_PUBLIC_API_BASE)?.replace(/\/$/, '') ?? 'http://localhost:8000';

// Create axios instance with credentials enabled
export const apiClient = axios.create({
  baseURL: API_BASE,
  withCredentials: true, // Important: Send cookies with all requests
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor to handle token refresh on 401 errors
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (error?: any) => void;
}> = [];

const processQueue = (error: AxiosError | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => {
    // Update activity on successful API calls
    updateActivity();
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // If error is 401 and we haven't tried to refresh yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return apiClient(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Try to refresh the token using apiClient to ensure baseURL is used
        const response = await apiClient.post(
          '/auth/refresh',
          {}
        );

        if (response.status === 200) {
          processQueue(null, null);
          // Retry the original request
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        processQueue(refreshError as AxiosError, null);
        // If refresh fails, redirect to login
        if (typeof window !== 'undefined') {
          window.location.href = '/auth';
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
export { API_BASE };

