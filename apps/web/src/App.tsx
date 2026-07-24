import { Routes, Route, NavLink } from 'react-router-dom'
import { DashboardPage } from '@/pages/DashboardPage'
import { ProjectsPage } from '@/pages/ProjectsPage'
import { ProjectDetailPage } from '@/pages/ProjectDetailPage'
import { FactorLabPage } from '@/pages/FactorLabPage'
import { RunsPage } from '@/pages/RunsPage'
import { RunDetailPage } from '@/pages/RunDetailPage'
import { SettingsPage } from '@/pages/SettingsPage'

const navItems = [
  { to: '/', label: 'Dashboard', icon: '[D]' },
  { to: '/projects', label: 'Projects', icon: '[P]' },
  { to: '/factor-lab', label: 'Factor Lab', icon: '[F]' },
  { to: '/runs', label: 'Runs', icon: '[R]' },
  { to: '/settings', label: 'Settings', icon: '[S]' },
]

export default function App() {
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-title">CogAlpha Studio</div>
          <div className="sidebar-subtitle">v0.2.0 | Research Only</div>
        </div>
        <ul className="sidebar-nav">
          {navItems.map(item => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                className={({ isActive }) => isActive ? 'active' : ''}
                end={item.to === '/'}
              >
                {item.icon} {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </aside>
      <main className="main-content">
        <div className="disclaimer">
          RESEARCH_BACKTEST_ONLY | NO_LIVE_TRADING | NOT_INVESTMENT_ADVICE
        </div>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
          <Route path="/factor-lab" element={<FactorLabPage />} />
          <Route path="/runs" element={<RunsPage />} />
          <Route path="/runs/:runId" element={<RunDetailPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  )
}
