import { describe, it, expect } from 'vitest'
import api from '../api'

describe('API client', () => {
  it('exports default api instance', () => {
    expect(api).toBeDefined()
  })
})
