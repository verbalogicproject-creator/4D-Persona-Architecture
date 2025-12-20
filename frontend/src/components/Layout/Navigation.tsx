import { NavLink } from 'react-router-dom'
import { Home, Trophy, Users, MessageCircle } from 'lucide-react'
import { theme } from '@/config/theme'

const navItems = [
  { to: '/', label: 'Games', icon: Home },
  { to: '/standings', label: 'Standings', icon: Trophy },
  { to: '/teams', label: 'Teams', icon: Users },
  { to: '/chat', label: 'Chat', icon: MessageCircle },
]

export function Navigation() {
  return (
    <nav
      className="sticky top-0 z-50 border-b"
      style={{
        backgroundColor: theme.colors.background.elevated,
        borderColor: theme.colors.border.subtle,
      }}
    >
      <div className="container mx-auto px-4 max-w-7xl">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center space-x-2">
            <div
              className="text-2xl font-bold"
              style={{ color: theme.colors.primary }}
            >
              ⚽ Soccer AI
            </div>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center space-x-1">
            {navItems.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                    isActive ? 'font-semibold' : 'font-medium'
                  }`
                }
                style={({ isActive }) => ({
                  backgroundColor: isActive
                    ? theme.colors.primary + '20'
                    : 'transparent',
                  color: isActive
                    ? theme.colors.primary
                    : theme.colors.text.secondary,
                })}
              >
                <Icon size={20} />
                <span className="hidden sm:inline">{label}</span>
              </NavLink>
            ))}
          </div>
        </div>
      </div>
    </nav>
  )
}
