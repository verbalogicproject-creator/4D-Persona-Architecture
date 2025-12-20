/**
 * ChatMessage Component
 *
 * Displays a single message bubble (user or assistant).
 * Bot messages with sources render rich visual elements.
 */

import { theme } from '../../config/theme'
import { RichChatMessage } from './RichChatMessage'
import type { Message } from '../../types'

interface ChatMessageProps {
  message: Message
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'
  const hasRichContent = !isUser && message.sources && message.sources.length > 0

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 animate-fadeIn`}
    >
      <div
        className={`${hasRichContent ? 'max-w-[90%]' : 'max-w-[80%]'} rounded-2xl px-4 py-3 shadow-md transition-all duration-200 hover:shadow-lg ${
          isUser
            ? 'rounded-br-sm'
            : 'rounded-bl-sm'
        }`}
        style={{
          backgroundColor: isUser
            ? theme.colors.bubbles.user
            : theme.colors.bubbles.bot,
          color: isUser
            ? theme.colors.bubbles.userText
            : theme.colors.bubbles.botText,
        }}
      >
        {/* Message content */}
        <div className="text-sm md:text-base leading-relaxed whitespace-pre-wrap break-words">
          {message.isLoading ? (
            <TypingIndicator />
          ) : hasRichContent ? (
            <RichChatMessage content={message.content} sources={message.sources} />
          ) : (
            message.content
          )}
        </div>

        {/* Timestamp */}
        <div
          className="text-xs mt-1 opacity-70"
          style={{
            color: isUser
              ? theme.colors.bubbles.userText
              : theme.colors.text.secondary,
          }}
        >
          {formatTimestamp(message.timestamp)}
        </div>
      </div>
    </div>
  )
}

/**
 * Typing indicator (animated dots)
 */
function TypingIndicator() {
  return (
    <div className="flex items-center space-x-1">
      <div
        className="w-2 h-2 rounded-full animate-bounce"
        style={{
          backgroundColor: theme.colors.text.secondary,
          animationDelay: '0ms',
        }}
      />
      <div
        className="w-2 h-2 rounded-full animate-bounce"
        style={{
          backgroundColor: theme.colors.text.secondary,
          animationDelay: '150ms',
        }}
      />
      <div
        className="w-2 h-2 rounded-full animate-bounce"
        style={{
          backgroundColor: theme.colors.text.secondary,
          animationDelay: '300ms',
        }}
      />
    </div>
  )
}

/**
 * Format timestamp for display
 */
function formatTimestamp(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`

  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`

  return date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })
}
