import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

export const scanUrl = async (url) => {
  const response = await api.post('/api/scan', { url });
  return response.data;
};

export const getHistory = async (limit = 50, offset = 0) => {
  const response = await api.get(`/api/history?limit=${limit}&offset=${offset}`);
  return response.data;
};

export const getScanDetail = async (scanId) => {
  const response = await api.get(`/api/history/${scanId}`);
  return response.data;
};

export const getStats = async () => {
  const response = await api.get('/api/history/stats');
  return response.data;
};

export const exportReport = async (format = 'json') => {
  const response = await api.get(`/api/report/export?format=${format}`);
  return response.data;
};

export const getHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
