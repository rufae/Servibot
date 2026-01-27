import { useState, useEffect } from 'react'
import { Send, FileDown, Mic, MicOff, Sparkles, Trash2 } from 'lucide-react'
import VoiceRecorder from './VoiceRecorder'
import FileGenerator from './FileGenerator'
import ChatHistory from './ChatHistory'
import { chatService } from '../services'
import { API_BASE_URL } from '../services/api'
import ConfirmationModal from './ConfirmationModal'
import { api } from '../services/api'
import Swal from 'sweetalert2'

export default function ChatInterface({ messages, setMessages, setAgentActivity }) {
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showVoiceRecorder, setShowVoiceRecorder] = useState(false)
  const [showFileGenerator, setShowFileGenerator] = useState(false)
  const [pendingAction, setPendingAction] = useState(null)

  // Ensure messages is always an array
  const safeMessages = Array.isArray(messages) ? messages : []
  
  // Load messages from localStorage on mount
  useEffect(() => {
    const savedMessages = localStorage.getItem('servibot_conversation')
    if (savedMessages) {
      try {
        const parsed = JSON.parse(savedMessages)
        if (Array.isArray(parsed) && parsed.length > 0) {
          setMessages(parsed)
        }
      } catch (e) {
        console.warn('Failed to load saved conversation:', e)
      }
    }
  }, [])
  
  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (safeMessages.length > 0) {
      localStorage.setItem('servibot_conversation', JSON.stringify(safeMessages))
    }
  }, [safeMessages])
  
  const handleClearConversation = async () => {
    const result = await Swal.fire({
      title: '¿Eliminar conversación?',
      text: 'Se borrará todo el historial de mensajes',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#ef4444',
      cancelButtonColor: '#6b7280',
      confirmButtonText: 'Sí, eliminar',
      cancelButtonText: 'Cancelar',
      background: 'var(--bg-panel)',
      color: 'var(--text-primary)'
    })
    
    if (result.isConfirmed) {
      setMessages([])
      localStorage.removeItem('servibot_conversation')
      Swal.fire({
        icon: 'success',
        title: 'Conversación eliminada',
        timer: 1500,
        showConfirmButton: false,
        background: 'var(--bg-panel)',
        color: 'var(--text-primary)'
      })
    }
  }

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Prepare conversation history (last 10 messages for context)
      const historyForContext = safeMessages.slice(-10).map(msg => ({
        role: msg.role,
        content: msg.content
      }))
      
      const result = await chatService.sendMessage(input, {}, historyForContext)

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

      // If backend indicates a pending confirmation, show modal
      if (response.pending_confirmation) {
        console.log('📬 Pending confirmation received, opening modal')
        setPendingAction(response.pending_confirmation)
      }

      // Update agent activity timeline
      if (response.plan && Array.isArray(response.plan)) {
        setAgentActivity(response.plan)
      }

      // Emit calendar update event if calendar was modified
      // Check if execution results include calendar operations
      let calendarModified = false
      if (response.execution?.results) {
        calendarModified = response.execution.results.some(result => 
          result.tool_used === 'calendar' && 
          result.status === 'success' &&
          result.result?.success
        )
      }
      
      // Fallback to text matching if no execution data
      if (!calendarModified) {
        const contentLower = response.response?.toLowerCase() || ''
        const calendarKeywords = [
          'evento creado', 'evento actualizado', 'evento eliminado',
          'evento modificado', 'evento borrado', 'calendario actualizado',
          'event created', 'event updated', 'event deleted'
        ]
        calendarModified = calendarKeywords.some(kw => contentLower.includes(kw))
      }
      
      if (calendarModified) {
        console.log('📅 Calendar modification detected, emitting update event...')
        window.dispatchEvent(new CustomEvent('calendarUpdated'))
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
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
        error: true
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleTranscription = (transcribedText) => {
    setInput(transcribedText)
    setShowVoiceRecorder(false)
  }

  return (
    <div className="glass-effect rounded-3xl shadow-2xl border border-white/10 flex flex-col h-[500px] sm:h-[650px] overflow-hidden backdrop-blur-xl bg-slate-800/40">
      {/* Chat Header */}
      <div className="px-5 sm:px-6 py-4 sm:py-5 border-b border-white/10 bg-gradient-to-r from-primary-500/20 via-secondary-500/20 to-accent-500/20 backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative group">
              <div className="absolute inset-0 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-xl blur-md opacity-50 group-hover:opacity-75 transition-opacity"></div>
              <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center shadow-glow">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
            </div>
            <div>
              <h2 className="text-lg sm:text-xl font-bold text-white">Chat con ServiBot</h2>
              <p className="text-xs text-dark-400">Hazme preguntas sobre tus documentos</p>
            </div>
          </div>
          
          {/* Header Actions - grouped so buttons stay together */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleClearConversation}
              className="p-2 sm:p-2.5 rounded-xl bg-dark-900/50 hover:bg-red-500/20 text-dark-300 hover:text-red-400 transition-all border border-dark-800 hover:border-red-500/30 hover-lift"
              title="Eliminar conversación"
            >
              <Trash2 className="w-4 h-4 sm:w-5 sm:h-5" />
            </button>
            <button
              onClick={() => setShowFileGenerator(!showFileGenerator)}
              className="p-2 sm:p-2.5 rounded-xl bg-dark-900/50 hover:bg-dark-900/80 text-dark-300 hover:text-white transition-all border border-dark-800 hover:border-dark-700 hover-lift"
              title="Exportar conversación"
            >
              <FileDown className="w-4 h-4 sm:w-5 sm:h-5" />
            </button>
          </div>
        </div>
        
        {/* File Generator Panel */}
        {showFileGenerator && (
          <div className="mt-4 p-4 bg-dark-900/50 rounded-xl border border-dark-800 backdrop-blur-sm animate-scaleIn">
            <FileGenerator messages={safeMessages} />
          </div>
        )}
      </div>

      {/* Messages Area - Using ChatHistory component */}
      <ChatHistory messages={safeMessages} isLoading={isLoading} />

      {/* Confirmation Modal for pending actions */}
      <ConfirmationModal
        pendingAction={pendingAction}
        onConfirm={async (updatedAction) => {
          // If updatedAction provided (edit mode), use it; otherwise use pendingAction
          const payload = {
            message: '',
            confirmation_action: 'confirm',
            pending_action_data: updatedAction || pendingAction
          }
          try {
            setIsLoading(true)
            const resp = await api.post('/api/chat', payload)
            // Append assistant response
            const assistantMsg = {
              role: 'assistant',
              content: resp.response,
              sources: resp.sources || null,
              timestamp: resp.timestamp
            }
            setMessages(prev => [...prev, assistantMsg])
            
            // Check if we confirmed a calendar action and trigger refresh
            const actionType = (updatedAction || pendingAction)?.action_type
            if (actionType && actionType.includes('calendar')) {
              console.log('📅 Calendar action confirmed, triggering refresh...')
              setTimeout(() => {
                window.dispatchEvent(new CustomEvent('calendarUpdated'))
              }, 500)
            }
            
            // Clear modal
            setPendingAction(null)
          } catch (err) {
            console.error('Error confirming action:', err)
          } finally {
            setIsLoading(false)
          }
        }}
        onEdit={() => {
          // Edit is handled inside ConfirmationModal via edit mode; noop here
        }}
        onCancel={async () => {
          // Notify backend about cancellation for consistency
          try {
            setIsLoading(true)
            await api.post('/api/chat', { message: '', confirmation_action: 'cancel', pending_action_data: pendingAction })
          } catch (err) {
            console.error('Error cancelling action:', err)
          } finally {
            setPendingAction(null)
            setIsLoading(false)
          }
        }}
      />

      {/* Input Area */}
      <div className="px-4 sm:px-6 py-4 border-t border-dark-800/50 bg-dark-900/30 backdrop-blur-sm">
        {/* Voice Recorder Panel */}
        {showVoiceRecorder && (
          <div className="mb-4 p-4 bg-dark-900/80 rounded-xl border border-secondary-500/30 backdrop-blur-sm animate-scaleIn">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Mic className="w-4 h-4 text-secondary-400" />
                Grabación de Voz
              </h3>
              <button
                onClick={() => setShowVoiceRecorder(false)}
                className="p-1.5 text-dark-400 hover:text-white hover:bg-dark-800 rounded-lg transition-all"
              >
                <MicOff className="w-4 h-4" />
              </button>
            </div>
            <VoiceRecorder 
              onTranscriptionComplete={handleTranscription}
              disabled={isLoading}
            />
          </div>
        )}

        <div className="flex gap-2 sm:gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Escribe tu mensaje o usa el micrófono..."
            disabled={isLoading}
            aria-label="Escribe tu mensaje"
            className="flex-1 glass-effect text-white rounded-xl px-4 sm:px-5 py-2.5 sm:py-3 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 border border-dark-800 focus:border-primary-500 transition-all placeholder-dark-500 text-sm sm:text-base backdrop-blur-sm"
          />
          
          {/* Voice Button */}
          <button
            onClick={() => setShowVoiceRecorder(!showVoiceRecorder)}
            disabled={isLoading}
            className={`rounded-xl px-3 sm:px-4 py-2.5 sm:py-3 transition-all hover-lift flex items-center justify-center ${
              showVoiceRecorder 
                ? 'bg-gradient-to-r from-secondary-500 to-accent-500 hover:from-secondary-600 hover:to-accent-600 text-white shadow-glow' 
                : 'glass-effect hover:bg-dark-900/80 text-dark-300 hover:text-white border border-dark-800'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
            title="Grabar mensaje de voz"
          >
            <Mic className="w-4 h-4 sm:w-5 sm:h-5" />
          </button>

          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            aria-label="Enviar mensaje"
            className="bg-gradient-to-r from-primary-500 via-secondary-500 to-accent-500 hover:from-primary-600 hover:via-secondary-600 hover:to-accent-600 disabled:from-slate-700 disabled:to-slate-800 disabled:cursor-not-allowed text-white rounded-xl px-4 sm:px-6 py-2.5 sm:py-3 flex items-center gap-2 transition-all shadow-glow-strong hover:shadow-[0_0_50px_rgba(59,130,246,0.8)] disabled:shadow-none transform hover:scale-110 active:scale-95 disabled:scale-100"
          >
            <Send className="w-4 h-4 sm:w-5 sm:h-5" />
            <span className="font-medium text-sm sm:text-base hidden sm:inline">Enviar</span>
          </button>
        </div>
      </div>
    </div>
  )
}
