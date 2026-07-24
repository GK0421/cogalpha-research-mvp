import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projectsApi } from '@/api'
import type { ProjectCreate } from '@/types'
import { Link } from 'react-router-dom'

export function ProjectsPage() {
  const queryClient = useQueryClient()
  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
  })
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState<ProjectCreate>({
    name: '',
    description: '',
    market: 'A_STOCK',
  })

  const createMutation = useMutation({
    mutationFn: (data: ProjectCreate) => projectsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setShowCreate(false)
      setForm({ name: '', description: '', market: 'A_STOCK' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => projectsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Projects</h1>
        <button
          className="btn-primary"
          onClick={() => setShowCreate(!showCreate)}
        >
          {showCreate ? 'Cancel' : '+ New Project'}
        </button>
      </div>

      {showCreate && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Create New Project</h2>
          </div>
          <div className="form-group">
            <label className="form-label">Project Name</label>
            <input
              className="form-input"
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
              placeholder="My Research Project"
            />
          </div>
          <div className="form-group">
            <label className="form-label">Description</label>
            <textarea
              className="form-textarea"
              value={form.description}
              onChange={e => setForm({ ...form, description: e.target.value })}
              placeholder="Project description..."
            />
          </div>
          <div className="form-group">
            <label className="form-label">Market</label>
            <select
              className="form-select"
              value={form.market}
              onChange={e => setForm({ ...form, market: e.target.value })}
            >
              <option value="A_STOCK">A-Share (China)</option>
              <option value="US_STOCK">US Stock</option>
              <option value="HK_STOCK">HK Stock</option>
              <option value="GLOBAL">Global</option>
            </select>
          </div>
          <button
            className="btn-primary"
            onClick={() => createMutation.mutate(form)}
            disabled={!form.name || createMutation.isPending}
          >
            {createMutation.isPending ? 'Creating...' : 'Create Project'}
          </button>
        </div>
      )}

      {isLoading ? (
        <div className="loading">Loading projects...</div>
      ) : projects && projects.length > 0 ? (
        <div className="card">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Market</th>
                <th>Status</th>
                <th>Description</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {projects.map(p => (
                <tr key={p.id}>
                  <td>
                    <Link to={`/projects/${p.id}`}>{p.name}</Link>
                  </td>
                  <td>{p.market}</td>
                  <td>
                    <span className="badge badge-info">{p.status}</span>
                  </td>
                  <td>{p.description || '---'}</td>
                  <td>{p.created_at?.split('T')[0] ?? '---'}</td>
                  <td>
                    <button
                      className="btn-danger btn-sm"
                      onClick={() => {
                        if (confirm(`Delete project "${p.name}"?`)) {
                          deleteMutation.mutate(p.id)
                        }
                      }}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon">[ ]</div>
            <p>No projects yet. Click "New Project" to create one.</p>
          </div>
        </div>
      )}
    </div>
  )
}
