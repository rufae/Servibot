import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import authService from '../services/authService'
import { useAuthStore } from '../store'
import { Sparkles, MessageSquare, Calendar, Mail, FileText, Zap, Shield, Cpu } from 'lucide-react'

export default function LoginPage() {
  const navigate = useNavigate()
  const { isAuthenticated, checkAuth } = useAuthStore()
  const [error, setError] = useState(null)
  const [isHovering, setIsHovering] = useState(false)

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/app', { replace: true })
    }
  }, [isAuthenticated, navigate])

  const handleGoogleLogin = () => {
    // Mantener funcionalidad exacta - redirigir al backend OAuth
    window.location.href = 'http://localhost:8000/auth/google/start'
  }

  return (
    <div className="min-h-screen bg-dark-950 relative overflow-hidden flex items-center justify-center p-4">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Gradient Orbs */}
        <div className="absolute top-0 -left-40 w-96 h-96 bg-primary-500/20 rounded-full blur-3xl animate-float"></div>
        <div className="absolute top-20 -right-40 w-96 h-96 bg-secondary-500/20 rounded-full blur-3xl animate-float delay-200"></div>
        <div className="absolute -bottom-20 left-1/2 -translate-x-1/2 w-96 h-96 bg-accent-500/20 rounded-full blur-3xl animate-float delay-400"></div>
        
        {/* Grid Pattern */}
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAwIDEwIEwgNDAgMTAgTSAxMCAwIEwgMTAgNDAgTSAwIDIwIEwgNDAgMjAgTSAyMCAwIEwgMjAgNDAgTSAwIDMwIEwgNDAgMzAgTSAzMCAwIEwgMzAgNDAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSg5OSwgMTAyLCAyNDEsIDAuMDUpIiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-30"></div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 w-full max-w-6xl grid lg:grid-cols-2 gap-8 items-center">
        {/* Left Side - Hero Content */}
        <div className="space-y-8 animate-slide-in-left">
          {/* Logo & Brand */}
          <div className="space-y-4">
            <div className="inline-flex items-center gap-3 px-4 py-2 bg-primary-500/10 border border-primary-500/20 rounded-full backdrop-blur-sm">
              <Sparkles className="w-4 h-4 text-primary-400" />
              <span className="text-sm font-medium text-primary-300">Asistente IA Multimodal</span>
            </div>
            
            <h1 className="text-6xl lg:text-7xl font-bold tracking-tight">
              <span className="text-white">Bienvenido a</span>
              <br />
              <span className="text-gradient animate-gradient">ServiBot</span>
            </h1>
            
            <p className="text-xl text-dark-400 max-w-lg leading-relaxed">
              Tu compañero inteligente para gestionar documentos, calendario, correos y mucho más. 
              Todo en un solo lugar, potenciado por IA.
            </p>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div className="group p-4 bg-dark-900/50 border border-dark-800 rounded-2xl hover:border-primary-500/30 transition-all duration-300 hover:scale-105">
              <div className="w-12 h-12 bg-gradient-to-br from-primary-500/20 to-secondary-500/20 rounded-xl flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                <MessageSquare className="w-6 h-6 text-primary-400" />
              </div>
              <h3 className="text-white font-semibold mb-1">Chat Inteligente</h3>
              <p className="text-sm text-dark-400">Consulta tus documentos con IA</p>
            </div>

            <div className="group p-4 bg-dark-900/50 border border-dark-800 rounded-2xl hover:border-secondary-500/30 transition-all duration-300 hover:scale-105">
              <div className="w-12 h-12 bg-gradient-to-br from-secondary-500/20 to-accent-500/20 rounded-xl flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                <Calendar className="w-6 h-6 text-secondary-400" />
              </div>
              <h3 className="text-white font-semibold mb-1">Google Calendar</h3>
              <p className="text-sm text-dark-400">Gestiona tu agenda</p>
            </div>

            <div className="group p-4 bg-dark-900/50 border border-dark-800 rounded-2xl hover:border-success-500/30 transition-all duration-300 hover:scale-105">
              <div className="w-12 h-12 bg-gradient-to-br from-success-500/20 to-info-500/20 rounded-xl flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                <Mail className="w-6 h-6 text-success-400" />
              </div>
              <h3 className="text-white font-semibold mb-1">Gmail</h3>
              <p className="text-sm text-dark-400">Envía correos rápido</p>
            </div>

            <div className="group p-4 bg-dark-900/50 border border-dark-800 rounded-2xl hover:border-warning-500/30 transition-all duration-300 hover:scale-105">
              <div className="w-12 h-12 bg-gradient-to-br from-warning-500/20 to-danger-500/20 rounded-xl flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                <FileText className="w-6 h-6 text-warning-400" />
              </div>
              <h3 className="text-white font-semibold mb-1">Documentos</h3>
              <p className="text-sm text-dark-400">Genera PDF y Excel</p>
            </div>
          </div>

          {/* Trust Indicators */}
          <div className="flex items-center gap-6 pt-4">
            <div className="flex items-center gap-2 text-dark-400">
              <Shield className="w-5 h-5 text-primary-400" />
              <span className="text-sm">Seguro y Privado</span>
            </div>
            <div className="flex items-center gap-2 text-dark-400">
              <Zap className="w-5 h-5 text-warning-400" />
              <span className="text-sm">Súper Rápido</span>
            </div>
            <div className="flex items-center gap-2 text-dark-400">
              <Cpu className="w-5 h-5 text-info-400" />
              <span className="text-sm">IA Avanzada</span>
            </div>
          </div>
        </div>

        {/* Right Side - Login Card */}
        <div className="animate-slide-in-right">
          <div className="relative group">
            {/* Glow Effect */}
            <div className="absolute -inset-1 bg-gradient-to-r from-primary-500 via-secondary-500 to-accent-500 rounded-3xl blur-xl opacity-20 group-hover:opacity-40 transition-opacity duration-500"></div>
            
            {/* Card */}
            <div className="relative bg-dark-900/80 backdrop-blur-xl border border-dark-800 rounded-3xl p-8 lg:p-12 space-y-8 shadow-2xl">
              {/* Card Header */}
              <div className="text-center space-y-4">
                <div className="inline-flex justify-center">
                  <div className="relative">
                    <img src="/Servibot.png" alt="ServiBot" className="w-24 h-24 object-contain mx-auto" />
                  </div>
                </div>
                
                <div>
                  <h2 className="text-3xl font-bold text-white mb-2">
                    Iniciar Sesión
                  </h2>
                  <p className="text-dark-400">
                    Usa tu cuenta de Google para continuar
                  </p>
                </div>
              </div>

              {/* Login Button */}
              <div className="space-y-6">
                <button
                  onClick={handleGoogleLogin}
                  onMouseEnter={() => setIsHovering(true)}
                  onMouseLeave={() => setIsHovering(false)}
                  className="w-full group relative bg-white hover:bg-gray-50 text-gray-900 font-semibold py-5 px-6 rounded-2xl transition-all duration-300 shadow-lg hover:shadow-2xl transform hover:scale-[1.02] active:scale-[0.98] overflow-hidden"
                >
                  {/* Shimmer effect */}
                  <div className={`absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent -translate-x-full ${isHovering ? 'animate-shimmer' : ''}`}></div>
                  
                  <div className="relative flex items-center justify-center gap-4">
                    {/* Google Logo */}
                    <svg className="w-7 h-7 flex-shrink-0" viewBox="0 0 24 24">
                      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                    <span className="text-lg">Continuar con Google</span>
                    <svg className="w-5 h-5 transform group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </div>
                </button>

                {error && (
                  <div className="bg-danger-500/10 border border-danger-500/30 rounded-xl p-4 backdrop-blur-sm animate-scaleIn">
                    <div className="flex items-center gap-3">
                      <svg className="w-5 h-5 text-danger-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <p className="text-danger-300 text-sm">{error}</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Features Preview */}
              <div className="pt-6 border-t border-dark-800 space-y-3">
                <p className="text-xs text-dark-400 text-center mb-4">
                  Al continuar, obtendrás acceso a:
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex items-center gap-2 text-dark-400 text-sm">
                    <div className="w-1.5 h-1.5 bg-primary-400 rounded-full"></div>
                    <span>Chat con documentos</span>
                  </div>
                  <div className="flex items-center gap-2 text-dark-400 text-sm">
                    <div className="w-1.5 h-1.5 bg-secondary-400 rounded-full"></div>
                    <span>Gestión de calendario</span>
                  </div>
                  <div className="flex items-center gap-2 text-dark-400 text-sm">
                    <div className="w-1.5 h-1.5 bg-success-400 rounded-full"></div>
                    <span>Envío de emails</span>
                  </div>
                  <div className="flex items-center gap-2 text-dark-400 text-sm">
                    <div className="w-1.5 h-1.5 bg-warning-400 rounded-full"></div>
                    <span>Generación de docs</span>
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="text-center pt-4">
                <p className="text-xs text-dark-500">
                  Al continuar, aceptas nuestros{' '}
                  <button className="text-primary-400 hover:text-primary-300 transition-colors underline-offset-2 hover:underline">
                    términos de servicio
                  </button>
                  {' '}y{' '}
                  <button className="text-primary-400 hover:text-primary-300 transition-colors underline-offset-2 hover:underline">
                    política de privacidad
                  </button>
                </p>
              </div>
            </div>
          </div>

          {/* Bottom Text */}
          <div className="mt-8 text-center animate-fadeIn delay-300">
            <p className="text-dark-400 text-sm flex items-center justify-center gap-2">
              <span>Desarrollado con</span>
              <svg className="w-4 h-4 text-danger-400 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
              </svg>
              <span>por el equipo de ServiBot</span>
            </p>
          </div>
        </div>
      </div>

      {/* Floating particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(20)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-primary-400/30 rounded-full animate-float"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 3}s`,
              animationDuration: `${3 + Math.random() * 4}s`
            }}
          />
        ))}
      </div>
    </div>
  )
}
