import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projectsApi, factorsApi } from '@/api'

export function FactorLabPage() {
  const queryClient = useQueryClient()
  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
  })
  const [selectedProject, setSelectedProject] = useState<string>('')
  const [expression, setExpression] = useState('')
  const [validation, setValidation] = useState<{ valid: boolean; error: string | null } | null>(null)

  const { data: factors } = useQuery({
    queryKey: ['factors', selectedProject],
    queryFn: () => factorsApi.list(selectedProject),
    enabled: !!selectedProject,
  })

  const validateMutation = useMutation({
    mutationFn: (expr: string) => factorsApi.validate(selectedProject, expr),
    onSuccess: (data) => {
      setValidation({ valid: data.valid, error: data.error })
    },
  })

  const createMutation = useMutation({
    mutationFn: (data: { name: string; expression: string }) =>
      factorsApi.create(selectedProject, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['factors', selectedProject] })
      setExpression('')
      setValidation(null)
    },
  })

  const seedMutation = useMutation({
    mutationFn: () => factorsApi.seed(selectedProject),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['factors', selectedProject] })
    },
  })

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Factor Lab</h1>
        {projects && (
          <select
            className="form-select"
            style={{ width: 'auto' }}
            value={selectedProject}
            onChange={e => setSelectedProject(e.target.value)}
          >
            <option value="">Select Project...</option>
            {projects.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        )}
      </div>

      {!selectedProject ? (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon">[F]</div>
            <p>Select a project to use the Factor Lab.</p>
          </div>
        </div>
      ) : (
        <>
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">DSL Expression Validator</h2>
              <button
                className="btn-secondary btn-sm"
                onClick={() => seedMutation.mutate()}
                disabled={seedMutation.isPending}
              >
                Seed 21 Default Factors
              </button>
            </div>
            <div className="form-group">
              <label className="form-label">Expression</label>
              <textarea
                className="form-textarea"
                value={expression}
                onChange={e => {
                  setExpression(e.target.value)
                  if (e.target.value && selectedProject) {
                    validateMutation.mutate(e.target.value)
                  }
                }}
                placeholder="e.g. ts_rank(close, 20)"
              />
            </div>
            {validation && (
              <div style={{ marginBottom: '12px' }}>
                {validation.valid ? (
                  <span className="badge badge-success">Valid Expression</span>
                ) : (
                  <span className="badge badge-danger">Invalid: {validation.error}</span>
                )}
              </div>
            )}
            <button
              className="btn-primary btn-sm"
              onClick={() => {
                const name = prompt('Factor name:')
                if (name && expression) {
                  createMutation.mutate({ name, expression })
                }
              }}
              disabled={!expression || !validation?.valid}
            >
              Save as Factor
            </button>
            <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--text-secondary)' }}>
              <p><strong>Allowed fields:</strong> open, high, low, close, volume, amount</p>
              <p><strong>Allowed functions:</strong> delay, delta, ret, ts_mean, ts_sum, ts_std,
                ts_min, ts_max, ts_rank, corr, cov, rank, zscore, winsorize, abs, sign, log1p,
                sqrt, clip, add, sub, mul, div, min, max, where</p>
              <p><strong>Forbidden:</strong> exec, eval, compile, shift(-n), lead, future, file/network access</p>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Factors ({factors?.length ?? 0})</h2>
            </div>
            {factors && factors.length > 0 ? (
              <table>
                <thead>
                  <tr>
                    <th>Name</th><th>Level</th><th>Expression</th>
                    <th>Origin</th><th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {factors.map(f => (
                    <tr key={f.id}>
                      <td>{f.name}</td>
                      <td>L{f.level}</td>
                      <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>{f.expression}</td>
                      <td><span className="badge badge-info">{f.origin}</span></td>
                      <td><span className={`badge badge-${f.validation_status === 'valid' ? 'success' : 'warning'}`}>{f.validation_status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="empty-state">
                <p>No factors. Click "Seed 21 Default Factors" to load presets.</p>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
