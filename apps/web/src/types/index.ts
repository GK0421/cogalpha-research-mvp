// Core API types for CogAlpha Studio

export interface Project {
  id: string;
  name: string;
  description: string;
  market: string;
  status: string;
  default_config: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  market?: string;
  default_config?: Record<string, unknown>;
}

export interface Dataset {
  id: string;
  project_id: string;
  name: string;
  source_type: string;
  original_filename: string;
  stored_path: string;
  sha256: string;
  row_count: number;
  symbol_count: number;
  start_date: string;
  end_date: string;
  schema_version: string;
  quality_status: string;
  quality_report: Record<string, unknown>;
  created_at: string | null;
}

export interface Factor {
  id: string;
  project_id: string;
  name: string;
  agent_id: string;
  level: number;
  expression: string;
  direction: number;
  description: string;
  origin: string;
  expression_hash: string;
  validation_status: string;
  created_at: string | null;
}

export interface FactorCreate {
  name: string;
  expression: string;
  agent_id?: string;
  level?: number;
  direction?: number;
  description?: string;
  origin?: string;
}

export interface FactorValidation {
  valid: boolean;
  hash: string;
  error: string | null;
}

export interface ResearchRun {
  id: string;
  project_id: string;
  dataset_id: string | null;
  run_type: string;
  status: string;
  progress: number;
  current_stage: string;
  config_snapshot: Record<string, unknown>;
  started_at: string | null;
  finished_at: string | null;
  error_code: string;
  error_message: string;
  result_path: string;
  created_at: string | null;
}

export interface RunCreate {
  dataset_id?: string | null;
  run_type?: string;
  config?: Record<string, unknown>;
}

export interface RunSummary {
  run_id: string;
  n_factors?: number;
  n_passed_quality?: number;
  n_elite?: number;
  n_qualified?: number;
  n_after_dedup?: number;
  portfolio?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface FactorMetric {
  [key: string]: string | number;
}

export interface AppSettings {
  [key: string]: string;
}

export interface LLMConfig {
  enabled: boolean;
  provider: string;
  model: string;
  base_url: string;
  key_configured: boolean;
}

export interface Capabilities {
  product: string;
  version: string;
  features: string[];
  seed_factors_count: number;
  llm_required: boolean;
  trading_enabled: boolean;
  research_only: boolean;
}

export interface HealthResponse {
  status: string;
  product: string;
  version: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}
