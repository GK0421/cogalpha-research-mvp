import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '@/api'

export function SettingsPage() {
  const queryClient = useQueryClient()
  const { data: settings } = useQuery({
    queryKey: ['settings'],
    queryFn: settingsApi.getAll,
  })
  const { data: llmConfig } = useQuery({
    queryKey: ['llm-config'],
    queryFn: settingsApi.llm,
  })

  const updateMutation = useMutation({
    mutationFn: (updates: Record<string, string>) => settingsApi.update(updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      queryClient.invalidateQueries({ queryKey: ['llm-config'] })
    },
  })

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">LLM Configuration</h2>
          <span className={`badge badge-${llmConfig?.enabled ? 'success' : 'warning'}`}>
            {llmConfig?.enabled ? 'Enabled' : 'Disabled (Optional)'}
          </span>
        </div>
        <table>
          <tbody>
            <tr><th>Provider</th><td>{llmConfig?.provider ?? 'none'}</td></tr>
            <tr><th>Model</th><td>{llmConfig?.model || '---'}</td></tr>
            <tr><th>Base URL</th><td>{llmConfig?.base_url || '---'}</td></tr>
            <tr><th>API Key</th><td>{llmConfig?.key_configured ? 'Configured' : 'Not set'}</td></tr>
          </tbody>
        </table>
        <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--text-secondary)' }}>
          <p>LLM integration is <strong>optional</strong>. The MVP works fully without any API key.</p>
          <p>Supported providers: iFlytek Spark, MiniMax, OpenAI, Anthropic, DeepSeek, DashScope</p>
          <p>Configure via environment variables in <code>.env</code> file.</p>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Application Settings</h2>
          <button
            className="btn-primary btn-sm"
            onClick={() => {
              const key = prompt('Setting key:')
              const value = prompt('Setting value:')
              if (key && value) updateMutation.mutate({ [key]: value })
            }}
          >
            Add Setting
          </button>
        </div>
        {settings && (
          <table>
            <thead>
              <tr><th>Key</th><th>Value</th></tr>
            </thead>
            <tbody>
              {Object.entries(settings).map(([key, value]) => (
                <tr key={key}>
                  <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>{key}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>{value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Important Notice</h2>
        </div>
        <div className="disclaimer" style={{ marginBottom: '0' }}>
          RESEARCH_BACKTEST_ONLY | NO_LIVE_TRADING | NOT_INVESTMENT_ADVICE
        </div>
        <p style={{ marginTop: '12px', fontSize: '13px', color: 'var(--text-secondary)' }}>
          CogAlpha Studio is a research-only tool. It does not execute real trades.
          All backtest results are for educational and research purposes only.
        </p>
      </div>
    </div>
  )
}
