import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projectsApi, datasetsApi, factorsApi, runsApi } from '@/api'
import type { FactorCreate } from '@/types'

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'overview' | 'datasets' | 'factors' | 'runs'>('overview')
  const [showFactorForm, setShowFactorForm] = useState(false)
  const [factorForm, setFactorForm] = useState<FactorCreate>({
    name: '',
    expression: '',
    agent_id: '',
    level: 1,
    direction: 1,
    description: '',
  })

  const { data: project } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectsApi.get(projectId!),
    enabled: !!projectId,
  })
  const { data: datasets } = useQuery({
    queryKey: ['datasets', projectId],
    queryFn: () => datasetsApi.list(projectId!),
    enabled: !!projectId,
  })
  const { data: factors } = useQuery({
    queryKey: ['factors', projectId],
    queryFn: () => factorsApi.list(projectId!),
    enabled: !!projectId,
  })
  const { data: runs } = useQuery({
    queryKey: ['runs', projectId],
    queryFn: () => runsApi.list(projectId!),
    enabled: !!projectId,
  })

  const seedMutation = useMutation({
    mutationFn: () => factorsApi.seed(projectId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['factors', projectId] })
    },
  })

  const createFactorMutation = useMutation({
    mutationFn: (data: FactorCreate) => factorsApi.create(projectId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['factors', projectId] })
      setShowFactorForm(false)
      setFactorForm({ name: '', expression: '', agent_id: '', level: 1, direction: 1, description: '' })
    },
  })

  const validateMutation = useMutation({
    mutationFn: (expr: string) => factorsApi.validate(projectId!, expr),
  })

  const createRunMutation = useMutation({
    mutationFn: () => runsApi.create(projectId!, { run_type: 'full' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['runs', projectId] })
    },
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => datasetsApi.upload(projectId!, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets', projectId] })
    },
  })

  if (!project) return <div className="loading">Loading...</div>

  const tabs = ['overview', 'datasets', 'factors', 'runs'] as const

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to="/projects">← Projects</Link>
          <h1 className="page-title" style={{ marginTop: '8px' }}>{project.name}</h1>
        </div>
        <div>
          <button className="btn-primary" onClick={() => createRunMutation.mutate()}>
            Start Research Run
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '16px' }}>
        {tabs.map(tab => (
          <button
            key={tab}
            className={activeTab === tab ? 'btn-primary btn-sm' : 'btn-secondary btn-sm'}
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div className="card">
          <table>
            <tbody>
              <tr><th>Name</th><td>{project.name}</td></tr>
              <tr><th>Market</th><td>{project.market}</td></tr>
              <tr><th>Status</th><td><span className="badge badge-info">{project.status}</span></td></tr>
              <tr><th>Description</th><td>{project.description || '---'}</td></tr>
              <tr><th>Created</th><td>{project.created_at ?? '---'}</td></tr>
              <tr><th>Datasets</th><td>{datasets?.length ?? 0}</td></tr>
              <tr><th>Factors</th><td>{factors?.length ?? 0}</td></tr>
              <tr><th>Runs</th><td>{runs?.length ?? 0}</td></tr>
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'datasets' && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Datasets ({datasets?.length ?? 0})</h2>
            <input
              type="file"
              accept=".csv,.parquet"
              onChange={e => {
                const file = e.target.files?.[0]
                if (file) uploadMutation.mutate(file)
              }}
              style={{ display: 'none' }}
              id="dataset-upload"
            />
            <label htmlFor="dataset-upload">
              <button className="btn-primary btn-sm" as="span">
                Upload Dataset
              </button>
            </label>
          </div>
          {datasets && datasets.length > 0 ? (
            <table>
              <thead>
                <tr>
                  <th>Name</th><th>Type</th><th>Rows</th><th>Symbols</th>
                  <th>Date Range</th><th>Quality</th>
                </tr>
              </thead>
              <tbody>
                {datasets.map(d => (
                  <tr key={d.id}>
                    <td>{d.name}</td>
                    <td>{d.source_type}</td>
                    <td>{d.row_count.toLocaleString()}</td>
                    <td>{d.symbol_count}</td>
                    <td>{d.start_date} ~ {d.end_date}</td>
                    <td>
                      <span className={`badge badge-${d.quality_status === 'valid' ? 'success' : 'warning'}`}>
                        {d.quality_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-state">
              <p>No datasets uploaded yet.</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'factors' && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Factors ({factors?.length ?? 0})</h2>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                className="btn-secondary btn-sm"
                onClick={() => seedMutation.mutate()}
                disabled={seedMutation.isPending}
              >
                Seed 21 Factors
              </button>
              <button
                className="btn-primary btn-sm"
                onClick={() => setShowFactorForm(!showFactorForm)}
              >
                {showFactorForm ? 'Cancel' : '+ Add Factor'}
              </button>
            </div>
          </div>

          {showFactorForm && (
            <div style={{ marginBottom: '16px', padding: '16px', background: 'var(--bg-tertiary)', borderRadius: '8px' }}>
              <div className="form-group">
                <label className="form-label">Factor Name</label>
                <input
                  className="form-input"
                  value={factorForm.name}
                  onChange={e => setFactorForm({ ...factorForm, name: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">DSL Expression</label>
                <textarea
                  className="form-textarea"
                  value={factorForm.expression}
                  onChange={e => {
                    setFactorForm({ ...factorForm, expression: e.target.value })
                    if (e.target.value) validateMutation.mutate(e.target.value)
                  }}
                  placeholder="e.g. ts_rank(close, 20)"
                />
                {validateMutation.data && (
                  <div style={{ marginTop: '4px', fontSize: '12px' }}>
                    {validateMutation.data.valid ? (
                      <span className="badge badge-success">Valid</span>
                    ) : (
                      <span className="badge badge-danger">Error: {validateMutation.data.error}</span>
                    )}
                  </div>
                )}
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <div className="form-group" style={{ flex: 1 }}>
                  <label className="form-label">Agent ID</label>
                  <input
                    className="form-input"
                    value={factorForm.agent_id}
                    onChange={e => setFactorForm({ ...factorForm, agent_id: e.target.value })}
                    placeholder="Agent_01"
                  />
                </div>
                <div className="form-group" style={{ width: '100px' }}>
                  <label className="form-label">Level</label>
                  <select
                    className="form-select"
                    value={factorForm.level}
                    onChange={e => setFactorForm({ ...factorForm, level: Number(e.target.value) })}
                  >
                    {[1,2,3,4,5,6,7].map(l => <option key={l} value={l}>{l}</option>)}
                  </select>
                </div>
                <div className="form-group" style={{ width: '100px' }}>
                  <label className="form-label">Direction</label>
                  <select
                    className="form-select"
                    value={factorForm.direction}
                    onChange={e => setFactorForm({ ...factorForm, direction: Number(e.target.value) })}
                  >
                    <option value={1}>+1</option>
                    <option value={-1}>-1</option>
                  </select>
                </div>
              </div>
              <button
                className="btn-primary btn-sm"
                onClick={() => createFactorMutation.mutate(factorForm)}
                disabled={!factorForm.name || !factorForm.expression}
              >
                Create Factor
              </button>
            </div>
          )}

          {factors && factors.length > 0 ? (
            <table>
              <thead>
                <tr>
                  <th>Name</th><th>Agent</th><th>Level</th>
                  <th>Expression</th><th>Origin</th><th>Status</th>
                </tr>
              </thead>
              <tbody>
                {factors.map(f => (
                  <tr key={f.id}>
                    <td>{f.name}</td>
                    <td>{f.agent_id || '---'}</td>
                    <td>L{f.level}</td>
                    <td style={{ fontFamily: 'monospace', fontSize: '12px', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {f.expression}
                    </td>
                    <td><span className="badge badge-info">{f.origin}</span></td>
                    <td><span className={`badge badge-${f.validation_status === 'valid' ? 'success' : 'warning'}`}>{f.validation_status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-state">
              <p>No factors yet. Click "Seed 21 Factors" to load defaults.</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'runs' && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Research Runs ({runs?.length ?? 0})</h2>
          </div>
          {runs && runs.length > 0 ? (
            <table>
              <thead>
                <tr>
                  <th>ID</th><th>Type</th><th>Status</th>
                  <th>Progress</th><th>Stage</th><th>Created</th>
                </tr>
              </thead>
              <tbody>
                {runs.map(r => (
                  <tr key={r.id}>
                    <td><Link to={`/runs/${r.id}`}>{r.id.slice(0, 8)}...</Link></td>
                    <td>{r.run_type}</td>
                    <td>
                      <span className={`badge badge-${
                        r.status === 'succeeded' ? 'success' :
                        r.status === 'failed' ? 'danger' :
                        r.status === 'running' ? 'info' : 'warning'
                      }`}>{r.status}</span>
                    </td>
                    <td>
                      <div className="progress-bar">
                        <div className="progress-bar-fill" style={{ width: `${r.progress}%` }} />
                      </div>
                      <span style={{ fontSize: '11px' }}>{r.progress.toFixed(0)}%</span>
                    </td>
                    <td>{r.current_stage}</td>
                    <td>{r.created_at?.split('T')[0] ?? '---'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-state">
              <p>No runs yet. Click "Start Research Run" to begin.</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
