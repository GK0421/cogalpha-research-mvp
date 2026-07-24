import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { runsApi, reportsApi } from '@/api'

export function RunDetailPage() {
  const { runId } = useParams<{ runId: string }>()

  const { data: run } = useQuery({
    queryKey: ['run', runId],
    queryFn: () => runsApi.get(runId!),
    enabled: !!runId,
    refetchInterval: (data) => data?.status === 'running' ? 2000 : false,
  })

  const { data: summary } = useQuery({
    queryKey: ['run-summary', runId],
    queryFn: () => runsApi.summary(runId!),
    enabled: !!runId && run?.status === 'succeeded',
  })

  const { data: factorMetrics } = useQuery({
    queryKey: ['factor-metrics', runId],
    queryFn: () => runsApi.factorMetrics(runId!),
    enabled: !!runId && run?.status === 'succeeded',
  })

  if (!run) return <div className="loading">Loading...</div>

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to="/runs">← Runs</Link>
          <h1 className="page-title" style={{ marginTop: '8px' }}>
            Run {run.id.slice(0, 8)}...
          </h1>
        </div>
        <div>
          {run.status === 'running' && (
            <button
              className="btn-danger btn-sm"
              onClick={() => runsApi.cancel(run.id)}
            >
              Cancel Run
            </button>
          )}
          {run.status === 'succeeded' && (
            <>
              <button
                className="btn-secondary btn-sm"
                onClick={() => runsApi.rerun(run.id)}
              >
                Re-run
              </button>
              <a href={reportsApi.reportUrl(run.id)} target="_blank" rel="noopener noreferrer">
                <button className="btn-primary btn-sm">View Report</button>
              </a>
            </>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Run Details</h2>
          <span className={`badge badge-${
            run.status === 'succeeded' ? 'success' :
            run.status === 'failed' ? 'danger' :
            run.status === 'running' ? 'info' : 'warning'
          }`}>{run.status}</span>
        </div>
        <table>
          <tbody>
            <tr><th>Run ID</th><td style={{ fontFamily: 'monospace' }}>{run.id}</td></tr>
            <tr><th>Type</th><td>{run.run_type}</td></tr>
            <tr><th>Progress</th><td>{run.progress.toFixed(1)}%</td></tr>
            <tr><th>Current Stage</th><td>{run.current_stage}</td></tr>
            <tr><th>Started</th><td>{run.started_at ?? '---'}</td></tr>
            <tr><th>Finished</th><td>{run.finished_at ?? '---'}</td></tr>
            {run.error_message && (
              <tr><th>Error</th><td style={{ color: 'var(--danger)' }}>{run.error_message}</td></tr>
            )}
          </tbody>
        </table>
        {run.status === 'running' && (
          <div style={{ marginTop: '12px' }}>
            <div className="progress-bar">
              <div className="progress-bar-fill" style={{ width: `${run.progress}%` }} />
            </div>
          </div>
        )}
      </div>

      {summary && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Run Summary</h2>
          </div>
          <table>
            <tbody>
              {summary.n_factors !== undefined && <tr><th>Total Factors</th><td>{summary.n_factors}</td></tr>}
              {summary.n_passed_quality !== undefined && <tr><th>Passed Quality</th><td>{summary.n_passed_quality}</td></tr>}
              {summary.n_elite !== undefined && <tr><th>Elite Factors</th><td>{summary.n_elite}</td></tr>}
              {summary.n_qualified !== undefined && <tr><th>Qualified Factors</th><td>{summary.n_qualified}</td></tr>}
              {summary.n_after_dedup !== undefined && <tr><th>After Dedup</th><td>{summary.n_after_dedup}</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {factorMetrics && factorMetrics.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Factor Metrics</h2>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  {Object.keys(factorMetrics[0]).map(k => (
                    <th key={k}>{k}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {factorMetrics.map((m, i) => (
                  <tr key={i}>
                    {Object.values(m).map((v, j) => (
                      <td key={j} style={{ fontFamily: j === 0 ? 'inherit' : 'monospace', fontSize: '12px' }}>
                        {typeof v === 'number' ? v.toFixed(4) : String(v)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
