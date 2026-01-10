import { useState, useEffect, useRef } from 'react'
import { X, Trash2, FileText, AlertTriangle, CheckCircle, Clock, RefreshCw, Download } from 'lucide-react'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function FileManager({ isOpen, onClose }) {
  const [files, setFiles] = useState([])
  const [selectedFiles, setSelectedFiles] = useState(new Set())
  const [loading, setLoading] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [confirmAction, setConfirmAction] = useState(null)

  useEffect(() => {
    if (isOpen) {
      loadFiles()
    }
    console.log('FileManager mounted, isOpen=', isOpen)
    return () => {
      console.log('FileManager unmounted')
    }
  }, [isOpen])

  // Mounted guard to avoid state updates after unmount
  const isMounted = useRef(true)
  useEffect(() => {
    isMounted.current = true
    return () => {
      isMounted.current = false
    }
  }, [])

  const loadFiles = async () => {
    if (isMounted.current) setLoading(true)
    try {
      const [filesRes, statusRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/upload/list`),
        // Get status for all files (we'll batch this in a real app)
        Promise.resolve({ data: {} })
      ])

      const filesWithStatus = await Promise.all(
        filesRes.data.files.map(async (file) => {
          try {
            const status = await axios.get(`${API_BASE_URL}/api/upload/status/${file.filename}`)
            return { ...file, indexStatus: status.data }
          } catch {
            return { ...file, indexStatus: { status: 'unknown' } }
          }
        })
      )

      if (isMounted.current) setFiles(filesWithStatus)
    } catch (error) {
      console.error('Error loading files:', error)
    } finally {
      if (isMounted.current) setLoading(false)
    }
  }

  const handleSelectFile = (filename) => {
    setSelectedFiles(prev => {
      const newSet = new Set(prev)
      if (newSet.has(filename)) {
        newSet.delete(filename)
      } else {
        newSet.add(filename)
      }
      return newSet
    })
  }

  const handleSelectAll = () => {
    if (selectedFiles.size === files.length) {
      setSelectedFiles(new Set())
    } else {
      setSelectedFiles(new Set(files.map(f => f.filename)))
    }
  }

  const handleDeleteSelected = async () => {
    if (isMounted.current) setDeleting(true)
    try {
      await Promise.all(
        Array.from(selectedFiles).map(filename =>
          axios.delete(`${API_BASE_URL}/api/upload/file/${encodeURIComponent(filename)}`)
        )
      )
      if (isMounted.current) setSelectedFiles(new Set())
      await loadFiles()
    } catch (error) {
      console.error('Error deleting files:', error)
      alert('Error al eliminar algunos archivos')
    } finally {
      if (isMounted.current) setDeleting(false)
    }
  }

  const handleClearAll = async () => {
    if (isMounted.current) setDeleting(true)
    try {
      await axios.delete(`${API_BASE_URL}/api/upload/clear-all`)
      if (isMounted.current) setSelectedFiles(new Set())
      await loadFiles()
    } catch (error) {
      console.error('Error clearing all files:', error)
      alert('Error al limpiar todos los archivos')
    } finally {
      if (isMounted.current) setDeleting(false)
    }
  }

  const confirmDelete = (action) => {
    setConfirmAction(() => action)
    setShowConfirm(true)
  }

  const getStatusIcon = (status) => {
    // Return icon elements without JSX prop to avoid React warning
    switch (status) {
      case 'indexed':
        return <CheckCircle className="w-4 h-4 text-green-400" />
      case 'error':
        return <AlertTriangle className="w-4 h-4 text-red-400" />
      case 'indexing':
      case 'retrying':
        return <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />
      default:
        return <Clock className="w-4 h-4 text-gray-400" />
    }
  }

  const getStatusText = (status) => {
    switch (status) {
      case 'indexed':
        return 'Indexado'
      case 'error':
        return 'Error'
      case 'indexing':
        return 'Indexando'
      case 'retrying':
        return 'Reintentando'
      default:
        return 'Pendiente'
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1048576).toFixed(1)} MB`
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-fadeIn">
      <div className="bg-gradient-to-br from-gray-800 via-gray-900 to-gray-800 rounded-2xl shadow-2xl border border-gray-700 w-full max-w-4xl max-h-[85vh] flex flex-col overflow-hidden animate-scaleIn">
        {/* Header */}
        <div className="px-6 py-5 border-b border-gray-700 bg-gradient-to-r from-primary-600/20 to-purple-600/20">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                <FileText className="w-7 h-7 text-primary-400" />
                Gestor de Archivos
              </h2>
              <p className="text-sm text-gray-400 mt-1">
                {files.length} archivo{files.length !== 1 ? 's' : ''} en el contexto
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors p-2 hover:bg-white/10 rounded-lg"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Actions Bar */}
        <div className="px-6 py-4 bg-gray-800/50 border-b border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={handleSelectAll}
              className="text-sm text-gray-300 hover:text-white transition-colors px-3 py-1.5 rounded-lg hover:bg-white/5"
            >
              {selectedFiles.size === files.length ? 'Deseleccionar todo' : 'Seleccionar todo'}
            </button>
            {selectedFiles.size > 0 && (
              <span className="text-sm text-primary-400 font-medium">
                {selectedFiles.size} seleccionado{selectedFiles.size !== 1 ? 's' : ''}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadFiles}
              disabled={loading}
              className="text-sm text-gray-300 hover:text-white transition-colors px-3 py-1.5 rounded-lg hover:bg-white/5 flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Actualizar
            </button>
            {selectedFiles.size > 0 && (
              <button
                onClick={() => confirmDelete(handleDeleteSelected)}
                disabled={deleting}
                className="text-sm bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors px-4 py-1.5 rounded-lg flex items-center gap-2 border border-red-500/30"
              >
                <Trash2 className="w-4 h-4" />
                Eliminar seleccionados
              </button>
            )}
            <button
              onClick={() => confirmDelete(handleClearAll)}
              disabled={deleting || files.length === 0}
              className="text-sm bg-red-600/20 text-red-300 hover:bg-red-600/30 transition-colors px-4 py-1.5 rounded-lg flex items-center gap-2 border border-red-600/30 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <AlertTriangle className="w-4 h-4" />
              Limpiar todo
            </button>
          </div>
        </div>

        {/* File List */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <RefreshCw className="w-8 h-8 text-primary-400 animate-spin" />
            </div>
          ) : files.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-gray-400">
              <FileText className="w-16 h-16 mb-4 opacity-50" />
              <p className="text-lg">No hay archivos en el contexto</p>
              <p className="text-sm mt-2">Sube archivos para comenzar</p>
            </div>
          ) : (
            <div className="space-y-2">
              {files.map((file) => (
                <div
                  key={file.filename}
                  className={`group flex items-center gap-4 p-4 rounded-xl border transition-all cursor-pointer ${
                    selectedFiles.has(file.filename)
                      ? 'bg-primary-500/20 border-primary-500/50 shadow-lg shadow-primary-500/10'
                      : 'bg-gray-800/50 border-gray-700 hover:bg-gray-800 hover:border-gray-600'
                  }`}
                  onClick={() => handleSelectFile(file.filename)}
                >
                  {/* Checkbox */}
                  <div className="flex-shrink-0">
                    <input
                      type="checkbox"
                      checked={selectedFiles.has(file.filename)}
                      onChange={() => {}}
                      className="w-5 h-5 rounded border-gray-600 text-primary-500 focus:ring-primary-500 focus:ring-offset-0 cursor-pointer"
                    />
                  </div>

                  {/* File Icon */}
                  <div className="flex-shrink-0">
                    <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary-500/20 to-purple-500/20 flex items-center justify-center border border-primary-500/30">
                      <FileText className="w-6 h-6 text-primary-400" />
                    </div>
                  </div>

                  {/* File Info */}
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-white truncate mb-1">
                      {file.filename}
                    </h3>
                    <div className="flex items-center gap-3 text-xs text-gray-400">
                      <span>{formatFileSize(file.size_bytes)}</span>
                      <span>•</span>
                      <span>{new Date(file.uploaded_at).toLocaleDateString('es-ES')}</span>
                    </div>
                  </div>

                  {/* Status Badge */}
                  <div className="flex-shrink-0">
                    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${
                      file.indexStatus?.status === 'indexed' ? 'bg-green-500/20 text-green-400 border border-green-500/30' :
                      file.indexStatus?.status === 'error' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                      'bg-gray-700 text-gray-300 border border-gray-600'
                    }`}>
                      {getStatusIcon(file.indexStatus?.status)}
                      {getStatusText(file.indexStatus?.status)}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                    <a
                      href={`${API_BASE_URL}/api/upload/file/${encodeURIComponent(file.filename)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="p-2 hover:bg-white/10 rounded-lg transition-colors text-gray-400 hover:text-white"
                      title="Descargar"
                    >
                      <Download className="w-4 h-4" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Confirmation Modal */}
        {showConfirm && (
          <div className="absolute inset-0 bg-black/80 flex items-center justify-center p-6 backdrop-blur-sm">
            <div className="bg-gray-800 rounded-xl border border-red-500/30 p-6 max-w-md w-full shadow-2xl">
              <div className="flex items-start gap-4 mb-4">
                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center">
                  <AlertTriangle className="w-6 h-6 text-red-400" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white mb-2">¿Estás seguro?</h3>
                  <p className="text-sm text-gray-400">
                    {confirmAction === handleClearAll
                      ? 'Esto eliminará TODOS los archivos y limpiará completamente el contexto del sistema. Esta acción no se puede deshacer.'
                      : `Esto eliminará ${selectedFiles.size} archivo${selectedFiles.size !== 1 ? 's' : ''} del sistema. Esta acción no se puede deshacer.`
                    }
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 justify-end">
                <button
                  onClick={() => setShowConfirm(false)}
                  disabled={deleting}
                  className="px-4 py-2 text-sm text-gray-300 hover:text-white transition-colors rounded-lg hover:bg-white/5"
                >
                  Cancelar
                </button>
                <button
                  onClick={async () => {
                    // Close modal immediately to avoid DOM mutation during async ops
                    setShowConfirm(false)
                    if (confirmAction) await confirmAction()
                  }}
                  disabled={deleting}
                  className="px-4 py-2 text-sm bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
                >
                  {deleting ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Eliminando...
                    </>
                  ) : (
                    <>
                      <Trash2 className="w-4 h-4" />
                      Sí, eliminar
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Styles moved to global CSS to avoid runtime style tag issues */}
    </div>
  )
}
