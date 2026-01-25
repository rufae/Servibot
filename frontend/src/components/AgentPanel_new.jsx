import { useEffect, useState } from 'react'
import AgentTimeline from './AgentTimeline'
import Swal from 'sweetalert2'
import { authService } from '../services/authService'
import api from '../services/api'
import { useAuthStore } from '../store'
import { Calendar, Mail, ExternalLink, Clock, Loader2, User, ChevronRight, X } from 'lucide-react'

function LoadingSpinner({ size = 'md' }) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8'
  }
  
  return (
    <div className="flex items-center justify-center py-8">
      <Loader2 className={`animate-spin ${sizeClasses[size]} text-[var(--color-primary)]`} />
    </div>
  )
}

function CalendarModal({ events, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-[var(--bg-panel)] rounded-2xl shadow-2xl border border-[var(--bg-panel)] w-full max-w-3xl max-h-[80vh] flex flex-col m-4" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-6 border-b border-[var(--bg-main)]">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-lg">
              <Calendar className="w-5 h-5 text-blue-400" />
            </div>
            <h2 className="text-xl font-semibold">Todos los Eventos</h2>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-[var(--bg-main)] rounded-lg transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-6">
          {events.length === 0 ? (
            <div className="text-center py-12">
              <Calendar className="w-16 h-16 mx-auto mb-4 text-[var(--text-secondary)] opacity-50" />
              <p className="text-[var(--text-secondary)]">No hay eventos próximos</p>
            </div>
          ) : (
            <div className="space-y-3">
              {events.map(ev => (
                <div key={ev.id} className="p-4 rounded-xl bg-gradient-to-r from-[var(--bg-main)]/50 to-transparent border border-[var(--bg-main)] hover:border-blue-500/30 transition-all group">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-base font-semibold mb-1 group-hover:text-blue-400 transition-colors">{ev.summary || ev.title}</h3>
                      <div className="flex items-center gap-4 text-sm text-[var(--text-secondary)]">
                        <div className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          <span>{ev.start}</span>
                        </div>
                        {ev.location && (
                          <span className="flex items-center gap-1">
                            <ExternalLink className="w-3 h-3" />
                            {ev.location}
                          </span>
                        )}
                      </div>
                      {ev.description && (
                        <p className="text-sm text-[var(--text-secondary)] mt-2 line-clamp-2">{ev.description}</p>
                      )}
                    </div>
                    <ChevronRight className="w-5 h-5 text-[var(--text-secondary)] opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function EmailModal({ mails, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-[var(--bg-panel)] rounded-2xl shadow-2xl border border-[var(--bg-panel)] w-full max-w-3xl max-h-[80vh] flex flex-col m-4" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-6 border-b border-[var(--bg-main)]">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-green-500/20 to-emerald-500/20 rounded-lg">
              <Mail className="w-5 h-5 text-green-400" />
            </div>
            <h2 className="text-xl font-semibold">Todos los Correos</h2>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-[var(--bg-main)] rounded-lg transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-6">
          {mails.length === 0 ? (
            <div className="text-center py-12">
              <Mail className="w-16 h-16 mx-auto mb-4 text-[var(--text-secondary)] opacity-50" />
              <p className="text-[var(--text-secondary)]">No hay correos recientes</p>
            </div>
          ) : (
            <div className="space-y-3">
              {mails.map(mail => (
                <div key={mail.id} className="p-4 rounded-xl bg-gradient-to-r from-[var(--bg-main)]/50 to-transparent border border-[var(--bg-main)] hover:border-green-500/30 transition-all group">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-base font-semibold mb-1 group-hover:text-green-400 transition-colors line-clamp-1">{mail.subject}</h3>
                      <div className="flex items-center gap-1 text-sm text-[var(--text-secondary)] mb-2">
                        <User className="w-4 h-4" />
                        <span>{mail.from}</span>
                      </div>
                      {mail.snippet && (
                        <p className="text-sm text-[var(--text-secondary)] line-clamp-2">{mail.snippet}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <div className="text-xs text-[var(--text-secondary)] whitespace-nowrap">{mail.time || mail.internalDate || ''}</div>
                      <ChevronRight className="w-5 h-5 text-[var(--text-secondary)] opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function CalendarView({ events = [], loading = false, onViewAll }) {
  return (
    <div className="bg-gradient-to-br from-[var(--bg-panel)] to-[var(--bg-main)]/30 rounded-xl border border-[var(--bg-panel)] shadow-lg h-[340px] flex flex-col overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 bg-[var(--bg-panel)]/40 border-b border-[var(--bg-panel)]/60 flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-blue-500/10 rounded-lg">
            <Calendar className="w-4 h-4 text-blue-400" />
          </div>
          <h3 className="text-sm font-semibold">Calendario</h3>
        </div>
        {events.length > 0 && (
          <button 
            onClick={onViewAll} 
            className="text-xs text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1 transition-colors"
          >
            Ver todo
            <ExternalLink className="w-3 h-3" />
          </button>
        )}
      </div>
      
      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto p-4 space-y-2 calendar-scroll">
          {events.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <Calendar className="w-12 h-12 mb-3 text-[var(--text-secondary)] opacity-30" />
              <p className="text-xs text-[var(--text-secondary)]">No hay eventos próximos</p>
            </div>
          ) : (
            events.slice(0, 5).map(ev => (
              <div key={ev.id} className="p-3 rounded-lg bg-[var(--bg-main)]/50 hover:bg-[var(--bg-main)] border border-transparent hover:border-blue-500/20 transition-all group cursor-pointer">
                <div className="text-sm font-medium mb-1 group-hover:text-blue-400 transition-colors line-clamp-1">{ev.summary || ev.title}</div>
                <div className="flex items-center gap-1 text-xs text-[var(--text-secondary)]">
                  <Clock className="w-3 h-3" />
                  <span>{ev.start}</span>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}

function InboxView({ mails = [], loading = false, onViewAll }) {
  return (
    <div className="bg-gradient-to-br from-[var(--bg-panel)] to-[var(--bg-main)]/30 rounded-xl border border-[var(--bg-panel)] shadow-lg h-[340px] flex flex-col overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 bg-[var(--bg-panel)]/40 border-b border-[var(--bg-panel)]/60 flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-green-500/10 rounded-lg">
            <Mail className="w-4 h-4 text-green-400" />
          </div>
          <h3 className="text-sm font-semibold">Correos Recientes</h3>
        </div>
        {mails.length > 0 && (
          <button 
            onClick={onViewAll} 
            className="text-xs text-green-400 hover:text-green-300 font-medium flex items-center gap-1 transition-colors"
          >
            Ver todo
            <ExternalLink className="w-3 h-3" />
          </button>
        )}
      </div>
      
      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-green-400 animate-spin" />
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto p-4 space-y-2 mails-scroll">
          {mails.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <Mail className="w-12 h-12 mb-3 text-[var(--text-secondary)] opacity-30" />
              <p className="text-xs text-[var(--text-secondary)]">No hay correos recientes</p>
            </div>
          ) : (
            mails.slice(0, 5).map(mail => (
              <div key={mail.id} className="p-3 rounded-lg bg-[var(--bg-main)]/50 hover:bg-[var(--bg-main)] border border-transparent hover:border-green-500/20 transition-all group cursor-pointer">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium mb-1 group-hover:text-green-400 transition-colors line-clamp-1">{mail.subject}</p>
                    <p className="text-xs text-[var(--text-secondary)] line-clamp-1">{mail.from}</p>
                  </div>
                  <div className="text-xs text-[var(--text-secondary)] whitespace-nowrap flex-shrink-0">
                    {mail.time || mail.internalDate || ''}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}

export default function AgentPanel({ activity = [], setAgentActivity = () => {} }) {
  const { user, setGoogleConnected } = useAuthStore()
  const [checking, setChecking] = useState(true)
  const [connected, setConnected] = useState(false)
  const [loadingData, setLoadingData] = useState(false)
  const [events, setEvents] = useState([])
  const [mails, setMails] = useState([])
  const [showCalendarModal, setShowCalendarModal] = useState(false)
  const [showEmailModal, setShowEmailModal] = useState(false)

  const fetchData = async () => {
    setLoadingData(true)
    try {
      const cal = await api.get('/api/tools/calendar/events?max_results=10')
      if (cal && cal.events) setEvents(cal.events)
    } catch (e) {
      console.warn('Failed to fetch calendar events', e)
    }

    try {
      const mail = await api.get('/api/tools/gmail/messages?max_results=10')
      if (mail && mail.messages) setMails(mail.messages)
    } catch (e) {
      console.warn('Failed to fetch mails', e)
    }
    setLoadingData(false)
  }

  useEffect(() => {
    const init = async () => {
      setChecking(true)
      
      try {
        const status = await authService.getGoogleStatus()
        if (status.success && status.data && status.data.connected) {
          setConnected(true)
          setGoogleConnected(true, status.data.user_id || null)
          await fetchData()
        } else {
          setConnected(false)
          setEvents([])
          setMails([])
        }
      } catch (e) {
        console.warn('Status check failed', e)
        setConnected(false)
      }

      setChecking(false)
    }

    init()
    
    const handleMessage = async (ev) => {
      try {
        if (!ev.data) return
        if (ev.data.type === 'oauth_token' && ev.data.token) {
          setTimeout(async () => {
            const status = await authService.getGoogleStatus()
            if (status.success && status.data && status.data.connected) {
              setConnected(true)
              await fetchData()
            }
          }, 300)
        }
      } catch (e) {
        // ignore
      }
    }

    window.addEventListener('message', handleMessage)

    return () => {
      window.removeEventListener('message', handleMessage)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const userId = user?.id || 'default_user'

  const handleConnect = () => {
    const popup = authService.startGoogleAuth(userId)
    const interval = setInterval(() => {
      try {
        if (!popup || popup.closed) {
          clearInterval(interval)
          setTimeout(async () => {
            const status = await authService.getGoogleStatus()
            if (status.success && status.data && status.data.connected) {
              setConnected(true)
              await fetchData()
            }
          }, 500)
        }
      } catch (e) {
        clearInterval(interval)
      }
    }, 500)
  }

  const handleDisconnect = async () => {
    const res = await authService.revokeGoogleAccess()
    if (res.success) {
      localStorage.removeItem('auth_token')
      setConnected(false)
      setEvents([])
      setMails([])
      setGoogleConnected(false, null)
      Swal.fire({ icon: 'success', title: 'Desconectado', text: 'Cuenta Google desconectada' })
    } else {
      Swal.fire({ icon: 'error', title: 'Error', text: String(res.error || 'No se pudo desconectar') })
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold">Integración Google</h2>
        {checking ? (
          <div className="text-xs text-[var(--text-secondary)]">Verificando...</div>
        ) : connected ? (
          <div className="flex items-center gap-2">
            <span className="px-2 py-1 bg-green-500/10 text-green-400 text-xs rounded-md border border-green-500/20">Conectado</span>
            <button onClick={handleDisconnect} className="text-xs text-red-400 hover:text-red-300">Desconectar</button>
          </div>
        ) : (
          <button onClick={handleConnect} className="px-3 py-1.5 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white text-xs rounded-lg transition-all">
            Conectar Google
          </button>
        )}
      </div>

      <CalendarView events={events} loading={loadingData} onViewAll={() => setShowCalendarModal(true)} />
      <InboxView mails={mails} loading={loadingData} onViewAll={() => setShowEmailModal(true)} />
      <AgentTimeline activity={activity} />
      
      {showCalendarModal && <CalendarModal events={events} onClose={() => setShowCalendarModal(false)} />}
      {showEmailModal && <EmailModal mails={mails} onClose={() => setShowEmailModal(false)} />}
    </div>
  )
}
