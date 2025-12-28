/**
 * ChatContainer Component
 *
 * The main chat interface that combines messages and input.
 * Handles auto-scrolling, empty states, and overall layout.
 */

import { useEffect, useRef } from 'react'
import { ChatMessage } from './ChatMessage'
import { ChatInput } from './ChatInput'
import { SmartSuggestions, generateSuggestions } from './SmartSuggestions'
import { theme } from '../../config/theme'
import type { Message } from '../../types'

interface ChatContainerProps {
  messages: Message[]
  onSendMessage: (message: string) => void
  isLoading: boolean
  conversationId: string | null
  onClearChat?: () => void
  clubId?: string
  streamingEnabled?: boolean
  onToggleStreaming?: () => void
}

export function ChatContainer({
  messages,
  onSendMessage,
  isLoading,
  onClearChat,
  streamingEnabled = true,
  onToggleStreaming,
}: ChatContainerProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div
      className="flex flex-col h-screen"
      style={{ backgroundColor: theme.colors.background.main }}
    >
      {/* Header */}
      <header
        className="border-b px-6 py-4 flex items-center justify-between"
        style={{
          backgroundColor: theme.colors.background.surface,
          borderColor: theme.colors.background.elevated,
          height: theme.layout.headerHeight,
        }}
      >
        <div>
          <h1
            className="text-xl font-bold"
            style={{ color: theme.colors.text.primary }}
          >
            ⚽ Soccer AI
          </h1>
          <p className="text-sm" style={{ color: theme.colors.text.secondary }}>
            Your AI-powered football knowledge base
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Streaming toggle button */}
          {onToggleStreaming && (
            <button
              onClick={onToggleStreaming}
              className="px-3 py-2 rounded-lg text-sm font-medium transition-colors hover:opacity-80 flex items-center gap-1"
              style={{
                backgroundColor: streamingEnabled
                  ? theme.colors.primary
                  : theme.colors.background.elevated,
                color: streamingEnabled
                  ? '#fff'
                  : theme.colors.text.secondary,
              }}
              title={`Streaming ${streamingEnabled ? 'ON' : 'OFF'} (type /stream to toggle)`}
            >
              <span>{streamingEnabled ? '⚡' : '📄'}</span>
              <span className="hidden sm:inline">
                {streamingEnabled ? 'Stream' : 'Instant'}
              </span>
            </button>
          )}

          {/* Clear chat button (only show if there are messages) */}
          {messages.length > 0 && onClearChat && (
            <button
              onClick={onClearChat}
              className="px-4 py-2 rounded-lg text-sm font-medium transition-colors hover:opacity-80"
              style={{
                backgroundColor: theme.colors.background.elevated,
                color: theme.colors.text.secondary,
              }}
            >
              Clear Chat
            </button>
          )}
        </div>
      </header>

      {/* Messages area */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto px-4 py-6"
        style={{ backgroundColor: theme.colors.background.main }}
      >
        <div className="max-w-4xl mx-auto">
          {messages.length === 0 ? (
            <EmptyState />
          ) : (
            <>
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </div>

      {/* Smart Suggestions */}
      {!isLoading && (
        <SmartSuggestions
          suggestions={generateSuggestions(messages)}
          onSelect={onSendMessage}
        />
      )}

      {/* Input area */}
      <ChatInput onSend={onSendMessage} disabled={isLoading} />
    </div>
  )
}

/**
 * Empty state - shown when no messages yet
 */
function EmptyState() {
  const suggestions = [
    '🏆 Who is leading the Premier League?',
    '⚽ Is Haaland injured?',
    '📊 Show me Arsenal\'s recent results',
    '🗓️ What games are today?',
    '🏥 Which players are currently injured?',
  ]

  return (
    <div className="text-center py-12">
      <div className="mb-8">
        <div
          className="text-6xl mb-4"
          style={{ color: theme.colors.primary }}
        >
          ⚽
        </div>
        <h2
          className="text-2xl font-bold mb-2"
          style={{ color: theme.colors.text.primary }}
        >
          Welcome to Soccer AI
        </h2>
        <p
          className="text-lg"
          style={{ color: theme.colors.text.secondary }}
        >
          Ask me anything about football - players, teams, injuries, games, and more!
        </p>
      </div>

      {/* Suggestion chips */}
      <div className="flex flex-wrap gap-2 justify-center max-w-2xl mx-auto">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            className="px-4 py-2 rounded-full text-sm transition-all hover:scale-105"
            style={{
              backgroundColor: theme.colors.background.surface,
              color: theme.colors.text.secondary,
            }}
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  )
}
