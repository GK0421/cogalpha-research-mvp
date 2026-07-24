import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import RunsPage from '../pages/RunsPage'
import DashboardPage from '../pages/DashboardPage'
import SettingsPage from '../pages/SettingsPage'

vi.mock('../api', () => ({
  api: { get: vi.fn(), post: vi.fn(), delete: vi.fn(), patch: vi.fn() },
  API_BASE: 'http://127.0.0.1:8765/api',
}))

import { api } from '../api'

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('RunsPage', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders runs header', () => {
    vi.mocked(api.get).mockReturnValue(new Promise(() => {}))
    renderWithProviders(<RunsPage />)
    expect(screen.getByText(/Runs/i)).toBeInTheDocument()
  })

  it('shows empty state', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })
    renderWithProviders(<RunsPage />)
    await waitFor(() => {
      expect(screen.getByText(/No runs/i)).toBeInTheDocument()
    })
  })
})

describe('DashboardPage', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders dashboard title', () => {
    vi.mocked(api.get).mockReturnValue(new Promise(() => {}))
    renderWithProviders(<DashboardPage />)
    expect(screen.getByText(/Dashboard/i)).toBeInTheDocument()
  })

  it('shows stats when loaded', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: { projects: 3, runs: 5, factors: 21 },
    })
    renderWithProviders(<DashboardPage />)
    await waitFor(() => {
      expect(screen.getByText(/3/)).toBeInTheDocument()
    })
  })
})

describe('SettingsPage', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders settings header', () => {
    vi.mocked(api.get).mockReturnValue(new Promise(() => {}))
    renderWithProviders(<SettingsPage />)
    expect(screen.getByText(/Settings/i)).toBeInTheDocument()
  })
})
