import { http, HttpResponse } from 'msw'

const API_BASE_URL = 'http://localhost:8000'

/**
 * MSW handlers for API contract testing
 * These mocks ensure the frontend can handle the expected API responses
 */
export const handlers = [
  // Health check endpoint
  http.get(`${API_BASE_URL}/api/health`, () => {
    return HttpResponse.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: '1.0.0',
    })
  }),

  // Chat endpoint - standard response
  http.post(`${API_BASE_URL}/api/chat`, async ({ request }) => {
    const body = await request.json()
    
    return HttpResponse.json({
      response: 'This is a mock response to: ' + body.message,
      sources: [
        {
          content: 'Mock source content',
          metadata: {
            filename: 'test.txt',
            page: 1,
          },
        },
      ],
      execution_time: 0.5,
    })
  }),

  // Chat streaming endpoint (SSE)
  http.post(`${API_BASE_URL}/api/chat/stream`, async ({ request }) => {
    const body = await request.json()
    
    // Create a text encoder for SSE format
    const encoder = new TextEncoder()
    
    const stream = new ReadableStream({
      start(controller) {
        // Send plan event
        controller.enqueue(
          encoder.encode('event: plan\ndata: {"plan":"Mock plan"}\n\n')
        )
        
        // Send step event
        setTimeout(() => {
          controller.enqueue(
            encoder.encode('event: step\ndata: {"step":"Mock step 1","status":"completed"}\n\n')
          )
        }, 100)
        
        // Send response event
        setTimeout(() => {
          controller.enqueue(
            encoder.encode('event: response\ndata: {"response":"Mock streaming response"}\n\n')
          )
        }, 200)
        
        // Send done event
        setTimeout(() => {
          controller.enqueue(
            encoder.encode('event: done\ndata: {"execution_time":0.3}\n\n')
          )
          controller.close()
        }, 300)
      },
    })
    
    return new HttpResponse(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    })
  }),

  // Upload file
  http.post(`${API_BASE_URL}/api/upload`, async ({ request }) => {
    const formData = await request.formData()
    const file = formData.get('file')
    
    return HttpResponse.json({
      filename: file?.name || 'test.txt',
      status: 'uploaded',
      message: 'File uploaded successfully',
    })
  }),

  // List uploaded files
  http.get(`${API_BASE_URL}/api/upload/list`, () => {
    return HttpResponse.json({
      files: [
        {
          filename: 'test.txt',
          upload_date: '2024-01-01T00:00:00',
          size: 1024,
          status: 'indexed',
        },
        {
          filename: 'document.pdf',
          upload_date: '2024-01-02T00:00:00',
          size: 2048,
          status: 'indexed',
        },
      ],
    })
  }),

  // Get upload status
  http.get(`${API_BASE_URL}/api/upload/status/:filename`, ({ params }) => {
    return HttpResponse.json({
      filename: params.filename,
      status: 'indexed',
      attempts: 1,
      last_attempt: new Date().toISOString(),
    })
  }),

  // Delete file
  http.delete(`${API_BASE_URL}/api/upload/:filename`, ({ params }) => {
    return HttpResponse.json({
      message: `File ${params.filename} deleted successfully`,
    })
  }),

  // Generate document
  http.post(`${API_BASE_URL}/api/generate`, async ({ request }) => {
    const body = await request.json()
    
    return HttpResponse.json({
      filename: 'generated_document.txt',
      content: 'Mock generated content based on: ' + body.prompt,
      format: body.format || 'txt',
    })
  }),

  // Voice transcription
  http.post(`${API_BASE_URL}/api/voice/transcribe`, async ({ request }) => {
    return HttpResponse.json({
      text: 'Mock transcription of audio',
      confidence: 0.95,
    })
  }),

  // RAG query
  http.post(`${API_BASE_URL}/api/rag/query`, async ({ request }) => {
    const body = await request.json()
    
    return HttpResponse.json({
      results: [
        {
          content: 'Mock relevant content',
          metadata: {
            filename: 'test.txt',
            score: 0.85,
          },
        },
      ],
      query: body.query,
    })
  }),

  // Error scenarios for testing
  http.get(`${API_BASE_URL}/api/test/error-500`, () => {
    return new HttpResponse(null, { status: 500 })
  }),

  http.get(`${API_BASE_URL}/api/test/error-429`, () => {
    return new HttpResponse(null, { status: 429 })
  }),

  http.get(`${API_BASE_URL}/api/test/timeout`, () => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(HttpResponse.json({ data: 'delayed' }))
      }, 65000) // Longer than the 60s timeout
    })
  }),
]
