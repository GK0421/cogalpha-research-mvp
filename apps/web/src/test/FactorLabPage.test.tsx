import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { FactorLabPage } from '../pages/FactorLabPage'

vi.mock('@/api', () => ({
  projectsApi: { list: vi.fn(), create: vi.fn(), delete: vi.fn() },
  factorsApi: {
    list: vi.fn(),
    validate: vi.fn(),
    seed: vi.fn(),
  },
  datasetsApi: { list: vi.fn(), upload: vi.fn(), delete: vi.fn() },
  runsApi: { list: vi.fn(), get: vi.fn(), create: vi.fn() },
  reportsApi: { list: vi.fn(), download: vi.fn() },
  settingsApi: { get: vi.fn(), update: vi.fn() },
  healthApi: { check: vi.fn() },
}))

import { factorsApi } from '@/api'

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <FactorLabPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('FactorLabPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders factor lab header', () => {
    vi.mocked(factorsApi.list).mockReturnValue(new Promise(() => {}))
    renderPage()
    expect(screen.getByText(/Factor/i)).toBeInTheDocument()
  })

  it('shows factors when loaded', async () => {
    vi.mocked(factorsApi.list).mockResolvedValue([
      { id: 'f1', name: 'momentum', expression: 'ts_rank(close, 20)', origin: 'seed', project_id: 'p1', agent_id: 'L1-001', level: 1, direction: 1, description: 'momentum', expression_hash: 'h1', validation_status: 'valid', created_at: '2024-01-01' } as any,
    ])
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('momentum')).toBeInTheDocument()
    })
  })
})
