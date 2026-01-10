import ChatInterface from '../components/ChatInterface'
import FileUpload from '../components/FileUpload'
import AgentTimeline from '../components/AgentTimeline'
import GoogleToolsTest from '../components/GoogleToolsTest'
import { useAuthStore, useSettingsStore, useChatStore } from '../store'
import { useNavigate } from 'react-router-dom'
import Swal from 'sweetalert2'

export default function AppPage() {
  const { user, logout } = useAuthStore()
  const { setShowFileManager } = useSettingsStore()
  const navigate = useNavigate()
  
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
      confirmButtonColor: '#ef4444',
      cancelButtonColor: '#6b7280',
      confirmButtonText: 'Sí, cerrar sesión',
      cancelButtonText: 'Cancelar',
      background: '#1f2937',
      color: '#f3f4f6'
    })

    if (result.isConfirmed) {
      await logout()
      navigate('/login', { replace: true })
    }
  }

  return (
    <div className="h-screen bg-gray-900 text-white flex flex-col">
      {/* Header */}
      <header className="bg-gray-800/50 backdrop-blur-sm border-b border-gray-700 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
              ServiBot
            </h1>
            <p className="text-xs text-gray-400">Asistente Inteligente</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={() => setShowFileManager(true)}
            className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
            <span className="hidden sm:inline">Gestor de Archivos</span>
            <span className="sm:hidden">Archivos</span>
          </button>
          
          {user && (
            <div className="flex items-center gap-3">
              {user.picture && (
                <img 
                  src={user.picture} 
                  alt={user.name}
                  className="w-8 h-8 rounded-full border-2 border-blue-500/30"
                />
              )}
              <div className="hidden sm:block text-right">
                <p className="text-sm font-medium text-gray-200">{user.name}</p>
                <p className="text-xs text-gray-400">{user.email}</p>
              </div>
            </div>
          )}
          
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 text-sm font-medium rounded-lg transition-colors"
          >
            Cerrar Sesión
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full grid grid-cols-1 lg:grid-cols-[1fr_350px_400px] gap-4 p-4">
          {/* Left Column - Chat */}
          <div className="flex flex-col space-y-4 min-h-0">
            <ChatInterface 
              messages={messages}
              setMessages={setMessages}
              setAgentActivity={setAgentActivity}
            />
          </div>

          {/* Middle Column - Upload */}
          <div className="flex flex-col min-h-0">
            <FileUpload />
          </div>

          {/* Right Column - Agent Activity + Google Tools */}
          <div className="flex flex-col space-y-4 overflow-y-auto">
            <AgentTimeline activity={agentActivity} />
            
            <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-4">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />
                </svg>
                Google Integration
              </h2>
              <GoogleToolsTest />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
