import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeSanitize from 'rehype-sanitize'

/**
 * Markdown renderer component with sanitization
 * Used for rendering assistant messages with proper formatting
 */
export default function MarkdownRenderer({ content, className = '' }) {
  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
        components={{
        // Custom component renderers
        p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
        a: ({ node, ...props }) => (
          <a
            className="text-blue-400 hover:text-blue-300 underline"
            target="_blank"
            rel="noopener noreferrer"
            {...props}
          />
        ),
        code: ({ node, inline, ...props }) =>
          inline ? (
            <code className="bg-gray-800/50 px-1.5 py-0.5 rounded text-sm font-mono" {...props} />
          ) : (
            <code className="block bg-gray-800/50 p-3 rounded-lg text-sm font-mono overflow-x-auto" {...props} />
          ),
        pre: ({ node, ...props }) => (
          <pre className="bg-gray-800/50 p-3 rounded-lg overflow-x-auto mb-2" {...props} />
        ),
        ul: ({ node, ...props }) => (
          <ul className="list-disc list-inside mb-2 space-y-1" {...props} />
        ),
        ol: ({ node, ...props }) => (
          <ol className="list-decimal list-inside mb-2 space-y-1" {...props} />
        ),
        li: ({ node, ...props }) => <li className="ml-2" {...props} />,
        h1: ({ node, ...props }) => <h1 className="text-2xl font-bold mb-2" {...props} />,
        h2: ({ node, ...props }) => <h2 className="text-xl font-bold mb-2" {...props} />,
        h3: ({ node, ...props }) => <h3 className="text-lg font-bold mb-2" {...props} />,
        blockquote: ({ node, ...props }) => (
          <blockquote className="border-l-4 border-gray-600 pl-4 italic my-2" {...props} />
        ),
        table: ({ node, ...props }) => (
          <div className="overflow-x-auto mb-2">
            <table className="min-w-full border border-gray-700" {...props} />
          </div>
        ),
        th: ({ node, ...props }) => (
          <th className="border border-gray-700 px-3 py-2 bg-gray-800" {...props} />
        ),
        td: ({ node, ...props }) => (
          <td className="border border-gray-700 px-3 py-2" {...props} />
        ),
      }}
    >
      {content}
    </ReactMarkdown>
    </div>
  )
}
