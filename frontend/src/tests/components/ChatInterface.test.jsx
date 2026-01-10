import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ChatInterface from '../../components/ChatInterface'

// Mock services
vi.mock('../../services', () => ({
  chatService: {
    sendMessage: vi.fn(() => Promise.resolve({
      success: true,
      data: {
        response: 'Test response',
        timestamp: new Date().toISOString(),
        sources: [],
        plan: []
      }
    }))
  },
  voiceService: {
    synthesize: vi.fn(() => Promise.resolve({
      success: true,
      data: {
        status: 'success',
        audio_url: 'test-audio.mp3'
      }
    }))
  }
}))

describe('ChatInterface', () => {
  const mockSetMessages = vi.fn()
  const mockSetAgentActivity = vi.fn()

  it('renders chat interface with initial empty state', () => {
    render(
      <ChatInterface 
        messages={[]} 
        setMessages={mockSetMessages}
        setAgentActivity={mockSetAgentActivity}
      />
    )

    expect(screen.getByText(/¡Hola! Soy ServiBot/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Escribe tu mensaje/i)).toBeInTheDocument()
  })

  it('displays input field and send button', () => {
    render(
      <ChatInterface 
        messages={[]} 
        setMessages={mockSetMessages}
        setAgentActivity={mockSetAgentActivity}
      />
    )

    const input = screen.getByPlaceholderText(/Escribe tu mensaje/i)
    const sendButton = screen.getByRole('button', { name: /Enviar mensaje/i })

    expect(input).toBeInTheDocument()
    expect(sendButton).toBeInTheDocument()
  })

  it('allows typing in the input field', () => {
    render(
      <ChatInterface 
        messages={[]} 
        setMessages={mockSetMessages}
        setAgentActivity={mockSetAgentActivity}
      />
    )

    const input = screen.getByPlaceholderText(/Escribe tu mensaje/i)
    fireEvent.change(input, { target: { value: 'Hello' } })

    expect(input.value).toBe('Hello')
  })

  it('disables send button when input is empty', () => {
    render(
      <ChatInterface 
        messages={[]} 
        setMessages={mockSetMessages}
        setAgentActivity={mockSetAgentActivity}
      />
    )

    const sendButton = screen.getByRole('button', { name: /Enviar mensaje/i })
    expect(sendButton).toBeDisabled()
  })

  it('enables send button when input has text', () => {
    render(
      <ChatInterface 
        messages={[]} 
        setMessages={mockSetMessages}
        setAgentActivity={mockSetAgentActivity}
      />
    )

    const input = screen.getByPlaceholderText(/Escribe tu mensaje/i)
    const sendButton = screen.getByRole('button', { name: /Enviar mensaje/i })

    fireEvent.change(input, { target: { value: 'Test message' } })
    expect(sendButton).not.toBeDisabled()
  })

  it('renders messages when provided', () => {
    const messages = [
      {
        role: 'user',
        content: 'Hello',
        timestamp: new Date().toISOString()
      },
      {
        role: 'assistant',
        content: 'Hi there!',
        timestamp: new Date().toISOString()
      }
    ]

    render(
      <ChatInterface 
        messages={messages} 
        setMessages={mockSetMessages}
        setAgentActivity={mockSetAgentActivity}
      />
    )

    expect(screen.getByText('Hello')).toBeInTheDocument()
    expect(screen.getByText('Hi there!')).toBeInTheDocument()
  })
})
