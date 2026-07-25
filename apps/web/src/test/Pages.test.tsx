import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RunsPage } from '../pages/RunsPage'
import { DashboardPage } from '../pages/DashboardPage'
import { SettingsPage } from '../pages/SettingsPage'

vi.mock('@/api', () => ({
  projectsApi: {
    list: vi.fn().mockResolvedValue([]),
    create: vi.fn().mockResolvedValue({}),
    delete: vi.fn().mockResolvedValue(undefined),
  },
  factorsApi: { list: vi.fn().mockResolvedValue([]), validate: vi.fn().mockResolvedValue({}), seed: vi.fn().mockResolvedValue({}) },
  datasetsApi: { list: vi.fn().mockResolvedValue([]), upload: vi.fn().mockResolvedValue({}), delete: vi.fn().mockResolvedValue(undefined) },
  runsApi: {
    list: vi.fn().mockResolvedValue([]),
    get: vi.fn().mockResolvedValue({}),
    create: vi.fn().mockResolvedValue({}),
  },
  reportsApi: { list: vi.fn().mockResolvedValue([]), download: vi.fn().mockResolvedValue({}) },
  settingsApi: {
    get: vi.fn().mockResolvedValue({}),
    getAll: vi.fn().mockResolvedValue({}),
    update: vi.fn().mockResolvedValue({}),
    llm: vi.fn().mockResolvedValue({}),
  },
  healthApi: {
    check: vi.fn().mockResolvedValue({}),
    capabilities: vi.fn().mockResolvedValue({}),
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
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders runs header', () => {
    renderWithProviders(<RunsPage />)
    expect(screen.getByText(/Research Runs/i)).toBeInTheDocument()
  })
})

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders dashboard title', () => {
    renderWithProviders(<DashboardPage />)
    expect(screen.getByText(/Dashboard/i)).toBeInTheDocument()
  })
})

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders settings header', () => {
    renderWithProviders(<SettingsPage />)
    expect(screen.getByText('Settings', { selector: 'h1' })).toBeInTheDocument()
  })
})
