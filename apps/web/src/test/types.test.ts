import { describe, it, expect } from 'vitest'
import type { Project, Dataset, Factor, HealthResponse } from '../types'

describe('Type definitions', () => {
  it('Project type is usable', () => {
    const project: Project = {
      id: 'p1',
      name: 'Test',
      description: '',
      market: 'A-stock',
      status: 'active',
      default_config: {},
      created_at: '2024-01-01',
      updated_at: '2024-01-01',
    }
    expect(project.id).toBe('p1')
  })

  it('Dataset type is usable', () => {
    const ds: Dataset = {
      id: 'd1',
      project_id: 'p1',
      name: 'data.csv',
      source_type: 'csv',
      original_filename: 'data.csv',
      stored_path: '/data/data.csv',
      sha256: 'abc123',
      row_count: 100,
      symbol_count: 10,
      start_date: '2024-01-01',
      end_date: '2024-06-30',
      schema_version: '1.0',
      quality_status: 'valid',
      quality_report: {},
      created_at: '2024-01-01',
    }
    expect(ds.row_count).toBe(100)
  })

  it('Factor type is usable', () => {
    const f: Factor = {
      id: 'f1',
      project_id: 'p1',
      name: 'momentum',
      expression: 'ts_rank(close, 20)',
      origin: 'seed',
      agent_id: 'L1-001',
      level: 1,
      direction: 1,
      description: '20-day momentum',
      expression_hash: 'hash123',
      validation_status: 'valid',
      created_at: '2024-01-01',
    }
    expect(f.name).toBe('momentum')
  })

  it('HealthResponse type is usable', () => {
    const h: HealthResponse = {
      status: 'ok',
      product: 'CogAlpha Studio',
      version: '0.2.1',
    }
    expect(h.status).toBe('ok')
  })
})
