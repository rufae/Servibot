import { useState, useEffect } from 'react'
import { Send } from 'lucide-react'
import { chatService } from '../services'
import { API_BASE_URL } from '../services/api'

export default function ChatInput({ setMessages, setAgentActivity, disabled = false, onTranscription, onSend, isLoading: isLoadingProp = false, transcribedText = '' }) {
  const [input, setInput] = useState('')
  const [localLoading, setLocalLoading] = useState(false)

  // If parent provides transcribed text (from VoiceRecorder), fill input
  useEffect(() => {
    if (transcribedText && transcribedText.trim()) {
      setInput(transcribedText)
    }
  }, [transcribedText])

  const effectiveLoading = isLoadingProp || localLoading

  const handleSend = async () => {
    if (!input.trim() || effectiveLoading) return

    const textToSend = input
    setInput('')

    // If parent provided onSend, delegate to it so parent can set isLoading
    if (typeof onSend === 'function') {
      await onSend(textToSend)
      return
    }

    // Fallback: local send logic (keeps backward compatibility)
    const userMessage = {
      role: 'user',
      content: textToSend,
      timestamp: new Date().toISOString(),
    }

    setMessages(prev => [...prev, userMessage])
    setLocalLoading(true)

    try {
      const result = await chatService.sendMessage(textToSend)

      if (!result.success) {
        throw new Error(result.error)
      }

      const response = result.data
      const assistantMessage = {
        role: 'assistant',
        content: response.response,
        sources: response.sources || null,
        timestamp: response.timestamp,
        plan: response.plan,
      }

      setMessages(prev => [...prev, assistantMessage])

      if (response.plan && Array.isArray(response.plan)) {
        setAgentActivity(response.plan)
      }

      if (response.generated_file) {
        const { filename, download_url } = response.generated_file
        const downloadLink = document.createElement('a')
        downloadLink.href = `${API_BASE_URL}${download_url}`
        downloadLink.download = filename
        document.body.appendChild(downloadLink)
        downloadLink.click()
        if (downloadLink.parentNode) document.body.removeChild(downloadLink)
      }
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
        error: true,
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLocalLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="px-4 sm:px-6 py-3 sm:py-4 border-t border-dark-800 bg-dark-900/60 backdrop-blur-sm">
      <div className="flex space-x-2 sm:space-x-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Escribe tu mensaje..."
          disabled={effectiveLoading || disabled}
          aria-label="Escribe tu mensaje"
          className="flex-1 bg-dark-800/60 backdrop-blur-sm text-white rounded-xl px-4 sm:px-5 py-2.5 sm:py-3 text-sm sm:text-base focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed border border-dark-700 focus:border-primary-500 transition-all placeholder-dark-500"
        />

        <button
          onClick={handleSend}
          disabled={effectiveLoading || !input.trim()}
          aria-label="Enviar mensaje"
          className="bg-gradient-to-r from-primary-600 to-secondary-600 hover:from-primary-500 hover:to-secondary-500 disabled:from-dark-700 disabled:to-dark-800 disabled:cursor-not-allowed text-white rounded-xl px-4 sm:px-6 py-2.5 sm:py-3 flex items-center space-x-2 transition-all shadow-glow hover:shadow-glow-lg disabled:shadow-none transform hover:scale-105 disabled:scale-100 active:scale-95"
        >
          <Send className="w-4 h-4 sm:w-5 sm:h-5" />
          <span className="font-medium hidden sm:inline">Enviar</span>
        </button>
      </div>
    </div>
  )
}
