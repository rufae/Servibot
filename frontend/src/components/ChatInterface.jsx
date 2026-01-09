import { useState } from 'react'
import { Send, Loader2, Volume2, FileDown } from 'lucide-react'
import axios from 'axios'
import VoiceRecorder from './VoiceRecorder'
import AudioPlayer from './AudioPlayer'
import FileGenerator from './FileGenerator'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function ChatInterface({ messages, setMessages, setAgentActivity }) {
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [expandedSources, setExpandedSources] = useState({})
  const [showVoiceRecorder, setShowVoiceRecorder] = useState(false)
  const [showFileGenerator, setShowFileGenerator] = useState(false)
  const [audioUrlForMessage, setAudioUrlForMessage] = useState({}) // Map message index to audio URL

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
      const response = await axios.post(`${API_BASE_URL}/api/chat`, {
        message: input
      })

      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
        sources: response.data.sources || null,
        timestamp: response.data.timestamp,
        plan: response.data.plan
      }

      setMessages(prev => [...prev, assistantMessage])

      // Update agent activity timeline
      if (response.data.plan) {
        setAgentActivity(prev => [...prev, ...response.data.plan])
      }

      // Auto-download generated file if available
      if (response.data.generated_file) {
        const { filename, download_url } = response.data.generated_file
        console.log(`Auto-downloading generated file: ${filename}`)
        
        // Trigger download
        const downloadLink = document.createElement('a')
        downloadLink.href = `${API_BASE_URL}${download_url}`
        downloadLink.download = filename
        document.body.appendChild(downloadLink)
        downloadLink.click()
        document.body.removeChild(downloadLink)
        
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

  const handleGenerateTTS = async (messageIndex, messageContent) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/voice/synthesize`, {
        text: messageContent,
        language: 'es',
        engine: 'gtts'
      })

      if (response.data.status === 'success') {
        setAudioUrlForMessage(prev => ({
          ...prev,
          [messageIndex]: response.data.audio_url
        }))
      }
    } catch (error) {
      console.error('Error generating TTS:', error)
    }
  }

  return (
    <div className="bg-gradient-to-br from-gray-800 via-gray-900 to-gray-800 rounded-2xl shadow-2xl border border-gray-700 flex flex-col h-[600px] overflow-hidden">
      {/* Chat Header */}
      <div className="px-6 py-5 border-b border-gray-700 bg-gradient-to-r from-primary-600/20 to-purple-600/20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center">
              <span className="text-xl">💬</span>
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Chat con ServiBot</h2>
              <p className="text-xs text-gray-400">Hazme preguntas sobre tus documentos</p>
            </div>
          </div>
          
          {/* Header Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowFileGenerator(!showFileGenerator)}
              className="p-2 rounded-lg bg-gray-700/50 hover:bg-gray-600/50 text-gray-300 hover:text-white transition-all border border-gray-600/50"
              title="Exportar conversación"
            >
              <FileDown className="w-5 h-5" />
            </button>
          </div>
        </div>
        
        {/* File Generator Panel */}
        {showFileGenerator && (
          <div className="mt-4 p-4 bg-gray-800/50 rounded-lg border border-gray-700">
            <FileGenerator messages={messages} />
          </div>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
        {messages.length === 0 ? (
          <div className="text-center text-gray-400 mt-20 animate-fadeIn">
            <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-primary-500/20 to-purple-500/20 flex items-center justify-center border border-primary-500/30">
              <span className="text-4xl">👋</span>
            </div>
            <p className="text-lg mb-2 font-semibold text-white">¡Hola! Soy ServiBot</p>
            <p className="text-sm text-gray-500">Envíame un mensaje para comenzar</p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-slideIn`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-5 py-3 shadow-lg ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-br from-primary-600 to-primary-700 text-white'
                    : msg.error
                    ? 'bg-red-500/20 text-red-300 border border-red-500/50'
                    : 'bg-gradient-to-br from-gray-800 to-gray-900 text-gray-100 border border-gray-700'
                }`}
              >
                <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                
                {/* TTS Button for assistant messages */}
                {msg.role === 'assistant' && !msg.error && (
                  <div className="mt-3 flex items-center gap-2">
                    {!audioUrlForMessage[idx] ? (
                      <button
                        onClick={() => handleGenerateTTS(idx, msg.content)}
                        className="text-xs flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-500/20 text-purple-300 border border-purple-400/30 hover:bg-purple-500/30 hover:border-purple-400/50 transition-all"
                      >
                        <Volume2 className="w-3.5 h-3.5" />
                        Escuchar respuesta
                      </button>
                    ) : (
                      <div className="w-full">
                        <AudioPlayer audioUrl={audioUrlForMessage[idx]} />
                      </div>
                    )}
                  </div>
                )}
                
                {/* Render RAG sources if present */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-4 bg-black/20 p-3 rounded-xl border border-white/10">
                    <h4 className="text-xs font-semibold text-gray-300 mb-2 flex items-center gap-2">
                      <span className="w-1 h-1 rounded-full bg-primary-400"></span>
                      Fuentes consultadas
                    </h4>
                    <div className="flex flex-wrap gap-2 items-center">
                      {(() => {
                        const key = idx
                        const expanded = !!expandedSources[key]
                        const limit = 6
                        const sources = msg.sources.map(s => (typeof s === 'string' ? s : (s.filename || s.metadata?.source || 'Fuente desconocida')))
                        const visible = expanded ? sources : sources.slice(0, limit)
                        return (
                          <>
                            {visible.map((name, i) => (
                              <a
                                key={i}
                                href={`${API_BASE_URL}/api/upload/file/${encodeURIComponent(name)}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-xs bg-primary-500/30 text-primary-200 px-3 py-1.5 rounded-lg border border-primary-400/30 hover:bg-primary-500/40 hover:border-primary-400/50 transition-all flex items-center gap-1.5 group"
                                title={`Abrir ${name}`}
                              >
                                <span className="w-1.5 h-1.5 rounded-full bg-primary-400 group-hover:scale-125 transition-transform"></span>
                                {name}
                              </a>
                            ))}

                            {sources.length > limit && (
                              <button
                                onClick={() => setExpandedSources(prev => ({ ...prev, [key]: !prev[key] }))}
                                className="text-xs text-primary-300 px-3 py-1.5 rounded-lg hover:bg-primary-500/20 transition-all border border-primary-400/20 hover:border-primary-400/40"
                              >
                                {expanded ? '← Ver menos' : `+${sources.length - limit} más →`}
                              </button>
                            )}
                          </>
                        )
                      })()}
                    </div>
                  </div>
                )}
                
                <p className="text-xs mt-3 opacity-60 flex items-center gap-1.5">
                  <span className="w-1 h-1 rounded-full bg-current"></span>
                  {new Date(msg.timestamp).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex justify-start animate-slideIn">
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-2xl px-5 py-4 flex items-center space-x-3 shadow-lg">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
              <span className="text-gray-300 text-sm">Pensando...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="px-6 py-4 border-t border-gray-700 bg-gray-800/50">
        {/* Voice Recorder Panel */}
        {showVoiceRecorder && (
          <div className="mb-4 p-4 bg-gray-900/80 rounded-xl border border-purple-500/30">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-white">Grabación de Voz</h3>
              <button
                onClick={() => setShowVoiceRecorder(false)}
                className="text-xs text-gray-400 hover:text-white transition-colors"
              >
                Cerrar ✕
              </button>
            </div>
            <VoiceRecorder 
              onTranscriptionComplete={handleTranscription}
              disabled={isLoading}
            />
          </div>
        )}

        <div className="flex space-x-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Escribe tu mensaje o usa el micrófono..."
            disabled={isLoading}
            className="flex-1 bg-gray-900 text-white rounded-xl px-5 py-3 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 border border-gray-700 focus:border-primary-500 transition-all placeholder-gray-500"
          />
          
          {/* Voice Button */}
          <button
            onClick={() => setShowVoiceRecorder(!showVoiceRecorder)}
            disabled={isLoading}
            className={`
              rounded-xl px-4 py-3 transition-all
              ${showVoiceRecorder 
                ? 'bg-purple-600 hover:bg-purple-700 text-white' 
                : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
              }
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
            title="Grabar mensaje de voz"
          >
            🎤
          </button>

          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white rounded-xl px-6 py-3 flex items-center space-x-2 transition-all shadow-lg hover:shadow-primary-500/30 disabled:shadow-none transform hover:scale-105 disabled:scale-100"
          >
            <Send className="w-5 h-5" />
            <span className="font-medium">Enviar</span>
          </button>
        </div>
      </div>

      <style jsx>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        .animate-slideIn {
          animation: slideIn 0.3s ease-out;
        }
        .animate-fadeIn {
          animation: fadeIn 0.5s ease-out;
        }
        .scrollbar-thin::-webkit-scrollbar {
          width: 6px;
        }
        .scrollbar-thin::-webkit-scrollbar-track {
          background: transparent;
        }
        .scrollbar-thin::-webkit-scrollbar-thumb {
          background: #374151;
          border-radius: 3px;
        }
        .scrollbar-thin::-webkit-scrollbar-thumb:hover {
          background: #4B5563;
        }
      `}</style>
    </div>
  )
}
