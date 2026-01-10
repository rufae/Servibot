import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import LoginPage from './pages/LoginPage'
import AuthCallback from './pages/AuthCallback'
import AppPage from './pages/AppPage'
import ProtectedRoute from './components/ProtectedRoute'
import FileManager from './components/FileManager'
import ErrorBoundary from './components/ErrorBoundary'
import { useSettingsStore, useAuthStore } from './store'

function App() {
  const { showFileManager, setShowFileManager } = useSettingsStore()
  const { checkAuth } = useAuthStore()

  // Check auth on mount
  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        
        {/* Protected routes */}
        <Route 
          path="/app" 
          element={
            <ProtectedRoute>
              <AppPage />
            </ProtectedRoute>
          } 
        />
        
        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>

      {/* Global File Manager Modal */}
      {showFileManager && (
        <ErrorBoundary>
          <FileManager isOpen={showFileManager} onClose={() => setShowFileManager(false)} />
        </ErrorBoundary>
      )}
    </BrowserRouter>
  )
}

export default App
