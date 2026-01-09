import { useState } from 'react'
import ChatInterface from './components/ChatInterface'
import FileUpload from './components/FileUpload'
import AgentTimeline from './components/AgentTimeline'
import FileManager from './components/FileManager'
import { Bot, FolderOpen } from 'lucide-react'

function App() {
  const [messages, setMessages] = useState([])
  const [agentActivity, setAgentActivity] = useState([])
  const [showFileManager, setShowFileManager] = useState(false)

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-gray-100">
      {/* Header */}
      <header className="bg-gradient-to-r from-gray-800 via-gray-900 to-gray-800 border-b border-gray-700 px-6 py-4 shadow-lg">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center shadow-lg shadow-primary-500/30">
              <Bot className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">ServiBot</h1>
              <p className="text-sm text-gray-400">Asistente de IA Autónomo</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setShowFileManager(true)}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white rounded-xl transition-all shadow-lg hover:shadow-blue-500/30 transform hover:scale-105"
            >
              <FolderOpen className="w-5 h-5" />
              <span className="font-medium">Gestor de Archivos</span>
            </button>
            <span className="px-4 py-2 bg-green-500/20 text-green-400 rounded-xl text-sm font-medium border border-green-500/30 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
              Online
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chat Section - Takes 2 columns */}
          <div className="lg:col-span-2 space-y-6">
            <ChatInterface 
              messages={messages} 
              setMessages={setMessages}
              setAgentActivity={setAgentActivity}
            />
            <FileUpload />
          </div>

          {/* Activity Timeline - Takes 1 column */}
          <div className="lg:col-span-1">
            <AgentTimeline activity={agentActivity} />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gradient-to-r from-gray-800 via-gray-900 to-gray-800 border-t border-gray-700 px-6 py-4 mt-12">
        <div className="max-w-7xl mx-auto text-center text-sm text-gray-400">
          <p className="flex items-center justify-center gap-2">
            <span className="w-1 h-1 rounded-full bg-primary-400"></span>
            ServiBot v0.1.0 - Capstone Project 2025
            <span className="w-1 h-1 rounded-full bg-primary-400"></span>
          </p>
        </div>
      </footer>

      {/* File Manager Modal */}
      <FileManager isOpen={showFileManager} onClose={() => setShowFileManager(false)} />
    </div>
  )
}

export default App
