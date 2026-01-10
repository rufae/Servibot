import { describe, it, expect } from 'vitest'
import { apiClient } from '../services/api'

describe('API Contract Tests with MSW', () => {
  describe('Health Endpoint', () => {
    it('should return healthy status', async () => {
      const response = await apiClient.get('/api/health')
      
      expect(response.status).toBe(200)
      expect(response.data).toHaveProperty('status', 'healthy')
      expect(response.data).toHaveProperty('timestamp')
      expect(response.data).toHaveProperty('version')
    })
  })

  describe('Chat Endpoint', () => {
    it('should return response with sources', async () => {
      const response = await apiClient.post('/api/chat', {
        message: 'test query',
      })
      
      expect(response.status).toBe(200)
      expect(response.data).toHaveProperty('response')
      expect(response.data).toHaveProperty('sources')
      expect(Array.isArray(response.data.sources)).toBe(true)
      expect(response.data).toHaveProperty('execution_time')
    })

    it('should handle sources with metadata', async () => {
      const response = await apiClient.post('/api/chat', {
        message: 'test query',
      })
      
      const source = response.data.sources[0]
      expect(source).toHaveProperty('content')
      expect(source).toHaveProperty('metadata')
      expect(source.metadata).toHaveProperty('filename')
    })
  })

  describe('Upload Endpoints', () => {
    it('should upload file successfully', async () => {
      const formData = new FormData()
      const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
      formData.append('file', file)
      
      const response = await apiClient.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      
      expect(response.status).toBe(200)
      expect(response.data).toHaveProperty('filename')
      expect(response.data).toHaveProperty('status', 'uploaded')
    })

    it('should list uploaded files', async () => {
      const response = await apiClient.get('/api/upload/list')
      
      expect(response.status).toBe(200)
      expect(response.data).toHaveProperty('files')
      expect(Array.isArray(response.data.files)).toBe(true)
      
      if (response.data.files.length > 0) {
        const file = response.data.files[0]
        expect(file).toHaveProperty('filename')
        expect(file).toHaveProperty('upload_date')
        expect(file).toHaveProperty('status')
      }
    })

    it('should get file status', async () => {
      const response = await apiClient.get('/api/upload/status/test.txt')
      
      expect(response.status).toBe(200)
      expect(response.data).toHaveProperty('filename', 'test.txt')
      expect(response.data).toHaveProperty('status')
      expect(response.data).toHaveProperty('attempts')
    })

    it('should delete file', async () => {
      const response = await apiClient.delete('/api/upload/test.txt')
      
      expect(response.status).toBe(200)
      expect(response.data).toHaveProperty('message')
    })
  })

  describe('Generate Endpoint', () => {
    it('should generate document', async () => {
      const response = await apiClient.post('/api/generate', {
        prompt: 'test prompt',
        format: 'txt',
      })
      
      expect(response.status).toBe(200)
      expect(response.data).toHaveProperty('filename')
      expect(response.data).toHaveProperty('content')
      expect(response.data).toHaveProperty('format')
    })
  })

  describe('Voice Endpoint', () => {
    it('should transcribe audio', async () => {
      const formData = new FormData()
      const audioBlob = new Blob(['fake audio'], { type: 'audio/wav' })
      formData.append('audio', audioBlob, 'test.wav')
      
      const response = await apiClient.post('/api/voice/transcribe', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      
      expect(response.status).toBe(200)
      expect(response.data).toHaveProperty('text')
      expect(response.data).toHaveProperty('confidence')
    })
  })

  describe('RAG Endpoint', () => {
    it('should query knowledge base', async () => {
      const response = await apiClient.post('/api/rag/query', {
        query: 'test query',
      })
      
      expect(response.status).toBe(200)
      expect(response.data).toHaveProperty('results')
      expect(Array.isArray(response.data.results)).toBe(true)
      expect(response.data).toHaveProperty('query')
      
      if (response.data.results.length > 0) {
        const result = response.data.results[0]
        expect(result).toHaveProperty('content')
        expect(result).toHaveProperty('metadata')
      }
    })
  })

  describe('Error Handling', () => {
    it('should handle 500 errors', { timeout: 10000 }, async () => {
      try {
        await apiClient.get('/api/test/error-500')
        expect.fail('Should have thrown error')
      } catch (error) {
        expect(error).toHaveProperty('status', 500)
      }
    })

    it('should handle 429 rate limiting', { timeout: 10000 }, async () => {
      try {
        await apiClient.get('/api/test/error-429')
        expect.fail('Should have thrown error')
      } catch (error) {
        expect(error).toHaveProperty('status', 429)
      }
    })
  })
})
