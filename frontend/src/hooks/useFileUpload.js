import { useState } from 'react'
import { uploadService } from '../services'

/**
 * Custom hook for managing file uploads
 */
export function useFileUpload() {
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [isUploading, setIsUploading] = useState(false)

  const uploadFile = async (file) => {
    setIsUploading(true)

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
      pollIndexStatus(result.data.file_id)

      return { success: true, fileId: result.data.file_id }
    } catch (error) {
      console.error('Upload error:', error)
      setUploadedFiles(prev => 
        prev.map(f => 
          f.name === file.name 
            ? { ...f, status: 'error', error: error.message }
            : f
        )
      )
      return { success: false, error: error.message }
    } finally {
      setIsUploading(false)
    }
  }

  const uploadMultipleFiles = async (files) => {
    const results = []
    for (const file of files) {
      const result = await uploadFile(file)
      results.push(result)
    }
    return results
  }

  const pollIndexStatus = async (fileId) => {
    const pollInterval = 1500
    const maxAttempts = 60
    let attempts = 0

    const iv = setInterval(async () => {
      attempts += 1
      try {
        const result = await uploadService.getUploadStatus(fileId)
        
        if (result.success) {
          const status = result.data.status
          const attempts = result.data.attempts || 0
          
          setUploadedFiles(prev => 
            prev.map(f => 
              f.file_id === fileId 
                ? { ...f, indexing_status: status, attempts } 
                : f
            )
          )

          if (status === 'indexed' || status === 'error') {
            clearInterval(iv)
            setUploadedFiles(prev => 
              prev.map(f => 
                f.file_id === fileId 
                  ? { ...f, status: status === 'indexed' ? 'success' : 'error', attempts } 
                  : f
              )
            )
          }
        }
      } catch (err) {
        if (attempts >= maxAttempts) {
          clearInterval(iv)
        }
      }
    }, pollInterval)
  }

  const reindexFile = async (fileId) => {
    try {
      const result = await uploadService.reindexFile(fileId)
      
      if (result.success) {
        setUploadedFiles(prev => 
          prev.map(f => 
            f.file_id === fileId 
              ? { ...f, indexing_status: 'indexing', index_info: result.data } 
              : f
          )
        )
        return { success: true }
      }
      
      return { success: false, error: result.error }
    } catch (error) {
      console.error('Reindex error:', error)
      return { success: false, error: error.message }
    }
  }

  return {
    uploadedFiles,
    setUploadedFiles,
    isUploading,
    uploadFile,
    uploadMultipleFiles,
    reindexFile,
  }
}
