import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ProjectsPage } from '../pages/ProjectsPage'

// Mock the named exports from api module
vi.mock('@/api', () => ({
  projectsApi: {
    list: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
  },
  factorsApi: { list: vi.fn(), validate: vi.fn(), seed: vi.fn() },
  datasetsApi: { list: vi.fn(), upload: vi.fn(), delete: vi.fn() },
  runsApi: { list: vi.fn(), get: vi.fn(), create: vi.fn() },
  reportsApi: { list: vi.fn(), download: vi.fn() },
  settingsApi: { get: vi.fn(), update: vi.fn() },
  healthApi: { check: vi.fn() },
}))

// Import after mock
import { projectsApi } from '@/api'

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ProjectsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ProjectsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders projects header', () => {
    vi.mocked(projectsApi.list).mockReturnValue(new Promise(() => {}))
    renderPage()
    expect(screen.getByText(/Projects/i)).toBeInTheDocument()
  })

  it('shows empty state when no projects', async () => {
    vi.mocked(projectsApi.list).mockResolvedValue([])
    renderPage()
    await waitFor(() => {
      expect(screen.getByText(/No projects/i)).toBeInTheDocument()
    })
  })

  it('shows project list', async () => {
    vi.mocked(projectsApi.list).mockResolvedValue([
      { id: 'p1', name: 'Test Project', description: '', market: 'A-stock', status: 'active', default_config: {}, created_at: '2024-01-01', updated_at: '2024-01-01' },
    ] as any)
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Test Project')).toBeInTheDocument()
    })
  })
})
