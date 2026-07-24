import { describe, it, expect } from 'vitest'
import { api, API_BASE } from '../api'

describe('API client', () => {
  it('exports API_BASE', () => {
    expect(API_BASE).toBeDefined()
    expect(typeof API_BASE).toBe('string')
  })

  it('exports api axios instance', () => {
    expect(api).toBeDefined()
    expect(api.get).toBeDefined()
    expect(api.post).toBeDefined()
    expect(api.delete).toBeDefined()
    expect(api.patch).toBeDefined()
  })
})
