import { useQuery } from '@tanstack/react-query'
import { projectsApi, runsApi } from '@/api'
import { Link } from 'react-router-dom'

export function RunsPage() {
  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
  })
  const { data: allRuns } = useQuery({
    queryKey: ['all-runs'],
    queryFn: async () => {
      if (!projects) return []
      const results = await Promise.all(
        projects.map(p => runsApi.list(p.id).then(runs => runs.map(r => ({ ...r, project_name: p.name }))))
      )
      return results.flat()
    },
    enabled: !!projects,
  })

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Research Runs</h1>
      </div>

      <div className="card">
        {allRuns && allRuns.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>ID</th><th>Project</th><th>Type</th><th>Status</th>
                <th>Progress</th><th>Stage</th><th>Created</th>
              </tr>
            </thead>
            <tbody>
              {allRuns.map(r => (
                <tr key={r.id}>
                  <td><Link to={`/runs/${r.id}`}>{r.id.slice(0, 8)}...</Link></td>
                  <td>{r.project_name}</td>
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
            <div className="empty-state-icon">[R]</div>
            <p>No research runs yet.</p>
          </div>
        )}
      </div>
    </div>
  )
}
