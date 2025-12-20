/**
 * useChat Hook
 *
 * Manages chat state and handles sending/receiving messages.
 * This is the core logic that powers the chat interface.
 */

import { useState, useCallback } from 'react'
import type { Message, ChatState } from '../types'
import { sendChatMessage } from '../services/api'

export function useChat(clubId?: string) {
  const [state, setState] = useState<ChatState>({
    messages: [],
    conversationId: null,
    isLoading: false,
    error: null,
  })

  /**
   * Send a message to the AI with fan persona
   */
  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return

    // Create user message
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    }

    // Create placeholder for bot response (shows "typing" indicator)
    const botMessageId = crypto.randomUUID()
    const botMessagePlaceholder: Message = {
      id: botMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: true,
    }

    // Update UI immediately with user message + loading indicator
    setState((prev) => ({
      ...prev,
      messages: [...prev.messages, userMessage, botMessagePlaceholder],
      isLoading: true,
      error: null,
    }))

    try {
      // Call backend API with fan persona
      const response = await sendChatMessage(
        content,
        state.conversationId || undefined,
        clubId  // Fan persona system
      )

      // Update bot message with actual response including sources
      setState((prev) => ({
        ...prev,
        messages: prev.messages.map((msg) =>
          msg.id === botMessageId
            ? {
                ...msg,
                content: response.response,
                sources: response.sources,
                isLoading: false,
              }
            : msg
        ),
        conversationId: response.conversation_id,
        isLoading: false,
      }))
    } catch (error) {
      // Handle error - show error message
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to send message'

      setState((prev) => ({
        ...prev,
        messages: prev.messages.map((msg) =>
          msg.id === botMessageId
            ? {
                ...msg,
                content: `❌ Error: ${errorMessage}`,
                isLoading: false,
              }
            : msg
        ),
        isLoading: false,
        error: errorMessage,
      }))
    }
  }, [state.conversationId, clubId])

  /**
   * Clear all messages and start a new conversation
   */
  const clearChat = useCallback(() => {
    setState({
      messages: [],
      conversationId: null,
      isLoading: false,
      error: null,
    })
  }, [])

  /**
   * Retry the last failed message
   */
  const retryLastMessage = useCallback(() => {
    const lastUserMessage = [...state.messages]
      .reverse()
      .find((msg) => msg.role === 'user')

    if (lastUserMessage) {
      // Remove failed bot response
      setState((prev) => ({
        ...prev,
        messages: prev.messages.slice(0, -1),
      }))
      // Retry
      sendMessage(lastUserMessage.content)
    }
  }, [state.messages, sendMessage])

  return {
    messages: state.messages,
    conversationId: state.conversationId,
    isLoading: state.isLoading,
    error: state.error,
    sendMessage,
    clearChat,
    retryLastMessage,
  }
}
