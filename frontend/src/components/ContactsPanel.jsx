import { useState, useEffect } from 'react'
import { User, Mail, Phone, Search, RefreshCw, AlertCircle, X } from 'lucide-react'
import Swal from 'sweetalert2'
import { createPortal } from 'react-dom'
import { useContactsStore, useAuthStore } from '../store'

export default function ContactsPanel() {
  const contacts = useContactsStore((s) => s.contacts)
  const [filteredContacts, setFilteredContacts] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const isLoading = useContactsStore((s) => s.isLoadingContacts)
  const error = useContactsStore((s) => s.errorContacts)
  const loadContacts = useContactsStore((s) => s.loadContacts)
  const reloadContacts = useContactsStore((s) => s.reloadContacts)
  const isConnected = useAuthStore((s) => s.googleConnected)
  const [selectedContact, setSelectedContact] = useState(null)
  const [showContactModal, setShowContactModal] = useState(false)

  useEffect(() => {
    loadContacts()
  }, [loadContacts])

  useEffect(() => {
    // Filter contacts based on search query
    if (searchQuery.trim()) {
      const filtered = contacts.filter(contact =>
        contact.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (contact.email || '').toLowerCase().includes(searchQuery.toLowerCase())
      )
      setFilteredContacts(filtered)
    } else {
      setFilteredContacts(contacts)
    }
  }, [searchQuery, contacts])

  const handleRefresh = () => {
    Swal.fire({
      toast: true,
      position: 'top-end',
      icon: 'info',
      title: 'Actualizando contactos...',
      showConfirmButton: false,
      timer: 1500,
      background: 'var(--bg-panel)',
      color: 'var(--text-primary)'
    })
    reloadContacts()
  }

  const handleConnectGoogle = () => {
    window.location.href = '/auth/google'
  }

  const openContactDetails = (contact) => {
    setSelectedContact(contact)
    setShowContactModal(true)
  }

  const closeContactModal = () => {
    setShowContactModal(false)
    setSelectedContact(null)
  }

  if (isLoading && contacts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center">
        <RefreshCw className="w-14 h-14 text-primary-500 animate-spin mb-4 drop-shadow-glow" />
        <p className="text-lg text-white font-semibold">Cargando contactos...</p>
      </div>
    )
  }

  if (error && !isConnected) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center">
        <div className="w-20 h-20 bg-warning-500/20 rounded-2xl flex items-center justify-center mb-5">
          <AlertCircle className="w-12 h-12 text-warning-400" />
        </div>
        <h3 className="text-2xl font-bold text-white mb-3">Conecta Google Contacts</h3>
        <p className="text-dark-400 mb-6 max-w-md leading-relaxed">
          Para acceder a tus contactos y usarlos con ServiBot, necesitas conectar tu cuenta de Google.
        </p>
        <button
          onClick={handleConnectGoogle}
          className="px-6 py-3 bg-gradient-to-r from-primary-600 to-secondary-600 hover:from-primary-500 hover:to-secondary-500 text-white rounded-xl font-semibold transition-all flex items-center gap-2.5 shadow-glow hover:shadow-glow-lg hover:scale-105 active:scale-95"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Conectar Google
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-dark-800/50 backdrop-blur-sm">
      {/* Header */}
      <div className="p-4 lg:p-5 border-b border-dark-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-secondary-500/20 to-accent-500/20 rounded-xl shadow-glow">
              <User className="w-5 h-5 text-secondary-400" />
            </div>
            Contactos
          </h2>
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="p-2.5 rounded-xl bg-secondary-500/10 hover:bg-secondary-500/20 text-secondary-400 transition-all disabled:opacity-50 hover:scale-105 active:scale-95"
            title="Actualizar contactos"
          >
            <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-dark-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Buscar contacto..."
            className="w-full pl-10 pr-4 py-2.5 bg-dark-900/60 backdrop-blur-sm text-white rounded-xl border border-dark-700 focus:border-secondary-500 focus:outline-none focus:ring-2 focus:ring-secondary-500/20 transition-all"
          />
        </div>

        <div className="mt-3 text-sm text-dark-400 font-medium">
          {filteredContacts.length} de {contacts.length} contactos
        </div>
      </div>

      {/* Contacts List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2.5 custom-scrollbar">
        {filteredContacts.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-dark-700/50 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <User className="w-9 h-9 text-dark-500" />
            </div>
            <p className="text-dark-400">
              {searchQuery ? 'No se encontraron contactos' : 'No hay contactos disponibles'}
            </p>
          </div>
        ) : (
          filteredContacts.map((contact, index) => (
            <div
              key={contact.resource_name || index}
              onClick={() => openContactDetails(contact)}
              className="p-3.5 bg-dark-900/60 backdrop-blur-sm rounded-xl border border-dark-700 hover:border-secondary-500/40 hover:bg-dark-900/80 transition-all group cursor-pointer hover:shadow-glow hover:scale-[1.02] active:scale-[0.98]"
            >
              <div className="flex items-center gap-3">
                {/* Avatar */}
                <div className="flex-shrink-0">
                  {contact.photo_url ? (
                    <img
                      src={contact.photo_url}
                      alt={contact.name}
                      className="w-11 h-11 rounded-full border-2 border-dark-700 group-hover:border-secondary-500/40 transition-all"
                    />
                  ) : (
                    <div className="w-11 h-11 rounded-full bg-gradient-to-br from-secondary-500 to-accent-500 flex items-center justify-center text-white font-bold text-lg shadow-glow">
                      {contact.name?.charAt(0)?.toUpperCase() || '?'}
                    </div>
                  )}
                </div>

                {/* Info - Solo nombre */}
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-white truncate group-hover:text-secondary-400 transition-colors">
                    {contact.name || 'Sin nombre'}
                  </h3>
                  <p className="text-xs text-dark-400 mt-0.5">
                    Click para ver detalles
                  </p>
                </div>

                {/* Indicador de información disponible */}
                <div className="flex-shrink-0 flex gap-1.5">
                  {contact.email && (
                    <div className="w-7 h-7 rounded-lg bg-secondary-500/20 flex items-center justify-center border border-secondary-500/30">
                      <Mail className="w-3.5 h-3.5 text-secondary-400" />
                    </div>
                  )}
                  {contact.phone && (
                    <div className="w-7 h-7 rounded-lg bg-accent-500/20 flex items-center justify-center border border-accent-500/30">
                      <Phone className="w-3.5 h-3.5 text-accent-400" />
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Contact Details Modal */}
      {showContactModal && selectedContact && createPortal(
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md flex items-center justify-center z-[9999] p-4 animate-fadeIn">
          <div className="bg-dark-900/95 backdrop-blur-xl rounded-3xl shadow-2xl border border-dark-800 max-w-md w-full animate-scaleIn">
            {/* Header */}
            <div className="p-6 border-b border-dark-800 flex items-center justify-between bg-gradient-to-r from-secondary-500/10 to-accent-500/10">
              <div className="flex items-center gap-4">
                {selectedContact.photo_url ? (
                  <img
                    src={selectedContact.photo_url}
                    alt={selectedContact.name}
                    className="w-16 h-16 rounded-full border-3 border-secondary-500/30 shadow-glow"
                  />
                ) : (
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-secondary-500 to-accent-500 flex items-center justify-center text-white font-bold text-2xl shadow-glow">
                    {selectedContact.name?.charAt(0)?.toUpperCase() || '?'}
                  </div>
                )}
                <div>
                  <h3 className="text-xl font-bold text-white">{selectedContact.name || 'Sin nombre'}</h3>
                  <p className="text-sm text-dark-400">Detalles del contacto</p>
                </div>
              </div>
              <button
                onClick={closeContactModal}
                className="p-2.5 hover:bg-dark-800 rounded-xl transition-all hover:scale-105 active:scale-95"
              >
                <X className="w-5 h-5 text-dark-400 hover:text-white transition-colors" />
              </button>
            </div>

            {/* Body */}
            <div className="p-6 space-y-4">
              {/* Email */}
              {selectedContact.email && (
                <div className="p-4 bg-dark-800/50 backdrop-blur-sm rounded-xl border border-dark-700">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-lg bg-secondary-500/20 flex items-center justify-center border border-secondary-500/30 flex-shrink-0">
                      <Mail className="w-5 h-5 text-secondary-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-dark-400 uppercase mb-1">Email</p>
                      <p className="text-sm text-white break-all">{selectedContact.email}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Additional Emails */}
              {selectedContact.emails && selectedContact.emails.length > 1 && (
                <div className="p-4 bg-dark-800/50 backdrop-blur-sm rounded-xl border border-dark-700">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-lg bg-secondary-500/20 flex items-center justify-center border border-secondary-500/30 flex-shrink-0">
                      <Mail className="w-5 h-5 text-secondary-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-dark-400 uppercase mb-2">Emails adicionales</p>
                      <div className="space-y-1.5">
                        {selectedContact.emails.slice(1).map((email, idx) => (
                          <p key={idx} className="text-sm text-white break-all">{email}</p>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Phone */}
              {selectedContact.phone && (
                <div className="p-4 bg-dark-800/50 backdrop-blur-sm rounded-xl border border-dark-700">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-lg bg-accent-500/20 flex items-center justify-center border border-accent-500/30 flex-shrink-0">
                      <Phone className="w-5 h-5 text-accent-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-dark-400 uppercase mb-1">Teléfono</p>
                      <p className="text-sm text-white">{selectedContact.phone}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* No info available */}
              {!selectedContact.email && !selectedContact.phone && (
                <div className="text-center py-6">
                  <AlertCircle className="w-12 h-12 text-dark-500 mx-auto mb-3" />
                  <p className="text-dark-400">No hay información de contacto disponible</p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-6 border-t border-dark-800">
              <button
                onClick={closeContactModal}
                className="w-full py-3 bg-gradient-to-r from-secondary-500 to-accent-500 hover:from-secondary-600 hover:to-accent-600 text-white rounded-xl transition-all font-semibold hover:scale-105 active:scale-95 shadow-glow"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  )
}
