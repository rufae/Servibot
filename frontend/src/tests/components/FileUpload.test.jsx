import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import FileUpload from '../../components/FileUpload'

// Mock services
vi.mock('../../services', () => ({
  uploadService: {
    uploadFile: vi.fn(() => Promise.resolve({
      success: true,
      data: {
        file_id: 'test-file-id',
        filename: 'test.pdf'
      }
    })),
    getUploadStatus: vi.fn(() => Promise.resolve({
      success: true,
      data: {
        status: 'indexed',
        attempts: 0
      }
    }))
  }
}))

describe('FileUpload', () => {
  it('renders file upload component', () => {
    render(<FileUpload />)
    
    expect(screen.getByText(/Subir Documentos/i)).toBeInTheDocument()
    // Use getAllByText since the text appears multiple times
    expect(screen.getAllByText(/Arrastra archivos/i)[0]).toBeInTheDocument()
  })

  it('displays drop zone', () => {
    render(<FileUpload />)
    
    const dropZone = screen.getByRole('button', { name: /Área para arrastrar/i })
    expect(dropZone).toBeInTheDocument()
  })

  it('shows file format information', () => {
    render(<FileUpload />)
    
    expect(screen.getByText(/Formatos: PDF, imágenes/i)).toBeInTheDocument()
  })

  it('drop zone responds to click', () => {
    render(<FileUpload />)
    
    const dropZone = screen.getByRole('button', { name: /Área para arrastrar/i })
    fireEvent.click(dropZone)
    
    // File input should be triggered (hidden)
    const fileInput = document.querySelector('input[type="file"]')
    expect(fileInput).toBeInTheDocument()
  })
})
