import { useState } from 'react'
import { chatService, voiceService } from '../services'
import { API_BASE_URL } from '../services/api'

/**
 * Custom hook for managing chat functionality
 */
export function useChat(setAgentActivity) {
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [audioUrlForMessage, setAudioUrlForMessage] = useState({})

  const sendMessage = async (input) => {
    if (!input.trim() || isLoading) return

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    try {
      const result = await chatService.sendMessage(input)

      if (!result.success) {
        throw new Error(result.error)
      }

      const response = result.data
      const assistantMessage = {
        role: 'assistant',
        content: response.response,
        sources: response.sources || null,
        timestamp: response.timestamp,
        plan: response.plan
      }

      setMessages(prev => [...prev, assistantMessage])

      // Update agent activity timeline
      if (response.plan) {
        setAgentActivity(prev => [...prev, ...response.plan])
      }

      // Auto-download generated file if available
      if (response.generated_file) {
        const { filename, download_url } = response.generated_file
        console.log(`Auto-downloading generated file: ${filename}`)
        
        // Trigger download
        const downloadLink = document.createElement('a')
        downloadLink.href = `${API_BASE_URL}${download_url}`
        downloadLink.download = filename
        document.body.appendChild(downloadLink)
        downloadLink.click()
        if (downloadLink.parentNode) {
          document.body.removeChild(downloadLink)
        }
        
        console.log(`Download triggered for: ${filename}`)
      }

      return { success: true, message: assistantMessage }
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
        error: true
      }
      setMessages(prev => [...prev, errorMessage])
      return { success: false, error: error.message }
    } finally {
      setIsLoading(false)
    }
  }

  const generateTTS = async (messageIndex, messageContent) => {
    try {
      const result = await voiceService.synthesize(messageContent, 'es', 'gtts')

      if (result.success && result.data.status === 'success') {
        setAudioUrlForMessage(prev => ({
          ...prev,
          [messageIndex]: result.data.audio_url
        }))
        return { success: true, audioUrl: result.data.audio_url }
      }
      
      return { success: false }
    } catch (error) {
      console.error('Error generating TTS:', error)
      return { success: false, error: error.message }
    }
  }

  return {
    messages,
    setMessages,
    isLoading,
    sendMessage,
    audioUrlForMessage,
    generateTTS,
  }
}
