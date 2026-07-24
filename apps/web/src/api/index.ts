import axios from 'axios';
import type {
  Project,
  ProjectCreate,
  Dataset,
  Factor,
  FactorCreate,
  FactorValidation,
  ResearchRun,
  RunCreate,
  RunSummary,
  FactorMetric,
  AppSettings,
  LLMConfig,
  Capabilities,
  HealthResponse,
} from '@/types';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// --- Health ---
export const healthApi = {
  check: () => api.get<HealthResponse>('/health').then(r => r.data),
  version: () => api.get<HealthResponse>('/version').then(r => r.data),
  capabilities: () => api.get<Capabilities>('/capabilities').then(r => r.data),
};

// --- Projects ---
export const projectsApi = {
  list: () => api.get<Project[]>('/projects').then(r => r.data),
  get: (id: string) => api.get<Project>(`/projects/${id}`).then(r => r.data),
  create: (data: ProjectCreate) => api.post<Project>('/projects', data).then(r => r.data),
  update: (id: string, data: Partial<ProjectCreate>) =>
    api.patch<Project>(`/projects/${id}`, data).then(r => r.data),
  delete: (id: string) =>
    api.delete(`/projects/${id}?confirm=true`).then(r => r.data),
};

// --- Datasets ---
export const datasetsApi = {
  list: (projectId: string) =>
    api.get<Dataset[]>(`/projects/${projectId}/datasets`).then(r => r.data),
  get: (id: string) => api.get<Dataset>(`/datasets/${id}`).then(r => r.data),
  upload: (projectId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<Dataset>(`/projects/${projectId}/datasets/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data);
  },
  validate: (id: string) =>
    api.post(`/datasets/${id}/validate`).then(r => r.data),
  preview: (id: string, nRows = 50) =>
    api.get(`/datasets/${id}/preview?n_rows=${nRows}`).then(r => r.data),
  delete: (id: string) =>
    api.delete(`/datasets/${id}?confirm=true`).then(r => r.data),
};

// --- Factors ---
export const factorsApi = {
  list: (projectId: string) =>
    api.get<Factor[]>(`/projects/${projectId}/factors`).then(r => r.data),
  get: (id: string) => api.get<Factor>(`/factors/${id}`).then(r => r.data),
  create: (projectId: string, data: FactorCreate) =>
    api.post<Factor>(`/projects/${projectId}/factors`, data).then(r => r.data),
  validate: (projectId: string, expression: string) =>
    api.post<FactorValidation>(`/projects/${projectId}/factors/validate`, { expression }).then(r => r.data),
  seed: (projectId: string) =>
    api.post<Factor[]>(`/projects/${projectId}/factors/seed`).then(r => r.data),
  delete: (id: string) =>
    api.delete(`/factors/${id}`).then(r => r.data),
};

// --- Runs ---
export const runsApi = {
  list: (projectId: string) =>
    api.get<ResearchRun[]>(`/projects/${projectId}/runs`).then(r => r.data),
  get: (id: string) => api.get<ResearchRun>(`/runs/${id}`).then(r => r.data),
  create: (projectId: string, data: RunCreate) =>
    api.post<ResearchRun>(`/projects/${projectId}/runs`, data).then(r => r.data),
  cancel: (id: string) =>
    api.post(`/runs/${id}/cancel`).then(r => r.data),
  rerun: (id: string) =>
    api.post<ResearchRun>(`/runs/${id}/rerun`).then(r => r.data),
  logs: (id: string) =>
    api.get(`/runs/${id}/logs`).then(r => r.data),
  summary: (id: string) =>
    api.get<RunSummary>(`/runs/${id}/summary`).then(r => r.data),
  factorMetrics: (id: string) =>
    api.get<FactorMetric[]>(`/runs/${id}/factor-metrics`).then(r => r.data),
};

// --- Reports ---
export const reportsApi = {
  reportUrl: (runId: string) => `/api/v1/runs/${runId}/report`,
  artifacts: (runId: string) =>
    api.get(`/runs/${runId}/artifacts`).then(r => r.data),
};

// --- Settings ---
export const settingsApi = {
  getAll: () => api.get<AppSettings>('/settings').then(r => r.data),
  update: (updates: Record<string, string>) =>
    api.patch<AppSettings>('/settings', { updates }).then(r => r.data),
  llm: () => api.get<LLMConfig>('/settings/llm').then(r => r.data),
};

export default api;
