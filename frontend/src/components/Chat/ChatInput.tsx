/**
 * ChatInput Component
 *
 * Text input + send button for user messages.
 * Handles Enter key submission and auto-focuses on mount.
 */

import { useState, useRef, useEffect } from 'react'
import type { KeyboardEvent } from 'react'
import { theme } from '../../config/theme'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'Ask about players, teams, injuries, games...',
}: ChatInputProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-focus on mount
  useEffect(() => {
    textareaRef.current?.focus()
  }, [])

  // Auto-resize textarea based on content
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${textarea.scrollHeight}px`
    }
  }, [input])

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input)
      setInput('')
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Enter (but Shift+Enter adds new line)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div
      className="border-t p-4"
      style={{
        backgroundColor: theme.colors.background.surface,
        borderColor: theme.colors.background.elevated,
      }}
    >
      <div className="max-w-4xl mx-auto flex items-end gap-3">
        {/* Text input */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className="w-full px-4 py-3 rounded-xl resize-none focus:outline-none focus:ring-2 transition-all"
            style={{
              backgroundColor: theme.colors.background.elevated,
              color: theme.colors.text.primary,
              borderColor: theme.colors.background.elevated,
              maxHeight: '150px',
            }}
          />

          {/* Character count (optional - shows when approaching limit) */}
          {input.length > 400 && (
            <div
              className="absolute bottom-1 right-2 text-xs"
              style={{ color: theme.colors.text.muted }}
            >
              {input.length}/1000
            </div>
          )}
        </div>

        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          className="px-6 py-3 rounded-xl font-medium transition-all duration-200 hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center gap-2"
          style={{
            backgroundColor: theme.colors.primary,
            color: '#FFFFFF',
          }}
        >
          <SendIcon />
          <span className="hidden sm:inline">Send</span>
        </button>
      </div>

      {/* Hint text */}
      <div
        className="max-w-4xl mx-auto mt-2 text-xs text-center"
        style={{ color: theme.colors.text.muted }}
      >
        Press Enter to send, Shift+Enter for new line
      </div>
    </div>
  )
}

/**
 * Send icon SVG
 */
function SendIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M22 2L11 13" />
      <path d="M22 2L15 22L11 13L2 9L22 2Z" />
    </svg>
  )
}
