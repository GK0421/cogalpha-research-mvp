import { useQuery } from '@tanstack/react-query'
import { healthApi, projectsApi } from '@/api'
import { Link } from 'react-router-dom'

export function DashboardPage() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: healthApi.check,
  })
  const { data: capabilities } = useQuery({
    queryKey: ['capabilities'],
    queryFn: healthApi.capabilities,
  })
  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
  })

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        {health && (
          <span className="badge badge-success">
            {health.product} v{health.version}
          </span>
        )}
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">System Status</h2>
        </div>
        <table>
          <tbody>
            <tr>
              <th>Status</th>
              <td><span className="badge badge-success">Online</span></td>
            </tr>
            <tr>
              <th>Product</th>
              <td>{health?.product ?? '---'}</td>
            </tr>
            <tr>
              <th>Version</th>
              <td>{health?.version ?? '---'}</td>
            </tr>
            <tr>
              <th>Seed Factors</th>
              <td>{capabilities?.seed_factors_count ?? '---'}</td>
            </tr>
            <tr>
              <th>LLM Required</th>
              <td>{capabilities?.llm_required ? 'Yes' : 'No'}</td>
            </tr>
            <tr>
              <th>Trading Enabled</th>
              <td>
                <span className="badge badge-danger">No (Research Only)</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Recent Projects ({projects?.length ?? 0})</h2>
          <Link to="/projects">
            <button className="btn-secondary btn-sm">View All</button>
          </Link>
        </div>
        {projects && projects.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Market</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {projects.slice(0, 5).map(p => (
                <tr key={p.id}>
                  <td>
                    <Link to={`/projects/${p.id}`}>{p.name}</Link>
                  </td>
                  <td>{p.market}</td>
                  <td>
                    <span className="badge badge-info">{p.status}</span>
                  </td>
                  <td>{p.created_at ?? '---'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state">
            <div className="empty-state-icon">[ ]</div>
            <p>No projects yet. Create one to get started.</p>
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Features</h2>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {capabilities?.features.map(f => (
            <span key={f} className="badge badge-info">{f}</span>
          ))}
        </div>
      </div>
    </div>
  )
}
