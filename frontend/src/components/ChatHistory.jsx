import React, { useEffect, useRef, useState } from 'react'
import MarkdownRenderer from './MarkdownRenderer'
import AudioPlayer from './AudioPlayer'
import { Volume2, X, FileText, Loader2 } from 'lucide-react'
import { API_BASE_URL } from '../services/api'
import { voiceService } from '../services'
import { useAuthStore } from '../store'

// Public avatar path (served from frontend/public)
const ServibotImg = '/servibot-avatar.png'

export default function ChatHistory({ messages = [], isLoading = false }) {
  const containerRef = useRef(null)
  const messagesEndRef = useRef(null)
  const [audioUrlForMessage, setAudioUrlForMessage] = useState({})
  const [showSourceModal, setShowSourceModal] = useState(false)
  const [selectedSource, setSelectedSource] = useState(null)
  const [audioGenerating, setAudioGenerating] = useState({})
  const [isAutoScrollEnabled, setIsAutoScrollEnabled] = useState(true)

  const user = useAuthStore((s) => s.user)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    if (isAutoScrollEnabled) {
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
    }
  }, [messages, isLoading, isAutoScrollEnabled])

  const handleScroll = () => {
    const el = containerRef.current
    if (!el) return
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
    setIsAutoScrollEnabled(distanceFromBottom < 120)
  }

  const openSourceModal = (source) => {
    setSelectedSource(source)
    setShowSourceModal(true)
  }

  const closeSourceModal = () => {
    setShowSourceModal(false)
    setSelectedSource(null)
  }

  const handleGenerateTTS = async (messageIndex, messageContent) => {
    setAudioGenerating(prev => ({ ...prev, [messageIndex]: true }))
    try {
      const result = await voiceService.synthesize(messageContent, 'es', 'gtts')
      if (result.success && result.data.status === 'success') {
        setAudioUrlForMessage(prev => ({ ...prev, [messageIndex]: result.data.audio_url }))
      }
    } catch (err) {
      console.error('TTS error', err)
    } finally {
      setAudioGenerating(prev => ({ ...prev, [messageIndex]: false }))
    }
  }

  const renderMessageBody = (msg) => {
    const sanitizeAssistantContent = (content) => {
      if (!content || typeof content !== 'string') return content
      // Remove any identifier that appears after the phrase "Correo enviado exitosamente"
      // e.g. "Correo enviado exitosamente: 19be7bfd02f3f7d5" -> "Correo enviado exitosamente"
      return content.replace(/(Correo enviado exitosamente)\s*[:\-–—]?\s*[A-Za-z0-9-_]+/i, '$1')
    }

    if (msg.role === 'user') return <p className="whitespace-pre-wrap leading-relaxed text-sm sm:text-base">{msg.content}</p>

    const displayContent = msg.role === 'assistant' ? sanitizeAssistantContent(msg.content) : msg.content

    return (
      <div className="prose prose-sm sm:prose-base prose-invert max-w-none">
        <MarkdownRenderer content={displayContent || (msg.streaming ? 'Escribiendo...' : '')} />
      </div>
    )
  }

  return (
    <div ref={containerRef} onScroll={handleScroll} className="flex-1 min-h-0 overflow-y-auto p-4 sm:p-6 space-y-4 scrollbar-hide relative" role="log" aria-live="polite" aria-label="Historial de conversación" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
      {messages.length === 0 ? (
        <div className="text-center text-dark-400 mt-10 sm:mt-20 animate-fadeIn px-4">
          <div className="w-16 h-16 sm:w-20 sm:h-20 mx-auto mb-4 sm:mb-6 rounded-2xl bg-gradient-to-br from-primary-500/20 to-secondary-500/20 flex items-center justify-center border border-primary-500/30 shadow-glow">
            <span className="text-3xl sm:text-4xl">👋</span>
          </div>
          <p className="text-base sm:text-lg mb-2 font-semibold text-white">¡Hola! Soy ServiBot</p>
          <p className="text-xs sm:text-sm text-dark-400">Envíame un mensaje para comenzar</p>
        </div>
      ) : (
        messages.map((msg, idx) => (
          <div key={msg.id || idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-slideIn`}>
            <div className={`flex items-end gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              {/* Avatar */}
              {msg.role !== 'user' ? (
                <img src={ServibotImg} alt="ServiBot" className="w-14 h-14 object-contain shadow-md flex-shrink-0" />
              ) : (
                (user && user.picture) ? (
                  <img src={user.picture} alt={user.name || 'Usuario'} className="w-9 h-9 rounded-full object-cover shadow-md" />
                ) : (
                  <div className="w-9 h-9 rounded-full bg-dark-800 flex items-center justify-center text-xs text-white">U</div>
                )
              )}

              <div className={`max-w-[85%] sm:max-w-[80%] rounded-2xl px-4 sm:px-5 py-3 shadow-lg break-words ${msg.role === 'user' ? 'bg-gradient-to-br from-primary-600 to-secondary-600 text-white' : msg.error ? 'bg-danger-500/20 text-danger-300 border border-danger-500/50' : msg.streaming ? 'bg-gradient-to-br from-dark-800/80 to-dark-900/80 text-white border border-primary-400/50 animate-pulse backdrop-blur-sm' : 'bg-gradient-to-br from-dark-800/80 to-dark-900/80 text-white border border-dark-700 backdrop-blur-sm'}`}>
                {renderMessageBody(msg)}

                {msg.role === 'assistant' && !msg.error && !msg.streaming && msg.content && (
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    {audioGenerating[idx] ? (
                      <button disabled className="text-xs flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-500/20 text-purple-300 border border-purple-400/30 opacity-70 cursor-wait">
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span className="hidden sm:inline">Generando audio...</span>
                        <span className="sm:hidden">⏳</span>
                      </button>
                    ) : !audioUrlForMessage[idx] ? (
                      <button onClick={() => handleGenerateTTS(idx, msg.content)} className="text-xs flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-secondary-500/20 text-secondary-300 border border-secondary-400/30 hover:bg-secondary-500/30 hover:border-secondary-400/50 transition-all hover:scale-105 active:scale-95">
                        <Volume2 className="w-3.5 h-3.5" />
                        <span className="hidden sm:inline">Escuchar respuesta</span>
                        <span className="sm:hidden">🔊</span>
                      </button>
                    ) : (
                      <div className="w-full"><AudioPlayer audioUrl={audioUrlForMessage[idx]} /></div>
                    )}
                  </div>
                )}

                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-4 bg-dark-900/40 backdrop-blur-sm p-3 rounded-xl border border-dark-700">
                    <h4 className="text-xs font-semibold text-dark-400 mb-2 flex items-center gap-2">
                      <span className="w-1 h-1 rounded-full bg-primary-400"></span>
                      Fuentes consultadas
                    </h4>
                    <div className="flex flex-wrap gap-2 items-center">
                      {msg.sources.map((source, i) => {
                        const isObject = typeof source === 'object'
                        const filename = isObject ? source.filename : source
                        const snippet = isObject ? source.snippet : null
                        return (
                          <button key={i} onClick={() => snippet ? openSourceModal(source) : null} className={`text-xs bg-primary-500/30 text-primary-200 px-3 py-1.5 rounded-lg border border-primary-400/30 transition-all flex items-center gap-1.5 group max-w-full truncate ${snippet ? 'hover:bg-primary-500/40 hover:border-primary-400/50 cursor-pointer' : 'cursor-default'}`} title={snippet ? 'Ver fragmento' : filename}>
                            <FileText className="w-3 h-3 flex-shrink-0" />
                            <span className="truncate">{filename}</span>
                            {isObject && source.distance !== undefined && (<span className="text-[10px] opacity-60">({source.distance})</span>)}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )}

                <p className="text-xs mt-3 opacity-60 flex items-center gap-1.5">
                  <span className="w-1 h-1 rounded-full bg-current"></span>
                  {new Date(msg.timestamp).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
                  {msg.streaming && <span className="ml-2 animate-pulse">✍️</span>}
                </p>
              </div>
            </div>
          </div>
        ))
      )}

      {isLoading && (
        <div className="flex justify-start animate-slideIn">
          <div className="bg-gradient-to-br from-dark-800/80 to-dark-900/80 backdrop-blur-sm border border-dark-700 rounded-2xl px-4 sm:px-5 py-4 flex items-center space-x-3 shadow-lg">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
            <span className="text-dark-400 text-sm">Pensando...</span>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />

      {!isAutoScrollEnabled && (
        <div className="sticky bottom-2 sm:bottom-4 left-0 right-0 flex justify-end px-4 pointer-events-none z-10">
          <button 
            onClick={() => { 
              if (containerRef.current) { 
                containerRef.current.scrollTo({ top: containerRef.current.scrollHeight, behavior: 'smooth' }) 
              } 
              setIsAutoScrollEnabled(true) 
            }} 
            className="py-2 px-3 sm:px-4 bg-gradient-to-r from-primary-500 to-secondary-500 text-white rounded-full text-xs sm:text-sm font-medium shadow-glow hover:scale-105 hover:shadow-glow-lg transition-all animate-slideIn flex items-center gap-1.5 sm:gap-2 pointer-events-auto"
          >
            <span>↓</span>
            <span className="hidden sm:inline">Ir al final</span>
            <span className="sm:hidden">Final</span>
          </button>
        </div>
      )}

      {showSourceModal && selectedSource && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-fadeIn">
          <div className="bg-dark-900/95 backdrop-blur-xl rounded-3xl shadow-2xl border border-dark-800 max-w-2xl w-full max-h-[80vh] flex flex-col animate-scaleIn">
            <div className="p-5 border-b border-dark-800 flex items-center justify-between bg-gradient-to-r from-primary-500/10 to-secondary-500/10">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-primary-500/20 to-secondary-500/20 flex items-center justify-center shadow-glow">
                  <FileText className="w-5 h-5 text-primary-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-white">Fragmento del Documento</h3>
                  <p className="text-xs text-dark-400">{selectedSource.filename}</p>
                </div>
              </div>
              <button onClick={closeSourceModal} className="p-2.5 hover:bg-dark-800 rounded-xl transition-all hover:scale-105 active:scale-95">
                <X className="w-5 h-5 text-dark-400 hover:text-white" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
              <div className="bg-dark-800/50 backdrop-blur-sm p-4 rounded-xl border border-dark-700">
                <div className="flex items-center justify-between mb-3 pb-2 border-b border-dark-700">
                  <span className="text-xs text-dark-400 font-medium">Chunk #{selectedSource.chunk_index}</span>
                  <span className="text-xs text-dark-400 font-medium">Relevancia: {(1 - selectedSource.distance).toFixed(2)}</span>
                </div>
                <p className="text-sm whitespace-pre-wrap text-white leading-relaxed">{selectedSource.snippet}</p>
              </div>
            </div>

            <div className="p-5 border-t border-dark-800 flex gap-3">
              <button onClick={closeSourceModal} className="flex-1 py-2.5 bg-gradient-to-r from-primary-500 to-secondary-600 hover:from-primary-600 hover:to-secondary-700 text-white rounded-xl transition-all font-semibold hover:scale-105 active:scale-95 shadow-glow">Cerrar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
