import { useState, useRef } from 'react'
import { Upload, FileText, Image, Loader2, CheckCircle, XCircle } from 'lucide-react'
import { uploadService } from '../services'
import { API_BASE_URL } from '../services/api'

export default function FileUpload() {
  const [isDragging, setIsDragging] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef(null)

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
    <div className="bg-gradient-to-br from-gray-800 via-gray-900 to-gray-800 rounded-2xl shadow-2xl border border-gray-700 p-6 overflow-hidden">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
          <Upload className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Subir Documentos</h2>
          <p className="text-xs text-gray-400">Arrastra archivos o haz clic para seleccionar</p>
        </div>
      </div>
      
      {/* Drop Zone */}
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
        className={`relative border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all duration-300 ${
          isDragging
            ? 'border-primary-500 bg-gradient-to-br from-primary-500/20 to-purple-500/20 scale-[1.02]'
            : 'border-gray-600 hover:border-gray-500 hover:bg-gray-800/50'
        }`}
      >
        <div className={`transition-all duration-300 ${isDragging ? 'scale-110' : 'scale-100'}`}>
          <div className={`w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center ${
            isDragging 
              ? 'bg-gradient-to-br from-primary-500 to-purple-500' 
              : 'bg-gradient-to-br from-gray-700 to-gray-800'
          }`}>
            <Upload className={`w-8 h-8 ${isDragging ? 'text-white animate-bounce' : 'text-gray-400'}`} />
          </div>
          <p className="text-gray-200 mb-2 font-medium">
            {isDragging ? '¡Suelta aquí!' : 'Arrastra archivos o haz clic'}
          </p>
          <p className="text-sm text-gray-500">
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
            <h3 className="text-sm font-semibold text-gray-300 uppercase flex items-center gap-2">
              <span className="w-1 h-1 rounded-full bg-primary-400"></span>
              Archivos subidos ({uploadedFiles.length})
            </h3>
          </div>
          <div className="space-y-2 max-h-64 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
            {uploadedFiles.map((file, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between bg-gradient-to-r from-gray-800 to-gray-900 rounded-xl p-4 border border-gray-700 hover:border-gray-600 transition-all group"
              >
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500/20 to-cyan-500/20 flex items-center justify-center flex-shrink-0 border border-blue-500/30">
                    {getFileIcon(file.name)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate text-white group-hover:text-primary-300 transition-colors">{file.name}</p>
                    <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 ml-3">
                  <div className="flex-shrink-0">
                    {file.status === 'uploading' && (
                      <div className="flex items-center gap-2 text-blue-400">
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span className="text-xs">{file.progress || 0}%</span>
                      </div>
                    )}
                    {file.status === 'success' && (
                      <CheckCircle className="w-5 h-5 text-green-400" />
                    )}
                    {file.status === 'error' && (
                      <XCircle className="w-5 h-5 text-red-400" />
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
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-green-500/20 rounded-lg border border-green-500/30">
          <CheckCircle className="w-3.5 h-3.5 text-green-400" />
          <span className="text-xs text-green-400 font-medium">Indexado</span>
        </div>
      ) : file.indexing_status === 'indexing' || file.indexing_status === 'retrying' ? (
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-500/20 rounded-lg border border-blue-500/30">
          <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin" />
          <span className="text-xs text-blue-400 font-medium">Indexando...</span>
        </div>
      ) : (
        <button
          onClick={indexFile}
          disabled={indexing}
          className="px-3 py-1.5 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white rounded-lg text-xs font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-blue-500/30 transform hover:scale-105"
        >
          {indexing ? 'Indexando...' : 'Reindexar'}
        </button>
      )}
      {file.indexing_status === 'error' && (
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/20 rounded-lg border border-red-500/30">
          <XCircle className="w-3.5 h-3.5 text-red-400" />
          <span className="text-xs text-red-400 font-medium">Error · {file.attempts || 0} intentos</span>
        </div>
      )}
      {error && (
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/20 rounded-lg border border-red-500/30">
          <span className="text-xs text-red-400 font-medium">Error</span>
        </div>
      )}
    </div>
  )
}
