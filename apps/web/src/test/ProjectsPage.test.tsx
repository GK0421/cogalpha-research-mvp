import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ProjectsPage } from '../pages/ProjectsPage'
import projectsApi from '../api'

vi.mock('../api', () => ({
  default: {
    list: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
  },
}))

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
      { id: 'p1', name: 'Test Project', created_at: '2024-01-01' },
    ])
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Test Project')).toBeInTheDocument()
    })
  })
})
