import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { FactorLabPage } from '../pages/FactorLabPage'
import factorsApi from '../api'

vi.mock('../api', () => ({
  default: {
    list: vi.fn(),
    validate: vi.fn(),
    seed: vi.fn(),
  },
}))

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
      { id: 'f1', name: 'momentum', expression: 'ts_rank(close, 20)', origin: 'seed' },
    ])
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('momentum')).toBeInTheDocument()
    })
  })
})
