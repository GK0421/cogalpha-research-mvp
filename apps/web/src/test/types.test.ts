import { describe, it, expect } from 'vitest'
import type {
  Project,
  Dataset,
  Factor,
  Run,
  Artifact,
  Setting,
  HealthResponse,
  CapabilityResponse,
} from '../types'

describe('Type definitions', () => {
  it('Project type has required fields', () => {
    const project: Project = {
      id: 'p1',
      name: 'Test',
      description: 'desc',
      created_at: '2024-01-01',
      updated_at: '2024-01-01',
    }
    expect(project.id).toBe('p1')
  })

  it('Dataset type has required fields', () => {
    const ds: Dataset = {
      id: 'd1',
      project_id: 'p1',
      name: 'data.csv',
      source_type: 'csv',
      row_count: 100,
      symbol_count: 10,
      created_at: '2024-01-01',
    }
    expect(ds.row_count).toBe(100)
  })

  it('Factor type has required fields', () => {
    const f: Factor = {
      id: 'f1',
      project_id: 'p1',
      name: 'momentum',
      expression: 'ts_rank(close, 20)',
      origin: 'seed',
      agent_id: 'L1-001',
      validation_status: 'valid',
      created_at: '2024-01-01',
    }
    expect(f.name).toBe('momentum')
  })

  it('Run type has required fields', () => {
    const r: Run = {
      id: 'r1',
      project_id: 'p1',
      status: 'completed',
      run_type: 'full',
      created_at: '2024-01-01',
    }
    expect(r.status).toBe('completed')
  })

  it('HealthResponse type', () => {
    const h: HealthResponse = {
      status: 'ok',
      version: '0.2.1',
    }
    expect(h.status).toBe('ok')
  })
})
