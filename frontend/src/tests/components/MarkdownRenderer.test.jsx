import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MarkdownRenderer from '../../components/MarkdownRenderer'

describe('MarkdownRenderer', () => {
  it('renders plain text', () => {
    render(<MarkdownRenderer content="Hello World" />)
    expect(screen.getByText('Hello World')).toBeInTheDocument()
  })

  it('renders markdown headings', () => {
    const content = '# Heading 1\n## Heading 2'
    render(<MarkdownRenderer content={content} />)
    
    expect(screen.getByText('Heading 1')).toBeInTheDocument()
    expect(screen.getByText('Heading 2')).toBeInTheDocument()
  })

  it('renders markdown lists', () => {
    const content = '- Item 1\n- Item 2\n- Item 3'
    render(<MarkdownRenderer content={content} />)
    
    expect(screen.getByText('Item 1')).toBeInTheDocument()
    expect(screen.getByText('Item 2')).toBeInTheDocument()
    expect(screen.getByText('Item 3')).toBeInTheDocument()
  })

  it('renders inline code', () => {
    const content = 'This is `inline code` example'
    render(<MarkdownRenderer content={content} />)
    
    expect(screen.getByText('inline code')).toBeInTheDocument()
  })

  it('renders links', () => {
    const content = '[Google](https://google.com)'
    render(<MarkdownRenderer content={content} />)
    
    const link = screen.getByRole('link', { name: 'Google' })
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute('href', 'https://google.com')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('renders bold text', () => {
    const content = '**Bold text**'
    render(<MarkdownRenderer content={content} />)
    
    expect(screen.getByText('Bold text')).toBeInTheDocument()
  })

  it('renders italic text', () => {
    const content = '*Italic text*'
    render(<MarkdownRenderer content={content} />)
    
    expect(screen.getByText('Italic text')).toBeInTheDocument()
  })
})
