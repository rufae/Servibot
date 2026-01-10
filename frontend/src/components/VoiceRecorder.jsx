import { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { voiceService } from '../services';

/**
 * VoiceRecorder Component
 * Records audio from microphone, visualizes waveform, and transcribes using Whisper API
 */
export default function VoiceRecorder({ onTranscriptionComplete, disabled = false }) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [permissionStatus, setPermissionStatus] = useState('prompt'); // 'prompt', 'granted', 'denied'
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  const canvasRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyzerRef = useRef(null);
  const animationRef = useRef(null);

  // Check microphone permission on mount
  useEffect(() => {
    checkMicrophonePermission();
    return () => {
      stopVisualization();
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const checkMicrophonePermission = async () => {
    try {
      const result = await navigator.permissions.query({ name: 'microphone' });
      setPermissionStatus(result.state);
      
      result.onchange = () => {
        setPermissionStatus(result.state);
      };
    } catch (err) {
      console.log('Permission API not supported, will request on recording');
    }
  };

  const startRecording = async () => {
    try {
      setError(null);
      setSuccess(false);

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });

      setPermissionStatus('granted');

      // Initialize audio visualization
      initializeVisualization(stream);

      // Setup MediaRecorder
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') 
        ? 'audio/webm' 
        : 'audio/mp4';
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: 128000
      });

      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(track => track.stop());
        stopVisualization();
        await processRecording();
      };

      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);

      // Start timer
      setRecordingTime(0);
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

    } catch (err) {
      console.error('Error starting recording:', err);
      setError('No se pudo acceder al micrófono. Verifica los permisos.');
      setPermissionStatus('denied');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const initializeVisualization = (stream) => {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const analyzer = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(stream);
    
    analyzer.fftSize = 2048;
    source.connect(analyzer);
    
    audioContextRef.current = audioContext;
    analyzerRef.current = analyzer;
    
    drawWaveform();
  };

  const drawWaveform = () => {
    if (!canvasRef.current || !analyzerRef.current) return;
    
    const canvas = canvasRef.current;
    const canvasCtx = canvas.getContext('2d');
    const analyzer = analyzerRef.current;
    
    const bufferLength = analyzer.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    const draw = () => {
      animationRef.current = requestAnimationFrame(draw);
      
      analyzer.getByteTimeDomainData(dataArray);
      
      // Clear canvas with gradient background
      const gradient = canvasCtx.createLinearGradient(0, 0, 0, canvas.height);
      gradient.addColorStop(0, 'rgba(99, 102, 241, 0.1)');
      gradient.addColorStop(1, 'rgba(139, 92, 246, 0.1)');
      canvasCtx.fillStyle = gradient;
      canvasCtx.fillRect(0, 0, canvas.width, canvas.height);
      
      // Draw waveform
      canvasCtx.lineWidth = 2;
      canvasCtx.strokeStyle = 'rgb(139, 92, 246)';
      canvasCtx.beginPath();
      
      const sliceWidth = canvas.width / bufferLength;
      let x = 0;
      
      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = v * canvas.height / 2;
        
        if (i === 0) {
          canvasCtx.moveTo(x, y);
        } else {
          canvasCtx.lineTo(x, y);
        }
        
        x += sliceWidth;
      }
      
      canvasCtx.lineTo(canvas.width, canvas.height / 2);
      canvasCtx.stroke();
    };
    
    draw();
  };

  const stopVisualization = () => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
    
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
  };

  const processRecording = async () => {
    setIsProcessing(true);
    
    try {
      // Create blob from recorded chunks
      const audioBlob = new Blob(audioChunksRef.current, { 
        type: audioChunksRef.current[0]?.type || 'audio/webm' 
      });
      
      // Send to backend for transcription
      const result = await voiceService.transcribe(audioBlob);
      
      if (result.success && result.data.status === 'success') {
        const transcribedText = result.data.text;
        setSuccess(true);
        
        // Clear success state after 2 seconds
        setTimeout(() => setSuccess(false), 2000);
        
        // Callback with transcribed text
        if (onTranscriptionComplete && transcribedText) {
          onTranscriptionComplete(transcribedText);
        }
      } else {
        throw new Error(result.error || 'Transcription failed');
      }
      
    } catch (err) {
      console.error('Error processing recording:', err);
      setError(
        err.message || 
        'Error al transcribir el audio. Intenta de nuevo.'
      );
    } finally {
      setIsProcessing(false);
      audioChunksRef.current = [];
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleRecordClick = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className="voice-recorder">
      {/* Recording Button */}
      <button
        onClick={handleRecordClick}
        disabled={disabled || isProcessing || permissionStatus === 'denied'}
        aria-label={isRecording ? 'Detener grabación' : 'Iniciar grabación'}
        aria-pressed={isRecording}
        className={`
          relative p-3 rounded-full transition-all duration-300
          ${isRecording 
            ? 'bg-red-500 hover:bg-red-600 shadow-lg shadow-red-500/50 animate-pulse' 
            : 'bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 shadow-lg'
          }
          disabled:opacity-50 disabled:cursor-not-allowed
          focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2
        `}
      >
        {isProcessing ? (
          <Loader2 className="w-5 h-5 text-white animate-spin" />
        ) : isRecording ? (
          <MicOff className="w-5 h-5 text-white" />
        ) : (
          <Mic className="w-5 h-5 text-white" />
        )}
        
        {/* Recording indicator ring */}
        {isRecording && (
          <span className="absolute inset-0 rounded-full border-2 border-red-300 animate-ping" />
        )}
      </button>

      {/* Recording Time Display */}
      {isRecording && (
        <div className="mt-2 text-center">
          <span className="text-sm font-mono text-gray-600 dark:text-gray-400">
            🔴 {formatTime(recordingTime)}
          </span>
        </div>
      )}

      {/* Waveform Visualization */}
      {isRecording && (
        <div className="mt-3">
          <canvas
            ref={canvasRef}
            width={300}
            height={60}
            className="w-full rounded-lg border border-purple-200 dark:border-purple-800"
          />
        </div>
      )}

      {/* Processing State */}
      {isProcessing && (
        <div className="mt-3 flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400" role="status" aria-live="polite">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Transcribiendo audio con Whisper...</span>
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="mt-3 flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
          <CheckCircle className="w-4 h-4" />
          <span>¡Transcripción completada!</span>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-3 flex items-start gap-2 text-sm text-red-600 dark:text-red-400">
          <XCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Permission Denied Message */}
      {permissionStatus === 'denied' && (
        <div className="mt-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
          <p className="text-sm text-yellow-800 dark:text-yellow-200">
            <strong>Permisos de micrófono denegados.</strong><br />
            Habilita el acceso al micrófono en la configuración de tu navegador.
          </p>
        </div>
      )}
    </div>
  );
}
