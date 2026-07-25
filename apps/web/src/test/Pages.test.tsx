import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RunsPage } from '../pages/RunsPage'
import { DashboardPage } from '../pages/DashboardPage'
import { SettingsPage } from '../pages/SettingsPage'
import api from '../api'

vi.mock('../api', () => ({
  default: {
    list: vi.fn(),
    get: vi.fn(),
    getAll: vi.fn(),
  },
}))

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
    vi.mocked(api.list).mockReturnValue(new Promise(() => {}))
    renderWithProviders(<RunsPage />)
    expect(screen.getByText(/Runs/i)).toBeInTheDocument()
  })
})

describe('DashboardPage', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders dashboard title', () => {
    vi.mocked(api.getAll).mockReturnValue(new Promise(() => {}))
    renderWithProviders(<DashboardPage />)
    expect(screen.getByText(/Dashboard/i)).toBeInTheDocument()
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
