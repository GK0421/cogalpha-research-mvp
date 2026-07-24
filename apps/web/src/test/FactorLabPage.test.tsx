import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import FactorLabPage from '../pages/FactorLabPage'

vi.mock('../api', () => ({
  api: { get: vi.fn(), post: vi.fn(), delete: vi.fn() },
  API_BASE: 'http://127.0.0.1:8765/api',
}))

import { api } from '../api'

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
  beforeEach(() => vi.clearAllMocks())

  it('renders DSL validator section', () => {
    vi.mocked(api.get).mockReturnValue(new Promise(() => {}))
    renderPage()
    expect(screen.getByText(/Factor Lab/i)).toBeInTheDocument()
  })

  it('shows seed factors when loaded', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: [
        { id: 'f1', name: 'momentum', expression: 'ts_rank(close, 20)', origin: 'seed' },
      ],
    })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('momentum')).toBeInTheDocument()
    })
  })

  it('shows empty state', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText(/No factors/i)).toBeInTheDocument()
    })
  })
})
