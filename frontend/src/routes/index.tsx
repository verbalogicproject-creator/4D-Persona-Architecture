import { Routes, Route } from 'react-router-dom'
import { AppLayout } from '@/components/Layout/AppLayout'
import { Dashboard } from '@/pages/Dashboard'
import { Standings } from '@/pages/Standings'
import { Teams } from '@/pages/Teams'
import { TeamDetail } from '@/pages/TeamDetail'
import { Chat } from '@/pages/Chat'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="standings" element={<Standings />} />
        <Route path="teams" element={<Teams />} />
        <Route path="teams/:id" element={<TeamDetail />} />
        <Route path="chat" element={<Chat />} />
      </Route>
    </Routes>
  )
}
