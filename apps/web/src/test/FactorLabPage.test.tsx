import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { FactorLabPage } from '../pages/FactorLabPage'

vi.mock('@/api', () => ({
  projectsApi: { list: vi.fn().mockResolvedValue([]), create: vi.fn().mockResolvedValue({}), delete: vi.fn().mockResolvedValue(undefined) },
  factorsApi: {
    list: vi.fn().mockResolvedValue([]),
    validate: vi.fn().mockResolvedValue({}),
    seed: vi.fn().mockResolvedValue({}),
  },
  datasetsApi: { list: vi.fn().mockResolvedValue([]), upload: vi.fn().mockResolvedValue({}), delete: vi.fn().mockResolvedValue(undefined) },
  runsApi: { list: vi.fn().mockResolvedValue([]), get: vi.fn().mockResolvedValue({}), create: vi.fn().mockResolvedValue({}) },
  reportsApi: { list: vi.fn().mockResolvedValue([]), download: vi.fn().mockResolvedValue({}) },
  settingsApi: { get: vi.fn().mockResolvedValue({}), getAll: vi.fn().mockResolvedValue({}), update: vi.fn().mockResolvedValue({}), llm: vi.fn().mockResolvedValue({}) },
  healthApi: { check: vi.fn().mockResolvedValue({}), capabilities: vi.fn().mockResolvedValue({}) },
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
    renderPage()
    expect(screen.getByText(/Factor Lab/i)).toBeInTheDocument()
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
