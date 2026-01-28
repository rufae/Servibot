import { create } from 'zustand'

/**
 * Global chat store using Zustand
 * Manages messages and agent activity state
 */
export const useChatStore = create((set) => ({
  // Messages state
  messages: [],
  addMessage: (message) => set((state) => ({ 
    messages: [...state.messages, message] 
  })),
  setMessages: (messagesOrFn) => set((state) => ({ 
    messages: typeof messagesOrFn === 'function' ? messagesOrFn(state.messages) : messagesOrFn 
  })),
  clearMessages: () => set({ messages: [] }),

  // Agent activity state
  agentActivity: [],
  addAgentActivity: (activity) => set((state) => ({ 
    agentActivity: [...state.agentActivity, ...activity] 
  })),
  setAgentActivity: (agentActivityOrFn) => set((state) => ({ 
    agentActivity: typeof agentActivityOrFn === 'function' ? agentActivityOrFn(state.agentActivity) : agentActivityOrFn 
  })),
  clearAgentActivity: () => set({ agentActivity: [] }),

  // Loading state
  isLoading: false,
  setIsLoading: (isLoading) => set({ isLoading }),

  // Audio URLs for TTS
  audioUrlForMessage: {},
  setAudioUrl: (messageIndex, audioUrl) => set((state) => ({
    audioUrlForMessage: {
      ...state.audioUrlForMessage,
      [messageIndex]: audioUrl
    }
  })),

  // Reset entire store
  reset: () => set({
    messages: [],
    agentActivity: [],
    isLoading: false,
    audioUrlForMessage: {},
  }),
}))

/**
 * Contacts store - caches Google Contacts locally and supports forced reload
 */
export const useContactsStore = create((set, get) => ({
  contacts: [],
  lastUpdated: null,
  isLoadingContacts: false,
  errorContacts: null,

  setContacts: (contacts) => {
    const now = Date.now()
    set({ contacts, lastUpdated: now, errorContacts: null })
    try {
      localStorage.setItem('contacts_cache', JSON.stringify({ contacts, lastUpdated: now }))
    } catch (e) {
      // ignore storage errors
    }
  },

  clearContacts: () => {
    set({ contacts: [], lastUpdated: null, errorContacts: null })
    try { localStorage.removeItem('contacts_cache') } catch (e) {}
  },

  loadContacts: async (forceRefresh = false) => {
    // If not forcing and we have a cache, use it
    if (!forceRefresh) {
      try {
        const raw = localStorage.getItem('contacts_cache')
        if (raw) {
          const parsed = JSON.parse(raw)
          if (parsed && Array.isArray(parsed.contacts) && parsed.contacts.length > 0) {
            set({ contacts: parsed.contacts, lastUpdated: parsed.lastUpdated, errorContacts: null })
            return
          }
        }
      } catch (e) {
        // continue to fetch if cache is invalid
      }
    }

    set({ isLoadingContacts: true, errorContacts: null })

    try {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        set({ errorContacts: 'No estás autenticado', isLoadingContacts: false })
        return
      }

      const res = await fetch('http://localhost:8000/api/google/contacts?page_size=200', {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (res.status === 403) {
        set({ errorContacts: 'Conecta tu cuenta de Google para ver tus contactos', isLoadingContacts: false })
        return
      }

      if (!res.ok) {
        throw new Error('Error al cargar contactos')
      }

      const data = await res.json()
      const contacts = data.contacts || []
      const now = Date.now()
      set({ contacts, lastUpdated: now, isLoadingContacts: false, errorContacts: null })
      try { localStorage.setItem('contacts_cache', JSON.stringify({ contacts, lastUpdated: now })) } catch (e) {}
    } catch (err) {
      console.error('Contacts load failed:', err)
      set({ errorContacts: err.message || 'Error al cargar contactos', isLoadingContacts: false })
    }
  },

  reloadContacts: () => get().loadContacts(true),
}))

/**
 * Global file upload store
 */
export const useUploadStore = create((set) => ({
  // Uploaded files state
  uploadedFiles: [],
  addUploadedFile: (file) => set((state) => ({ 
    uploadedFiles: [...state.uploadedFiles, file] 
  })),
  updateUploadedFile: (fileName, updates) => set((state) => ({
    uploadedFiles: state.uploadedFiles.map(f => 
      f.name === fileName ? { ...f, ...updates } : f
    )
  })),
  updateUploadedFileById: (fileId, updates) => set((state) => ({
    uploadedFiles: state.uploadedFiles.map(f => 
      f.file_id === fileId ? { ...f, ...updates } : f
    )
  })),
  setUploadedFiles: (uploadedFiles) => set({ uploadedFiles }),
  clearUploadedFiles: () => set({ uploadedFiles: [] }),

  // Upload state
  isUploading: false,
  setIsUploading: (isUploading) => set({ isUploading }),
}))

/**
 * Global settings store
 */
export const useSettingsStore = create((set) => ({
  // Voice settings
  voiceEnabled: false,
  setVoiceEnabled: (voiceEnabled) => set({ voiceEnabled }),

  // Theme settings
  theme: 'dark',
  setTheme: (theme) => set({ theme }),

  // File manager modal
  showFileManager: false,
  setShowFileManager: (showFileManager) => set({ showFileManager }),
}))

/**
 * Auth store - manages authentication and Google OAuth state
 */
export const useAuthStore = create((set, get) => ({
  // Authentication state
  isAuthenticated: false,
  isLoading: true,
  user: null, // { id, email, name, picture }
  
  // Google OAuth state
  googleConnected: false,
  googleEmail: null,
  
  // Check authentication status
  checkAuth: async () => {
    set({ isLoading: true })
    
    const token = localStorage.getItem('auth_token')
    
    // No token, not authenticated
    if (!token) {
      set({ 
        isAuthenticated: false,
        user: null,
        googleConnected: false,
        googleEmail: null,
        isLoading: false
      })
      return false
    }
    
    try {
      const response = await fetch('http://localhost:8000/auth/me', {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.authenticated && data.user) {
          set({ 
            isAuthenticated: true,
            user: data.user,
            googleConnected: data.user.google_connected || false,
            googleEmail: data.user.email,
            isLoading: false
          })
          return true
        }
      }
      
      // Si falla la verificación, limpiar token
      localStorage.removeItem('auth_token')
      set({ 
        isAuthenticated: false,
        user: null,
        googleConnected: false,
        googleEmail: null,
        isLoading: false
      })
      return false
    } catch (error) {
      console.error('Auth check failed:', error)
      // En caso de error, limpiar token
      localStorage.removeItem('auth_token')
      set({ 
        isAuthenticated: false,
        user: null,
        googleConnected: false,
        googleEmail: null,
        isLoading: false
      })
      return false
    }
  },
  
  // Logout
  logout: async () => {
    try {
      await fetch('http://localhost:8000/auth/logout', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
        }
      })
    } catch (error) {
      console.error('Logout failed:', error)
    } finally {
      localStorage.removeItem('auth_token')
      set({ 
        isAuthenticated: false,
        user: null,
        googleConnected: false,
        googleEmail: null
      })
    }
  },
  
  setGoogleConnected: (connected, email = null) => set({ 
    googleConnected: connected,
    googleEmail: email 
  }),
  
  // Legacy: kept for backward compatibility
  userId: 'default_user',
  setUserId: (userId) => set({ userId }),
  
  // Reset auth state
  resetAuth: () => set({ 
    isAuthenticated: false,
    user: null,
    googleConnected: false,
    googleEmail: null 
  }),
}))
