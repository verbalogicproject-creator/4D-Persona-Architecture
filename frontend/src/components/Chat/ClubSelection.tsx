import { useState, useEffect } from 'react'
import { theme } from '@/config/theme'
import { Shield } from 'lucide-react'
import { getClubs } from '@/services/api'

interface Club {
  id: string
  name: string
}

interface ClubSelectionProps {
  onSelectClub: (clubId: string) => void
}

// Club colors and identities
const CLUB_COLORS: Record<string, { primary: string; secondary: string; gradient: string }> = {
  'manchester-united': {
    primary: '#DA291C',
    secondary: '#FFD700',
    gradient: 'linear-gradient(135deg, #DA291C 0%, #8B0000 100%)'
  },
  'arsenal': {
    primary: '#EF0107',
    secondary: '#FFFFFF',
    gradient: 'linear-gradient(135deg, #EF0107 0%, #023474 100%)'
  },
  'chelsea': {
    primary: '#034694',
    secondary: '#FFD700',
    gradient: 'linear-gradient(135deg, #034694 0%, #001489 100%)'
  }
}

const CLUB_TAGLINES: Record<string, string> = {
  'manchester-united': 'The Theatre of Dreams. Glory Glory.',
  'arsenal': 'The Invincibles. North London is Red.',
  'chelsea': 'Pride of London. Champions of Europe.'
}

export function ClubSelection({ onSelectClub }: ClubSelectionProps) {
  const [clubs, setClubs] = useState<Club[]>([])
  const [hoveredClub, setHoveredClub] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchClubs = async () => {
      try {
        const data = await getClubs()
        setClubs(data)
      } catch (error) {
        console.error('Failed to fetch clubs:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchClubs()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 mx-auto mb-4"
               style={{ borderColor: theme.colors.primary }}></div>
          <p style={{ color: theme.colors.text.secondary }}>Loading clubs...</p>
        </div>
      </div>
    )
  }

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center p-6"
      style={{ backgroundColor: theme.colors.background.default }}
    >
      <div className="max-w-4xl w-full text-center mb-12">
        <h1
          className="text-5xl font-bold mb-4 animate-fadeIn"
          style={{ color: theme.colors.text.primary }}
        >
          Welcome to Football-AI
        </h1>
        <p
          className="text-xl mb-2"
          style={{ color: theme.colors.text.secondary }}
        >
          Your AI mate who bleeds your club's colors
        </p>
        <p
          className="text-lg italic"
          style={{ color: theme.colors.text.muted }}
        >
          "The young lad on the tip of his toes, holding his breath, a split second before the magic..."
        </p>
      </div>

      <div className="w-full max-w-5xl">
        <h2
          className="text-2xl font-semibold text-center mb-8"
          style={{ color: theme.colors.text.primary }}
        >
          Choose Your Club
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {clubs.map((club, index) => {
            const colors = CLUB_COLORS[club.id] || { primary: theme.colors.primary, secondary: theme.colors.secondary, gradient: theme.colors.primary }
            const tagline = CLUB_TAGLINES[club.id] || ''
            const isHovered = hoveredClub === club.id

            return (
              <button
                key={club.id}
                onClick={() => onSelectClub(club.id)}
                onMouseEnter={() => setHoveredClub(club.id)}
                onMouseLeave={() => setHoveredClub(null)}
                className="relative group cursor-pointer transform transition-all duration-300 hover:scale-105 animate-fadeIn"
                style={{
                  animationDelay: `${index * 150}ms`
                }}
              >
                <div
                  className="rounded-2xl p-8 min-h-[280px] flex flex-col items-center justify-center text-center border-2 transition-all duration-300"
                  style={{
                    background: isHovered ? colors.gradient : theme.colors.background.elevated,
                    borderColor: isHovered ? colors.primary : theme.colors.border.default,
                    boxShadow: isHovered ? `0 20px 40px ${colors.primary}30` : 'none'
                  }}
                >
                  {/* Club Shield Icon */}
                  <div
                    className="mb-6 transform transition-transform duration-300"
                    style={{
                      transform: isHovered ? 'scale(1.1)' : 'scale(1)'
                    }}
                  >
                    <div
                      className="rounded-full p-6"
                      style={{
                        backgroundColor: isHovered ? '#FFFFFF20' : colors.primary + '20'
                      }}
                    >
                      <Shield
                        size={48}
                        style={{
                          color: isHovered ? '#FFFFFF' : colors.primary,
                          strokeWidth: 2
                        }}
                      />
                    </div>
                  </div>

                  {/* Club Name */}
                  <h3
                    className="text-2xl font-bold mb-3 transition-colors duration-300"
                    style={{
                      color: isHovered ? '#FFFFFF' : theme.colors.text.primary
                    }}
                  >
                    {club.name}
                  </h3>

                  {/* Tagline */}
                  <p
                    className="text-sm italic font-medium transition-colors duration-300"
                    style={{
                      color: isHovered ? '#FFFFFF' : theme.colors.text.secondary
                    }}
                  >
                    {tagline}
                  </p>

                  {/* Select Button (appears on hover) */}
                  <div
                    className="mt-6 transition-all duration-300"
                    style={{
                      opacity: isHovered ? 1 : 0,
                      transform: isHovered ? 'translateY(0)' : 'translateY(10px)'
                    }}
                  >
                    <div
                      className="px-6 py-2 rounded-full font-semibold"
                      style={{
                        backgroundColor: '#FFFFFF',
                        color: colors.primary
                      }}
                    >
                      Select My Club →
                    </div>
                  </div>
                </div>
              </button>
            )
          })}
        </div>

        <div
          className="mt-12 text-center text-sm"
          style={{ color: theme.colors.text.muted }}
        >
          <p>Fan at heart. Analyst in nature.</p>
          <p className="mt-2">Football-AI speaks your language, knows your history, feels your passion.</p>
        </div>
      </div>
    </div>
  )
}
