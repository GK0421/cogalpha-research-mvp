import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from '../App'

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

describe('App', () => {
  it('renders navigation', () => {
    renderWithProviders(<App />)
    expect(screen.getByText(/CogAlpha Studio/i)).toBeInTheDocument()
  })

  it('renders research disclaimer', () => {
    renderWithProviders(<App />)
    expect(screen.getByText(/RESEARCH/i)).toBeInTheDocument()
  })
})
