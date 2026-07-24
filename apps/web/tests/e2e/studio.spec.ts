import { test, expect } from '@playwright/test'

test.describe('CogAlpha Studio E2E', () => {
  test('health check passes', async ({ request }) => {
    const response = await request.get('/api/health')
    expect(response.ok()).toBeTruthy()
    const body = await response.json()
    expect(body.status).toBe('ok')
  })

  test('version endpoint returns version', async ({ request }) => {
    const response = await request.get('/api/version')
    expect(response.ok()).toBeTruthy()
    const body = await response.json()
    expect(body.version).toBeDefined()
  })

  test('create project -> list -> delete', async ({ request }) => {
    // Create
    const createResp = await request.post('/api/projects', {
      data: { name: 'E2E Test Project', description: 'Created by Playwright' },
    })
    expect(createResp.ok()).toBeTruthy()
    const project = await createResp.json()
    expect(project.id).toBeDefined()

    // List
    const listResp = await request.get('/api/projects')
    expect(listResp.ok()).toBeTruthy()
    const projects = await listResp.json()
    expect(projects.length).toBeGreaterThan(0)

    // Delete
    const delResp = await request.delete(`/api/projects/${project.id}?confirm=true`)
    expect(delResp.ok()).toBeTruthy()
  })

  test('factor seed creates 21 factors', async ({ request }) => {
    // Create project
    const projResp = await request.post('/api/projects', {
      data: { name: 'Factor E2E' },
    })
    const project = await projResp.json()

    // Seed factors
    const seedResp = await request.post(`/api/projects/${project.id}/factors/seed`)
    expect(seedResp.ok()).toBeTruthy()
    const factors = await seedResp.json()
    expect(factors.length).toBe(21)

    // Cleanup
    await request.delete(`/api/projects/${project.id}?confirm=true`)
  })

  test('settings endpoint returns defaults', async ({ request }) => {
    const resp = await request.get('/api/settings')
    expect(resp.ok()).toBeTruthy()
    const settings = await resp.json()
    expect(settings).toBeDefined()
  })
})
