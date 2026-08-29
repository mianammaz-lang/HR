import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

const api = axios.create({
  baseURL: `${API_BASE}/api`,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
});

// Attach the logged-in user's token to every request.
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle 401 - session is missing/expired, send back to login.
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(err);
  }
);

// ─── Auth ─────────────────────────────────────────────────────────────────────
export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  getMe: () => api.get('/auth/me'),
  getUsers: () => api.get('/auth/users'),
  createUser: (data: any) => api.post('/auth/users', data),
  updateUser: (id: string, data: any) => api.put(`/auth/users/${id}`, data),
  deleteUser: (id: string) => api.delete(`/auth/users/${id}`),
};

// ─── Candidates ───────────────────────────────────────────────────────────────
export const candidatesAPI = {
  list: (params: any) => api.get('/candidates', { params }),
  get: (id: string) => api.get(`/candidates/${id}`),
  create: (data: any) => api.post('/candidates', data),
  update: (id: string, data: any) => api.put(`/candidates/${id}`, data),
  delete: (id: string) => api.delete(`/candidates/${id}`),
  export: (params: any) => api.get('/candidates/export', { params, responseType: 'blob' }),
};

// ─── Requisitions ─────────────────────────────────────────────────────────────
export const requisitionsAPI = {
  list: (params?: any) => api.get('/requisitions', { params }),
  get: (id: string) => api.get(`/requisitions/${id}`),
  create: (data: any) => api.post('/requisitions', data),
  update: (id: string, data: any) => api.put(`/requisitions/${id}`, data),
  delete: (id: string) => api.delete(`/requisitions/${id}`),
};

// ─── Scoring ──────────────────────────────────────────────────────────────────
export const scoringAPI = {
  score: (data: any) => api.post('/scoring/score', data),
  bulkScore: (data: any) => api.post('/scoring/bulk', data),
  history: (candidateId: string) => api.get(`/scoring/history/${candidateId}`),
};

// ─── Documents ────────────────────────────────────────────────────────────────
export const documentsAPI = {
  uploadCV: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/documents/upload-cv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// ─── Filters ──────────────────────────────────────────────────────────────────
export const filtersAPI = {
  apply: (data: any, params?: any) => api.post('/filters/apply', data, { params }),
  list: () => api.get('/filters'),
  save: (data: any) => api.post('/filters', data),
  delete: (id: string) => api.delete(`/filters/${id}`),
};

// ─── Search ───────────────────────────────────────────────────────────────────
export const searchAPI = {
  semantic: (q: string, limit?: number) =>
    api.get('/search/semantic', { params: { q, limit: limit || 20 } }),
};

// ─── Settings ─────────────────────────────────────────────────────────────────
export const settingsAPI = {
  getERPNext: () => api.get('/settings/erpnext'),
  updateERPNext: (data: any) => api.put('/settings/erpnext', data),
  testERPNext: () => api.post('/settings/erpnext/test'),
  importRequisitions: () => api.post('/settings/erpnext/import-requisitions'),
  retrySyncs: () => api.post('/settings/erpnext/retry-syncs'),
  getLLM: () => api.get('/settings/llm'),
  updateLLM: (data: any) => api.put('/settings/llm', data),
  getLLMModels: () => api.get('/settings/llm/models'),
  getPrompts: () => api.get('/settings/llm/prompts'),
  getAuditLogs: (params?: any) => api.get('/settings/audit-logs', { params }),
};

// ─── Analytics ────────────────────────────────────────────────────────────────
export const analyticsAPI = {
  dashboard: () => api.get('/analytics/dashboard'),
  full: () => api.get('/analytics'),
};

export default api;
