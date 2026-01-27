import { useState, useRef } from 'react'
import { Upload, FileText, Image, Loader2, CheckCircle, XCircle, Scan, RefreshCw } from 'lucide-react'
import { uploadService } from '../services'
import { API_BASE_URL } from '../services/api'

export default function FileUpload() {
  const [isDragging, setIsDragging] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef(null)

  const handleRetry = async (fileName) => {
    // Remove failed file and prompt user to re-upload
    setUploadedFiles(prev => prev.filter(f => f.name !== fileName))
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = async (e) => {
    e.preventDefault()
    setIsDragging(false)
    
    const files = Array.from(e.dataTransfer.files)
    await uploadFiles(files)
  }

  const handleFileSelect = async (e) => {
    const files = Array.from(e.target.files)
    await uploadFiles(files)
  }

  const uploadFiles = async (files) => {
    setIsUploading(true)

    for (const file of files) {
      const fileData = {
        name: file.name,
        size: file.size,
        type: file.type,
        status: 'uploading',
        progress: 0,
      }
      
      setUploadedFiles(prev => [...prev, fileData])

      try {
        // Upload with progress tracking
        const result = await uploadService.uploadFile(file, (progress) => {
          setUploadedFiles(prev => 
            prev.map(f => 
              f.name === file.name 
                ? { ...f, progress }
                : f
            )
          )
        })

        if (!result.success) {
          throw new Error(result.error)
        }

        setUploadedFiles(prev => 
          prev.map(f => 
            f.name === file.name 
              ? { ...f, status: 'success', file_id: result.data.file_id, progress: 100 }
              : f
          )
        )

        // Start polling status for automatic indexing
        const fileId = result.data.file_id
        pollIndexStatus(fileId)
      } catch (error) {
        console.error('Upload error:', error)
        setUploadedFiles(prev => 
          prev.map(f => 
            f.name === file.name 
              ? { ...f, status: 'error', error: error.message }
              : f
          )
        )
      }
    }

    setIsUploading(false)
  }

  const pollIndexStatus = async (fileId) => {
    const pollInterval = 1500
    const maxAttempts = 60 // up to ~90s
    let attempts = 0

    const iv = setInterval(async () => {
      attempts += 1
      try {
        const result = await uploadService.getUploadStatus(fileId)
        
        if (result.success) {
          const status = result.data.status
          const attempts = result.data.attempts || 0
          setUploadedFiles(prev => prev.map(f => f.file_id === fileId ? { ...f, indexing_status: status, attempts } : f))

          if (status === 'indexed' || status === 'error') {
            clearInterval(iv)
            setUploadedFiles(prev => prev.map(f => f.file_id === fileId ? { ...f, status: status === 'indexed' ? 'success' : 'error', attempts } : f))
          }
        }
      } catch (err) {
        // stop polling if not found or other error after many attempts
        if (attempts >= maxAttempts) {
          clearInterval(iv)
        }
      }
    }, pollInterval)
  }

  const getFileIcon = (fileName) => {
    const ext = fileName.split('.').pop().toLowerCase()
    if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) {
      return <Image className="w-5 h-5" />
    }
    return <FileText className="w-5 h-5" />
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="glass-effect rounded-3xl shadow-2xl border border-white/10 p-5 sm:p-6 overflow-hidden backdrop-blur-xl bg-slate-800/40">
      <div className="flex items-center gap-3 mb-6">
        <div className="relative group">
          <div className="absolute inset-0 bg-gradient-to-br from-info-500 to-primary-500 rounded-xl blur-md opacity-60 group-hover:opacity-100 transition-opacity"></div>
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-info-500 via-primary-500 to-secondary-500 flex items-center justify-center shadow-glow-strong">
            <Upload className="w-5 h-5 text-white" />
          </div>
        </div>
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-white">Subir Documentos</h2>
          <p className="text-xs text-dark-400">Arrastra archivos o haz clic para seleccionar</p>
        </div>
      </div>
      
      {/* Drop Zone - collapsed by default; expands on hover or when dragging */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        role="button"
        tabIndex={0}
        aria-label="Área para arrastrar y soltar archivos o hacer clic para seleccionar"
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            fileInputRef.current?.click()
          }
        }}
        className={`relative group border-2 border-dashed rounded-2xl text-center cursor-pointer transition-all duration-300 backdrop-blur-sm overflow-hidden p-3 sm:p-4 group-hover:p-8 group-hover:sm:p-10 ${
          isDragging
            ? 'border-primary-400 bg-gradient-to-br from-primary-500/20 to-secondary-500/20 scale-[1.02] shadow-glow'
            : 'border-dark-700 hover:border-dark-600 hover:bg-dark-900/50'
        }`}
      >
        <div className={`transition-all duration-300 ${isDragging ? 'scale-110' : 'scale-100'}`}>
          <div className={`w-10 h-10 sm:w-12 sm:h-12 mx-auto mb-2 rounded-2xl flex items-center justify-center ${
            isDragging 
              ? 'bg-gradient-to-br from-primary-500 to-secondary-500 shadow-glow' 
              : 'bg-transparent'
          }`}>
            <Upload className={`w-5 h-5 sm:w-6 sm:h-6 ${isDragging ? 'text-white animate-bounce' : 'text-dark-400'}`} />
          </div>
          <p className={`text-white mb-2 font-medium text-sm sm:text-base transition-all duration-300 overflow-hidden ${isDragging ? 'opacity-100 max-h-40' : 'opacity-0 max-h-0 group-hover:opacity-100 group-hover:max-h-40'}`}>
            {isDragging ? '¡Suelta aquí!' : 'Arrastra archivos o haz clic'}
          </p>
          <p className={`text-xs sm:text-sm text-dark-500 transition-all duration-300 overflow-hidden ${isDragging ? 'opacity-100 max-h-40' : 'opacity-0 max-h-0 group-hover:opacity-100 group-hover:max-h-40'}`}>
            Formatos: PDF, imágenes (PNG, JPG), archivos de texto
          </p>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.png,.jpg,.jpeg,.txt,.md"
          onChange={handleFileSelect}
          aria-label="Seleccionar archivos para subir"
          className="hidden"
        />
      </div>

      {/* Uploaded Files List */}
      {uploadedFiles.length > 0 && (
        <div className="mt-6 space-y-3">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-dark-300 uppercase flex items-center gap-2">
              <span className="w-1 h-1 rounded-full bg-primary-400"></span>
              Archivos subidos ({uploadedFiles.length})
            </h3>
          </div>
          <div className="space-y-2 max-h-64 overflow-y-auto custom-scrollbar">
            {uploadedFiles.map((file, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between glass-effect rounded-xl p-3 sm:p-4 border border-dark-800 hover:border-dark-700 transition-all group backdrop-blur-sm"
              >
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                  <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-lg bg-gradient-to-br from-info-500/20 to-primary-500/20 flex items-center justify-center flex-shrink-0 border border-info-500/30">
                    {getFileIcon(file.name)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium truncate text-white group-hover:text-primary-300 transition-colors">{file.name}</p>
                      {file.ocr_used && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-info-500/20 text-info-300 text-[10px] rounded border border-info-500/30 whitespace-nowrap">
                          <Scan className="w-3 h-3" />
                          <span className="hidden sm:inline">OCR</span>
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-dark-500">
                      <span>{formatFileSize(file.size)}</span>
                      {file.status === 'error' && file.error && (
                        <span className="text-danger-400 truncate">{file.error}</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 sm:gap-3 ml-2 sm:ml-3 flex-shrink-0">
                  <div className="flex-shrink-0">
                    {file.status === 'uploading' && (
                      <div className="flex items-center gap-2 text-info-400">
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span className="text-xs hidden sm:inline">{file.progress || 0}%</span>
                      </div>
                    )}
                    {file.status === 'success' && (
                      <CheckCircle className="w-5 h-5 text-success-400" />
                    )}
                    {file.status === 'error' && (
                      <div className="flex items-center gap-2">
                        <XCircle className="w-5 h-5 text-danger-400" />
                        <button
                          onClick={() => handleRetry(file.name)}
                          className="p-1.5 sm:p-2 bg-danger-500/10 hover:bg-danger-500/20 border border-danger-500/30 rounded-lg transition-all hover:scale-105 active:scale-95"
                          title="Reintentar subida"
                        >
                          <RefreshCw className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-danger-400" />
                        </button>
                      </div>
                    )}
                  </div>
                  <div className="flex-shrink-0">
                    {file.file_id && (
                      <IndexButton
                        file={file}
                        onUpdate={(updated) => setUploadedFiles(prev => prev.map(p => (p.file_id === updated.file_id ? updated : p)))}
                      />
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Additional indexing UI behavior: index uploaded file into RAG
// We'll export an IndexButton component to keep the UI tidy.
export function IndexButton({ file, onUpdate }) {
  const [indexing, setIndexing] = useState(false)
  const [indexed, setIndexed] = useState(file.indexed || false)
  const [error, setError] = useState(null)

  const indexFile = async () => {
    setIndexing(true)
    setError(null)
    try {
      const result = await uploadService.reindexFile(file.file_id || file.name)
      
      if (result.success) {
        onUpdate && onUpdate({ ...file, indexing_status: 'indexing', index_info: result.data })
      } else {
        throw new Error(result.error)
      }
    } catch (err) {
      console.error('Indexing error', err)
      setError(err?.message || 'Indexing failed')
      onUpdate && onUpdate({ ...file, indexed: false, index_error: err?.message })
    } finally {
      setIndexing(false)
    }
  }

  return (
    <div className="flex items-center space-x-2">
      {file.indexing_status === 'indexed' ? (
        <div className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 bg-success-500/20 rounded-lg border border-success-500/30">
          <CheckCircle className="w-3.5 h-3.5 text-success-400" />
          <span className="text-xs text-success-400 font-medium hidden sm:inline">Indexado</span>
        </div>
      ) : file.indexing_status === 'indexing' || file.indexing_status === 'retrying' ? (
        <div className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 bg-info-500/20 rounded-lg border border-info-500/30">
          <Loader2 className="w-3.5 h-3.5 text-info-400 animate-spin" />
          <span className="text-xs text-info-400 font-medium hidden sm:inline">Indexando...</span>
        </div>
      ) : (
        <button
          onClick={indexFile}
          disabled={indexing}
          className="px-2.5 sm:px-3 py-1.5 bg-gradient-to-r from-info-500 to-primary-500 hover:from-info-600 hover:to-primary-600 text-white rounded-lg text-xs font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-glow hover:shadow-glow-lg transform hover:scale-105 active:scale-95"
        >
          {indexing ? 'Indexando...' : 'Reindexar'}
        </button>
      )}
      {file.indexing_status === 'error' && (
        <div className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 bg-danger-500/20 rounded-lg border border-danger-500/30">
          <XCircle className="w-3.5 h-3.5 text-danger-400" />
          <span className="text-xs text-danger-400 font-medium hidden sm:inline">Error · {file.attempts || 0} intentos</span>
        </div>
      )}
      {error && (
        <div className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 bg-danger-500/20 rounded-lg border border-danger-500/30">
          <span className="text-xs text-danger-400 font-medium">Error</span>
        </div>
      )}
    </div>
  )
}
