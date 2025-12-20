import { Outlet } from 'react-router-dom'
import { Navigation } from './Navigation'
import { theme } from '@/config/theme'

export function AppLayout() {
  return (
    <div
      className="min-h-screen flex flex-col"
      style={{ backgroundColor: theme.colors.background.main }}
    >
      <Navigation />
      <main className="flex-1 container mx-auto px-4 py-6 max-w-7xl">
        <Outlet />
      </main>
    </div>
  )
}
