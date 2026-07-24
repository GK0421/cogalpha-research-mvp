import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ProjectsPage from '../pages/ProjectsPage'

vi.mock('../api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
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
        <ProjectsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ProjectsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state', () => {
    vi.mocked(api.get).mockReturnValue(new Promise(() => {}))
    renderPage()
    expect(screen.getByText(/Loading/i)).toBeInTheDocument()
  })

  it('shows empty state when no projects', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText(/No projects/i)).toBeInTheDocument()
    })
  })

  it('shows project list', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: [
        { id: 'p1', name: 'Test Project', created_at: '2024-01-01' },
      ],
    })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Test Project')).toBeInTheDocument()
    })
  })

  it('shows error state on failure', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('Network error'))
    renderPage()
    await waitFor(() => {
      expect(screen.getByText(/error|Error|failed|Failed/i)).toBeInTheDocument()
    })
  })
})
