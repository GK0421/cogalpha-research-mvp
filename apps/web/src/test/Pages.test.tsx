import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RunsPage } from '../pages/RunsPage'
import { DashboardPage } from '../pages/DashboardPage'
import { SettingsPage } from '../pages/SettingsPage'

vi.mock('@/api', () => ({
  projectsApi: {
    list: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
  },
  factorsApi: { list: vi.fn(), validate: vi.fn(), seed: vi.fn() },
  datasetsApi: { list: vi.fn(), upload: vi.fn(), delete: vi.fn() },
  runsApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
  },
  reportsApi: { list: vi.fn(), download: vi.fn() },
  settingsApi: {
    get: vi.fn(),
    getAll: vi.fn(),
    update: vi.fn(),
    llm: vi.fn(),
  },
  healthApi: {
    check: vi.fn(),
    capabilities: vi.fn(),
  },
}))

import { runsApi, settingsApi, healthApi, projectsApi } from '@/api'

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
    vi.mocked(projectsApi.list).mockReturnValue(new Promise(() => {}))
    renderWithProviders(<RunsPage />)
    expect(screen.getByText(/Runs/i)).toBeInTheDocument()
  })
})

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders dashboard title', () => {
    vi.mocked(healthApi.check).mockReturnValue(new Promise(() => {}))
    vi.mocked(healthApi.capabilities).mockReturnValue(new Promise(() => {}))
    vi.mocked(projectsApi.list).mockReturnValue(new Promise(() => {}))
    renderWithProviders(<DashboardPage />)
    expect(screen.getByText(/Dashboard/i)).toBeInTheDocument()
  })
})

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders settings header', () => {
    vi.mocked(settingsApi.getAll).mockReturnValue(new Promise(() => {}))
    vi.mocked(settingsApi.llm).mockReturnValue(new Promise(() => {}))
    renderWithProviders(<SettingsPage />)
    expect(screen.getByText(/Settings/i)).toBeInTheDocument()
  })
})
