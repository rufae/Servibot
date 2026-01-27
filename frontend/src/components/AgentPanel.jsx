import React, { useEffect, useState } from 'react'
import ReactDOM from 'react-dom'
import AgentTimeline from './AgentTimeline'
import ContactsPanel from './ContactsPanel'
import Swal from 'sweetalert2'
import { authService } from '../services/authService'
import api from '../services/api'
import { useAuthStore } from '../store'
import { Calendar, Mail, ExternalLink, Clock, Loader2, User, ChevronRight, X, Users } from 'lucide-react'

function LoadingSpinner({ size = 'md' }) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8'
  }
  
  return (
    <div className="flex items-center justify-center py-8">
      <svg className={`animate-spin ${sizeClasses[size]} text-[var(--color-primary)]`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </div>
  )
}

function CalendarModal({ events, onClose }) {
  const [currentDate, setCurrentDate] = React.useState(new Date())
  const [selectedDay, setSelectedDay] = React.useState(null)
  
  // Get calendar grid data
  const getCalendarData = () => {
    const year = currentDate.getFullYear()
    const month = currentDate.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const daysInMonth = lastDay.getDate()
    const startingDayOfWeek = firstDay.getDay()
    
    // Parse events and group by date
    const eventsByDate = {}
    events.forEach(ev => {
      try {
        const dateStr = ev.start?.split('T')[0] || ev.start?.split(' ')[0]
        if (dateStr) {
          if (!eventsByDate[dateStr]) eventsByDate[dateStr] = []
          eventsByDate[dateStr].push(ev)
        }
      } catch (e) {
        console.warn('Error parsing event date:', e)
      }
    })
    
    return { daysInMonth, startingDayOfWeek, eventsByDate, year, month }
  }
  
  const { daysInMonth, startingDayOfWeek, eventsByDate, year, month } = getCalendarData()
  const monthNames = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
  const dayNames = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb']
  
  const prevMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1))
    setSelectedDay(null)
  }
  const nextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1))
    setSelectedDay(null)
  }
  
  const handleDayClick = (day) => {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    const dayEvents = eventsByDate[dateStr] || []
    if (dayEvents.length > 0) {
      setSelectedDay({ day, dateStr, events: dayEvents })
    }
  }
  
  const formatEventTime = (startStr) => {
    try {
      if (startStr.includes('T')) {
        const time = startStr.split('T')[1]?.substring(0, 5)
        return time || 'Todo el día'
      }
      return 'Todo el día'
    } catch {
      return 'Todo el día'
    }
  }
  
  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/70 backdrop-blur-md animate-fadeIn p-4" onClick={onClose}>
      <div className="bg-dark-900/95 backdrop-blur-xl rounded-3xl shadow-2xl border border-dark-800 w-full max-w-6xl max-h-[92vh] flex flex-col animate-scaleIn" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-6 border-b border-dark-800 bg-gradient-to-r from-primary-500/10 to-secondary-500/10">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-primary-500/20 to-secondary-500/20 rounded-2xl flex items-center justify-center shadow-glow">
              <Calendar className="w-6 h-6 text-primary-400" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">Calendario</h2>
              <p className="text-sm text-dark-400">{events.length} eventos</p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-2.5 hover:bg-dark-800 rounded-xl transition-all hover:scale-105 active:scale-95"
          >
            <X className="w-5 h-5 text-dark-400 hover:text-white" />
          </button>
        </div>
        
        <div className="flex-1 overflow-hidden flex">
          {/* Calendar Section */}
          <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
            {/* Month Navigation */}
            <div className="flex items-center justify-between mb-6">
              <button 
                onClick={prevMonth}
                className="p-2 rounded-xl bg-dark-800/50 hover:bg-dark-800 text-primary-400 transition-all hover:scale-105"
              >
                <ChevronRight className="w-5 h-5 rotate-180" />
              </button>
              <h3 className="text-xl font-bold text-white">{monthNames[month]} {year}</h3>
              <button 
                onClick={nextMonth}
                className="p-2 rounded-xl bg-dark-800/50 hover:bg-dark-800 text-primary-400 transition-all hover:scale-105"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
            
            {/* Calendar Grid - Compact */}
            <div className="grid grid-cols-7 gap-1.5">
              {/* Day headers */}
              {dayNames.map(day => (
                <div key={day} className="text-center text-xs font-semibold text-primary-400 py-1.5">
                  {day}
                </div>
              ))}
              
              {/* Empty cells for days before month starts */}
              {Array.from({ length: startingDayOfWeek }).map((_, i) => (
                <div key={`empty-${i}`} className="h-14" />
              ))}
              
              {/* Calendar days - Compact */}
              {Array.from({ length: daysInMonth }).map((_, i) => {
                const day = i + 1
                const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
                const dayEvents = eventsByDate[dateStr] || []
                const isToday = new Date().toDateString() === new Date(year, month, day).toDateString()
                const isSelected = selectedDay?.day === day
                
                return (
                  <button
                    key={day}
                    onClick={() => handleDayClick(day)}
                    className={`h-14 p-1.5 rounded-lg border transition-all group relative ${
                      isSelected
                        ? 'bg-primary-500/30 border-primary-400 ring-2 ring-primary-500/50'
                        : isToday 
                          ? 'bg-primary-500/20 border-primary-500/50 hover:bg-primary-500/30' 
                          : dayEvents.length > 0 
                            ? 'bg-dark-800/50 border-dark-700 hover:border-primary-500/40 hover:bg-dark-800' 
                            : 'bg-dark-850/30 border-dark-800 hover:border-dark-700'
                    }`}
                  >
                    <div className={`text-xs font-semibold ${isToday ? 'text-primary-300' : 'text-white'}`}>{day}</div>
                    {dayEvents.length > 0 && (
                      <div className="absolute bottom-1 left-1/2 -translate-x-1/2 flex gap-0.5">
                        {dayEvents.slice(0, 3).map((_, idx) => (
                          <div key={idx} className="w-1 h-1 rounded-full bg-primary-400" />
                        ))}
                      </div>
                    )}
                  </button>
                )
              })}
            </div>
          </div>
          
          {/* Day Detail Panel */}
          {selectedDay && (
            <div className="w-80 border-l border-dark-800 bg-dark-900/50 flex flex-col animate-slideInFromRight">
              <div className="p-4 border-b border-dark-800 flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold text-white">{selectedDay.day} {monthNames[month]}</h3>
                  <p className="text-xs text-dark-400">{selectedDay.events.length} evento{selectedDay.events.length !== 1 ? 's' : ''}</p>
                </div>
                <button
                  onClick={() => setSelectedDay(null)}
                  className="p-2 hover:bg-dark-800 rounded-lg transition-all"
                >
                  <X className="w-4 h-4 text-dark-400" />
                </button>
              </div>
              
              <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
                {selectedDay.events.map((ev, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-dark-800/50 border border-dark-700 hover:border-primary-500/30 transition-all group"
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-12 text-center">
                        <div className="text-xs font-semibold text-primary-400">{formatEventTime(ev.start)}</div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-semibold text-white mb-1 line-clamp-2 group-hover:text-primary-300 transition-colors">
                          {ev.summary || ev.title}
                        </h4>
                        {ev.location && (
                          <div className="flex items-center gap-1.5 text-xs text-dark-400 mt-1">
                            <ExternalLink className="w-3 h-3" />
                            <span className="truncate">{ev.location}</span>
                          </div>
                        )}
                        {ev.description && (
                          <p className="text-xs text-dark-400 mt-2 line-clamp-2">{ev.description}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function EmailModal({ mails: initialMails, onClose }) {
  const [mails, setMails] = useState(initialMails)
  const [loading, setLoading] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const [pageToken, setPageToken] = useState(null)
  
  const loadMoreEmails = async () => {
    if (loading || !hasMore) return
    
    setLoading(true)
    try {
      const query = pageToken ? `&pageToken=${pageToken}` : ''
      const response = await api.get(`/api/tools/gmail/messages?max_results=20${query}`)
      
      if (response.messages && response.messages.length > 0) {
        setMails(prev => [...prev, ...response.messages])
        setPageToken(response.next_page_token || null)
        setHasMore(!!response.next_page_token)
      } else {
        setHasMore(false)
      }
    } catch (e) {
      console.warn('Failed to load more emails:', e)
      setHasMore(false)
    } finally {
      setLoading(false)
    }
  }
  
  const handleScroll = (e) => {
    const { scrollTop, scrollHeight, clientHeight } = e.target
    if (scrollHeight - scrollTop <= clientHeight + 100) {
      loadMoreEmails()
    }
  }
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md animate-fadeIn" onClick={onClose}>
      <div className="bg-dark-900/95 backdrop-blur-xl rounded-3xl shadow-2xl border border-dark-800 w-full max-w-4xl max-h-[85vh] flex flex-col m-4 animate-scaleIn" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-6 border-b border-dark-800 bg-gradient-to-r from-success-500/10 to-info-500/10">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-success-500/20 to-info-500/20 rounded-2xl flex items-center justify-center">
              <Mail className="w-6 h-6 text-success-400" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">Todos los Correos</h2>
              <p className="text-sm text-dark-400">{mails.length} correos cargados</p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-2.5 hover:bg-dark-800 rounded-xl transition-all hover:scale-105 active:scale-95"
          >
            <X className="w-5 h-5 text-dark-400 hover:text-white" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-6 custom-scrollbar" onScroll={handleScroll}>
          {mails.length === 0 ? (
            <div className="text-center py-12">
              <Mail className="w-16 h-16 mx-auto mb-4 text-[var(--text-secondary)] opacity-50" />
              <p className="text-[var(--text-secondary)]">No hay correos recientes</p>
            </div>
          ) : (
            <>
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
              
              {loading && (
                <div className="text-center py-4">
                  <Loader2 className="w-6 h-6 animate-spin text-primary-400 mx-auto" />
                  <p className="text-sm text-dark-400 mt-2">Cargando más correos...</p>
                </div>
              )}
              
              {!hasMore && mails.length > 0 && (
                <div className="text-center py-4 text-sm text-dark-400">
                  No hay más correos para cargar
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function CalendarView({ events = [], loading = false, onViewAll }) {
  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4 px-1">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-primary-500/20 to-secondary-500/20 rounded-xl shadow-glow">
            <Calendar className="w-5 h-5 text-primary-400" />
          </div>
          <h3 className="text-base font-bold text-white">Calendario</h3>
        </div>
        {events.length > 0 && (
          <button 
            onClick={onViewAll} 
            className="text-xs text-primary-400 hover:text-primary-300 font-semibold flex items-center gap-1.5 transition-all hover:scale-105 active:scale-95"
          >
            Ver todo
            <ExternalLink className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
      
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {loading ? (
          <LoadingSpinner size="sm" />
        ) : events.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-8">
            <div className="w-16 h-16 bg-dark-700/50 rounded-2xl flex items-center justify-center mb-4">
              <Calendar className="w-8 h-8 text-dark-500" />
            </div>
            <p className="text-sm text-dark-400">No hay eventos próximos</p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {events.slice(0, 5).map(ev => (
              <div key={ev.id} className="p-3.5 rounded-xl bg-dark-900/60 backdrop-blur-sm hover:bg-dark-900/80 border border-dark-700 hover:border-primary-500/30 transition-all group cursor-pointer hover:shadow-glow">
                <div className="text-sm font-semibold mb-2 text-white group-hover:text-primary-400 transition-colors line-clamp-1">{ev.summary || ev.title}</div>
                <div className="flex items-center gap-2 text-xs text-dark-400">
                  <Clock className="w-3.5 h-3.5" />
                  <span>{ev.start}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function InboxView({ mails = [], loading = false, onViewAll }) {
  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4 px-1">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-success-500/20 to-info-500/20 rounded-xl shadow-glow">
            <Mail className="w-5 h-5 text-success-400" />
          </div>
          <h3 className="text-base font-bold text-white">Correos</h3>
        </div>
        {mails.length > 0 && (
          <button 
            onClick={onViewAll} 
            className="text-xs text-success-400 hover:text-success-300 font-semibold flex items-center gap-1.5 transition-all hover:scale-105 active:scale-95"
          >
            Ver todo
            <ExternalLink className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
      
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {loading ? (
          <LoadingSpinner size="sm" />
        ) : mails.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-8">
            <div className="w-16 h-16 bg-dark-700/50 rounded-2xl flex items-center justify-center mb-4">
              <Mail className="w-8 h-8 text-dark-500" />
            </div>
            <p className="text-sm text-dark-400">No hay correos recientes</p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {mails.slice(0, 5).map(mail => (
              <div key={mail.id} className="p-3.5 rounded-xl bg-dark-900/60 backdrop-blur-sm hover:bg-dark-900/80 border border-dark-700 hover:border-success-500/30 transition-all group cursor-pointer hover:shadow-glow">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold mb-1.5 text-white group-hover:text-success-400 transition-colors line-clamp-1">{mail.subject}</p>
                    <p className="text-xs text-dark-400 line-clamp-1">{mail.from}</p>
                  </div>
                  <div className="text-xs text-dark-500 whitespace-nowrap flex-shrink-0">
                    {mail.time || mail.internalDate || ''}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
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
  const [activeTab, setActiveTab] = useState('calendar') // 'calendar', 'email', 'contacts', 'timeline'

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
    
    // Listen for calendar updates from chat confirmations
    const handleCalendarUpdate = () => {
      console.log('📅 Calendar update event received, refreshing data...')
      if (connected) {
        fetchData()
      }
    }
    
    window.addEventListener('calendarUpdated', handleCalendarUpdate)
    
    return () => {
      window.removeEventListener('message', handleMessage)
      window.removeEventListener('calendarUpdated', handleCalendarUpdate)
    }
  }, [connected])

  const handleConnect = () => {
    const userId = user?.id || 'default_user'
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
    const result = await Swal.fire({
      title: '¿Desconectar Google?',
      text: 'Se desconectará tu calendario y correo',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#3B82F6',
      cancelButtonColor: '#6b7280',
      confirmButtonText: 'Sí, desconectar',
      cancelButtonText: 'Cancelar',
      background: 'var(--bg-panel)',
      color: 'var(--text-primary)'
    })

    if (!result.isConfirmed) return

    const res = await authService.revokeGoogleAccess()
    if (res.success) {
      setConnected(false)
      setEvents([])
      setMails([])
      setGoogleConnected(false, null)
      Swal.fire({ 
        icon: 'success', 
        title: 'Desconectado', 
        text: 'Cuenta Google desconectada correctamente',
        background: 'var(--bg-panel)',
        color: 'var(--text-primary)',
        timer: 2000,
        showConfirmButton: false
      })
    } else {
      Swal.fire({ 
        icon: 'error', 
        title: 'Error', 
        text: String(res.error || 'No se pudo desconectar'),
        background: 'var(--bg-panel)',
        color: 'var(--text-primary)'
      })
    }
  }

  return (
    <>
      <div className="flex flex-col h-full bg-dark-900/60 backdrop-blur-xl rounded-3xl border border-dark-800 shadow-2xl overflow-hidden">
        {/* Tabs Header */}
        <div className="flex border-b border-dark-800 bg-gradient-to-r from-dark-900/80 to-dark-800/80 backdrop-blur-sm">
          <button
            onClick={() => setActiveTab('calendar')}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-3.5 text-sm font-semibold transition-all ${
              activeTab === 'calendar'
                ? 'text-primary-400 border-b-2 border-primary-400 bg-primary-500/10 shadow-glow-sm'
                : 'text-dark-400 hover:text-white hover:bg-dark-800/60'
            }`}
          >
            <Calendar className="w-4.5 h-4.5" />
            <span className="hidden sm:inline">Calendario</span>
          </button>
          
          <button
            onClick={() => setActiveTab('email')}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-3.5 text-sm font-semibold transition-all ${
              activeTab === 'email'
                ? 'text-success-400 border-b-2 border-success-400 bg-success-500/10 shadow-glow-sm'
                : 'text-dark-400 hover:text-white hover:bg-dark-800/60'
            }`}
          >
            <Mail className="w-4.5 h-4.5" />
            <span className="hidden sm:inline">Correos</span>
          </button>
          
          <button
            onClick={() => setActiveTab('contacts')}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-3.5 text-sm font-semibold transition-all ${
              activeTab === 'contacts'
                ? 'text-secondary-400 border-b-2 border-secondary-400 bg-secondary-500/10 shadow-glow-sm'
                : 'text-dark-400 hover:text-white hover:bg-dark-800/60'
            }`}
          >
            <Users className="w-4.5 h-4.5" />
            <span className="hidden sm:inline">Contactos</span>
          </button>
          
          <button
            onClick={() => setActiveTab('timeline')}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-3.5 text-sm font-semibold transition-all ${
              activeTab === 'timeline'
                ? 'text-warning-400 border-b-2 border-warning-400 bg-warning-500/10 shadow-glow-sm'
                : 'text-dark-400 hover:text-white hover:bg-dark-800/60'
            }`}
          >
            <Clock className="w-4.5 h-4.5" />
            <span className="hidden sm:inline">Timeline</span>
          </button>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-hidden">
          {activeTab === 'calendar' && (
            <div className="h-full overflow-y-auto p-4 lg:p-5 custom-scrollbar animate-fadeIn">
              <CalendarView 
                events={events} 
                loading={loadingData} 
                onViewAll={() => setShowCalendarModal(true)} 
              />
            </div>
          )}
          
          {activeTab === 'email' && (
            <div className="h-full overflow-y-auto p-4 lg:p-5 custom-scrollbar animate-fadeIn">
              <InboxView 
                mails={mails} 
                loading={loadingData} 
                onViewAll={() => setShowEmailModal(true)} 
              />
            </div>
          )}
          
          {activeTab === 'contacts' && (
            <div className="h-full animate-fadeIn">
              <ContactsPanel />
            </div>
          )}
          
          {activeTab === 'timeline' && (
            <div className="h-full overflow-y-auto p-4 lg:p-5 custom-scrollbar animate-fadeIn">
              <AgentTimeline activity={activity} />
            </div>
          )}
        </div>
      </div>

      {showCalendarModal && ReactDOM.createPortal(
        <CalendarModal events={events} onClose={() => setShowCalendarModal(false)} />,
        document.body
      )}
      
      {showEmailModal && ReactDOM.createPortal(
        <EmailModal mails={mails} onClose={() => setShowEmailModal(false)} />,
        document.body
      )}
    </>
  )
}

