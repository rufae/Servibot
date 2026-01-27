import { useState } from 'react';
import { FileText, Table, Download, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

/**
 * FileGenerator Component
 * Generates PDF and Excel files from chat conversation data
 */
export default function FileGenerator({ messages, currentConversation = null }) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationType, setGenerationType] = useState(null); // 'pdf' or 'excel'
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);

  const generatePDF = async () => {
    setIsGenerating(true);
    setGenerationType('pdf');
    setError(null);
    setSuccess(null);

    try {
      // Prepare content from messages
      const title = currentConversation?.title || `Conversación ServiBot - ${new Date().toLocaleDateString('es-ES')}`;
      
      let content = `Conversación generada el ${new Date().toLocaleString('es-ES')}\n\n`;
      content += `Total de mensajes: ${messages.length}\n\n`;
      content += '─'.repeat(80) + '\n\n';

      messages.forEach((msg, index) => {
        const role = msg.role === 'user' ? '👤 Usuario' : '🤖 ServiBot';
        const timestamp = msg.timestamp 
          ? new Date(msg.timestamp).toLocaleTimeString('es-ES') 
          : '';
        
        content += `${role}${timestamp ? ` - ${timestamp}` : ''}\n`;
        content += `${msg.content}\n`;
        
        // Add sources if available
        if (msg.sources && msg.sources.length > 0) {
          content += `\n📎 Fuentes: ${msg.sources.join(', ')}\n`;
        }
        
        // Add execution timeline if available
        if (msg.execution_timeline && msg.execution_timeline.length > 0) {
          content += `\n⚙️ Ejecución del agente:\n`;
          msg.execution_timeline.forEach((step, i) => {
            content += `  ${i + 1}. ${step.action} - ${step.status}\n`;
          });
        }
        
        content += '\n' + '─'.repeat(80) + '\n\n';
      });

      // Add metadata
      const metadata = {
        'Generado por': 'ServiBot',
        'Fecha': new Date().toLocaleDateString('es-ES'),
        'Hora': new Date().toLocaleTimeString('es-ES'),
        'Total mensajes': messages.length.toString()
      };

      // Send request to backend
      const response = await axios.post(`${API_URL}/api/generate/pdf`, {
        title,
        content,
        filename: `conversacion_${Date.now()}.pdf`,
        metadata
      });

      if (response.data.status === 'success') {
        setSuccess({
          type: 'pdf',
          filename: response.data.filename,
          downloadUrl: `${API_URL}${response.data.file_url}`
        });

        // Auto-download
        const link = document.createElement('a');
        link.href = `${API_URL}${response.data.file_url}`;
        link.download = response.data.filename;
        document.body.appendChild(link);
        link.click();
        if (link.parentNode) {
          document.body.removeChild(link);
        }

        // Clear success message after 5 seconds
        setTimeout(() => setSuccess(null), 5000);
      }

    } catch (err) {
      console.error('Error generating PDF:', err);
      setError(err.response?.data?.detail || 'Error al generar el PDF');
    } finally {
      setIsGenerating(false);
      setGenerationType(null);
    }
  };

  const generateExcel = async () => {
    setIsGenerating(true);
    setGenerationType('excel');
    setError(null);
    setSuccess(null);

    try {
      // Prepare Excel data with multiple sheets
      const sheets = {
        'Conversación': [
          ['#', 'Rol', 'Mensaje', 'Timestamp', 'Fuentes'],
          ...messages.map((msg, index) => [
            index + 1,
            msg.role === 'user' ? 'Usuario' : 'ServiBot',
            msg.content,
            msg.timestamp ? new Date(msg.timestamp).toLocaleString('es-ES') : '',
            msg.sources ? msg.sources.join(', ') : ''
          ])
        ],
        'Estadísticas': [
          ['Métrica', 'Valor'],
          ['Total de mensajes', messages.length],
          ['Mensajes de usuario', messages.filter(m => m.role === 'user').length],
          ['Respuestas de ServiBot', messages.filter(m => m.role === 'assistant').length],
          ['Mensajes con fuentes', messages.filter(m => m.sources && m.sources.length > 0).length],
          ['Fecha de generación', new Date().toLocaleString('es-ES')]
        ]
      };

      // Add agent execution sheet if available
      const messagesWithExecution = messages.filter(m => m.execution_timeline && m.execution_timeline.length > 0);
      if (messagesWithExecution.length > 0) {
        sheets['Ejecuciones Agente'] = [
          ['Mensaje #', 'Paso', 'Acción', 'Estado', 'Tiempo (s)'],
          ...messagesWithExecution.flatMap((msg, msgIndex) =>
            msg.execution_timeline.map((step, stepIndex) => [
              msgIndex + 1,
              stepIndex + 1,
              step.action || step.tool || 'N/A',
              step.status,
              step.execution_time?.toFixed(2) || 'N/A'
            ])
          )
        ];
      }

      const headers = {
        'Conversación': ['#', 'Rol', 'Mensaje', 'Timestamp', 'Fuentes'],
        'Estadísticas': ['Métrica', 'Valor'],
        ...(messagesWithExecution.length > 0 && {
          'Ejecuciones Agente': ['Mensaje #', 'Paso', 'Acción', 'Estado', 'Tiempo (s)']
        })
      };

      // Send request to backend
      const response = await axios.post(`${API_URL}/api/generate/excel`, {
        filename: `conversacion_${Date.now()}.xlsx`,
        sheets,
        headers
      });

      if (response.data.status === 'success') {
        setSuccess({
          type: 'excel',
          filename: response.data.filename,
          downloadUrl: `${API_URL}${response.data.file_url}`
        });

        // Auto-download
        const link = document.createElement('a');
        link.href = `${API_URL}${response.data.file_url}`;
        link.download = response.data.filename;
        document.body.appendChild(link);
        link.click();
        if (link.parentNode) {
          document.body.removeChild(link);
        }

        // Clear success message after 5 seconds
        setTimeout(() => setSuccess(null), 5000);
      }

    } catch (err) {
      console.error('Error generating Excel:', err);
      setError(err.response?.data?.detail || 'Error al generar el Excel');
    } finally {
      setIsGenerating(false);
      setGenerationType(null);
    }
  };

  const canGenerate = messages && messages.length > 0;

  return (
    <div className="file-generator">
      {/* Generation Buttons */}
      <div className="flex gap-2">
        {/* PDF Button */}
        <button
          onClick={generatePDF}
          disabled={!canGenerate || isGenerating}
          className={`
            flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all
            ${canGenerate && !isGenerating
              ? 'bg-gradient-to-r from-primary-500 to-secondary-600 hover:from-primary-600 hover:to-secondary-700 text-white shadow-lg hover:shadow-xl'
              : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-500 cursor-not-allowed'
            }
            disabled:opacity-50
          `}
          title="Exportar conversación como PDF"
        >
          {isGenerating && generationType === 'pdf' ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <FileText className="w-4 h-4" />
          )}
          <span className="text-sm">Exportar PDF</span>
        </button>

        {/* Excel Button */}
        <button
          onClick={generateExcel}
          disabled={!canGenerate || isGenerating}
          className={`
            flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all
            ${canGenerate && !isGenerating
              ? 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white shadow-lg hover:shadow-xl'
              : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-500 cursor-not-allowed'
            }
            disabled:opacity-50
          `}
          title="Exportar conversación como Excel"
        >
          {isGenerating && generationType === 'excel' ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Table className="w-4 h-4" />
          )}
          <span className="text-sm">Exportar Excel</span>
        </button>
      </div>

      {/* Status Messages */}
      {success && (
        <div className="mt-3 flex items-start gap-2 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
          <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-green-800 dark:text-green-200 font-medium">
              ¡{success.type === 'pdf' ? 'PDF' : 'Excel'} generado exitosamente!
            </p>
            <p className="text-xs text-green-700 dark:text-green-300 mt-1">
              {success.filename}
            </p>
            <a
              href={success.downloadUrl}
              download={success.filename}
              className="inline-flex items-center gap-1 mt-2 text-xs text-green-700 dark:text-green-300 hover:text-green-900 dark:hover:text-green-100 underline"
            >
              <Download className="w-3 h-3" />
              Descargar nuevamente
            </a>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-3 flex items-start gap-2 p-3 bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 rounded-lg">
          <AlertCircle className="w-5 h-5 text-danger-600 dark:text-danger-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-danger-800 dark:text-danger-200 font-medium">
              Error al generar archivo
            </p>
            <p className="text-xs text-danger-700 dark:text-danger-300 mt-1">
              {error}
            </p>
          </div>
        </div>
      )}

      {/* Info Message when no messages */}
      {!canGenerate && (
        <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <p className="text-sm text-blue-800 dark:text-blue-200">
            💬 Inicia una conversación para poder exportar como PDF o Excel
          </p>
        </div>
      )}

      {/* Feature Description */}
      {canGenerate && !isGenerating && !success && (
        <div className="mt-3 text-xs text-gray-600 dark:text-gray-400">
          <p>
            <strong>PDF:</strong> Documento formateado con toda la conversación y metadatos
          </p>
          <p className="mt-1">
            <strong>Excel:</strong> Hojas con conversación, estadísticas y ejecuciones del agente
          </p>
        </div>
      )}
    </div>
  );
}
