import ChatInterface from '../components/ChatInterface'
import FileUpload from '../components/FileUpload'
import AgentTimeline from '../components/AgentTimeline'
import AgentPanel from '../components/AgentPanel'
import { useAuthStore, useSettingsStore, useChatStore } from '../store'
import { useNavigate } from 'react-router-dom'
import Swal from 'sweetalert2'
import { Files, Sparkles, LogOut, User, ChevronDown, Menu, X } from 'lucide-react'
import { useState } from 'react'

export default function AppPage() {
  const { user, logout } = useAuthStore()
  const { setShowFileManager } = useSettingsStore()
  const navigate = useNavigate()
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [showMobileMenu, setShowMobileMenu] = useState(false)
  
  // Extract chat store values correctly
  const messages = useChatStore((state) => state.messages)
  const setMessages = useChatStore((state) => state.setMessages)
  const agentActivity = useChatStore((state) => state.agentActivity)
  const setAgentActivity = useChatStore((state) => state.setAgentActivity)

  const handleLogout = async () => {
    const result = await Swal.fire({
      title: '¿Cerrar sesión?',
      text: 'Tendrás que volver a iniciar sesión',
      icon: 'question',
      showCancelButton: true,
      confirmButtonColor: '#3B82F6',
      cancelButtonColor: '#6366F1',
      confirmButtonText: 'Sí, cerrar sesión',
      cancelButtonText: 'Cancelar',
      background: '#141B2D',
      color: '#F1F5F9',
      customClass: {
        popup: 'rounded-2xl border border-dark-800'
      }
    })

    if (result.isConfirmed) {
      await logout()
      navigate('/login', { replace: true })
    }
  }

  return (
    <div className="h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white flex flex-col overflow-hidden relative">
      {/* Background Gradient Orbs - Ultra Enhanced */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-[700px] h-[700px] bg-gradient-to-br from-primary-500/30 to-secondary-500/20 rounded-full blur-3xl animate-float"></div>
        <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-gradient-to-tr from-secondary-500/30 to-accent-500/20 rounded-full blur-3xl animate-float" style={{ animationDelay: '1s' }}></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-gradient-to-r from-accent-500/25 to-primary-500/20 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }}></div>
        
        {/* Floating Particles */}
        {[...Array(30)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1.5 h-1.5 rounded-full animate-float"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${3 + Math.random() * 4}s`,
              background: i % 3 === 0 ? 'rgba(139, 92, 246, 0.5)' : i % 3 === 1 ? 'rgba(236, 72, 153, 0.5)' : 'rgba(245, 158, 11, 0.5)'
            }}
          />
        ))}
        
        {/* Animated Grid Pattern */}
        <svg className="absolute inset-0 w-full h-full opacity-[0.08]" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      {/* Modern Header */}
      <header style={{ zIndex: 'var(--z-popover)' }} className="relative glass-effect border-b border-white/10 px-4 lg:px-6 py-3 animate-slideIn shadow-lg shadow-primary-500/10">
        <div className="flex items-center justify-between">
          {/* Logo & Brand */}
          <div className="flex items-center gap-4 group">
            <div className="relative w-11 h-11 bg-gradient-to-br from-primary-500 via-secondary-500 to-accent-500 rounded-xl flex items-center justify-center shadow-glow-strong group-hover:shadow-[0_0_50px_rgba(59,130,246,0.8)] transition-all duration-300 group-hover:scale-110 group-hover:rotate-6 animate-pulse-glow">
              <Sparkles className="w-6 h-6 text-white" />
              <div className="absolute inset-0 bg-gradient-to-br from-primary-400 to-secondary-400 rounded-xl opacity-0 group-hover:opacity-40 blur-xl transition-opacity"></div>
            </div>
            <div className="hidden sm:block">
              <h1 className="text-xl font-bold bg-gradient-to-r from-primary-400 via-secondary-400 to-accent-400 bg-clip-text text-transparent animate-gradient relative inline-block">
                ServiBot
              </h1>
              <p className="text-xs text-slate-400 transition-colors group-hover:text-primary-300">Asistente IA Multimodal</p>
            </div>
          </div>

          {/* Desktop Actions */}
          <div className="hidden lg:flex items-center gap-2 xl:gap-3 animate-slideInFromRight">
            <button
              onClick={() => setShowFileManager(true)}
              className="relative flex items-center gap-1.5 xl:gap-2 px-3 xl:px-4 py-2.5 bg-primary-500/10 hover:bg-primary-500/20 border border-primary-500/20 text-primary-300 text-sm font-medium rounded-xl transition-all hover:scale-105 active:scale-95 group overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-primary-500/0 via-primary-500/20 to-primary-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
              <Files className="w-4 h-4 relative z-10 group-hover:rotate-12 transition-transform" />
              <span className="relative z-10">Gestor de Archivos</span>
            </button>
            
            {user && (
              <div className="relative">
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="relative flex items-center gap-3 px-4 py-2 bg-dark-800/50 hover:bg-dark-800 border border-dark-700 hover:border-primary-500/30 rounded-xl transition-all group overflow-hidden"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-primary-500/0 via-primary-500/10 to-primary-500/0 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                  {user.picture && (
                    <div className="relative">
                      <img 
                        src={user.picture} 
                        alt={user.name}
                        className="w-8 h-8 rounded-lg border-2 border-primary-500/30 group-hover:border-primary-400/60 transition-all group-hover:scale-110"
                      />
                      <div className="absolute inset-0 rounded-lg bg-primary-400/20 opacity-0 group-hover:opacity-100 blur-md transition-opacity"></div>
                    </div>
                  )}
                  <div className="hidden xl:block text-left relative z-10">
                    <p className="text-sm font-medium text-white group-hover:text-primary-300 transition-colors">{user.name}</p>
                    <p className="text-xs text-dark-400 group-hover:text-dark-300 transition-colors">{user.email}</p>
                  </div>
                  <ChevronDown className={`w-4 h-4 text-dark-400 group-hover:text-primary-400 transition-all ${showUserMenu ? 'rotate-180' : ''}`} />
                </button>

                {/* User Dropdown */}
                {showUserMenu && (
                  <div style={{ zIndex: 'var(--z-modal)', position: 'absolute' }} className="right-0 mt-2 w-64 bg-dark-900 border border-dark-800 rounded-xl shadow-2xl overflow-hidden animate-scaleIn">
                    <div className="p-4 border-b border-dark-800">
                      <p className="text-sm font-semibold text-white">{user.name}</p>
                      <p className="text-xs text-dark-400 mt-1">{user.email}</p>
                    </div>
                    <button
                      onClick={() => {
                        setShowUserMenu(false)
                        handleLogout()
                      }}
                      className="w-full flex items-center gap-3 px-4 py-3 text-sm text-danger-400 hover:bg-danger-500/10 transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Cerrar Sesión</span>
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setShowMobileMenu(!showMobileMenu)}
            className="lg:hidden p-2 bg-dark-800 hover:bg-dark-700 rounded-lg border border-dark-700 hover:border-primary-500/30 transition-all group relative overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-primary-500/0 via-primary-500/20 to-primary-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-500"></div>
            {showMobileMenu ? <X className="w-5 h-5 relative z-10 transition-transform rotate-0 group-hover:rotate-90" /> : <Menu className="w-5 h-5 relative z-10 transition-transform group-hover:scale-110" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {showMobileMenu && (
          <div className="lg:hidden mt-4 pb-4 space-y-3 border-t border-dark-800 pt-4 animate-slideIn">
            <button
              onClick={() => {
                setShowFileManager(true)
                setShowMobileMenu(false)
              }}
              className="w-full flex items-center gap-3 px-4 py-3 bg-primary-500/10 hover:bg-primary-500/20 border border-primary-500/20 hover:border-primary-500/40 text-primary-300 rounded-xl transition-all hover:scale-[1.02] active:scale-95 group relative overflow-hidden"
              style={{ animationDelay: '0.1s' }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-primary-500/0 via-primary-500/30 to-primary-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
              <Files className="w-5 h-5 relative z-10 group-hover:rotate-12 transition-transform" />
              <span className="text-sm font-medium relative z-10">Gestor de Archivos</span>
            </button>
            <button
              onClick={() => {
                setShowMobileMenu(false)
                handleLogout()
              }}
              className="w-full flex items-center gap-3 px-4 py-3 bg-danger-500/10 hover:bg-danger-500/20 border border-danger-500/20 hover:border-danger-500/40 text-danger-300 rounded-xl transition-all hover:scale-[1.02] active:scale-95 group relative overflow-hidden"
              style={{ animationDelay: '0.2s' }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-danger-500/0 via-danger-500/30 to-danger-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
              <LogOut className="w-5 h-5 relative z-10 group-hover:-rotate-12 transition-transform" />
              <span className="text-sm font-medium relative z-10">Cerrar Sesión</span>
            </button>
          </div>
        )}
      </header>

      {/* Main Content - Fluid Modern Layout */}
      <div className="relative z-10 flex-1 overflow-hidden">
        <div className="h-full flex flex-col lg:flex-row gap-4 p-4">
          {/* Primary Column - Chat (Main Focus) */}
          <div className="flex-1 flex flex-col min-w-0 min-h-0 min-h-0 space-y-4 animate-slideIn" style={{ animationDelay: '0.1s' }}>
            <div className="relative group h-full">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-primary-500/20 via-secondary-500/20 to-accent-500/20 rounded-3xl blur opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative h-full">
                <ChatInterface 
                  messages={messages}
                  setMessages={setMessages}
                  setAgentActivity={setAgentActivity}
                />
              </div>
            </div>
          </div>

          {/* Secondary Column - Tools & Upload */}
          <div className="w-full lg:w-80 xl:w-96 flex flex-col gap-4 min-h-0 animate-slideInFromRight" style={{ animationDelay: '0.2s' }}>
            {/* File Upload Card */}
            <div className="flex-shrink-0 relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-info-500/20 to-primary-500/20 rounded-3xl blur opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative transform transition-transform hover:scale-[1.01]">
                <FileUpload />
              </div>
            </div>

            {/* Agent Panel - Scrollable */}
            <div className="flex-1 min-h-0 overflow-hidden relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-secondary-500/20 to-accent-500/20 rounded-3xl blur opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative h-full transform transition-transform hover:scale-[1.01]">
                <AgentPanel activity={agentActivity} setAgentActivity={setAgentActivity} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
