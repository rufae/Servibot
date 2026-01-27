import { useState, useRef, useEffect } from 'react';
import { Play, Pause, Volume2, VolumeX, Download, Loader2, RotateCcw } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

/**
 * AudioPlayer Component
 * Plays audio files from TTS synthesis with controls and visualization
 */
export default function AudioPlayer({ audioUrl, autoPlay = false, onEnded = null }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [error, setError] = useState(null);
  const [playbackRate, setPlaybackRate] = useState(1);
  
  const audioRef = useRef(null);
  const progressBarRef = useRef(null);
  const canvasRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyzerRef = useRef(null);
  const sourceRef = useRef(null);
  const animationRef = useRef(null);

  // Construct full audio URL
  const fullAudioUrl = audioUrl?.startsWith('http') 
    ? audioUrl 
    : `${API_URL}${audioUrl}`;

  useEffect(() => {
    console.log('[AudioPlayer] audioUrl received:', audioUrl);
    console.log('[AudioPlayer] fullAudioUrl constructed:', fullAudioUrl);
    
    if (audioUrl && audioRef.current) {
      console.log('[AudioPlayer] Loading audio...');
      audioRef.current.load();
      
      if (autoPlay) {
        console.log('[AudioPlayer] Autoplay enabled, starting playback');
        playAudio();
      }
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
      }
    };
  }, [audioUrl, autoPlay]);

  const playAudio = async () => {
    if (!audioRef.current) return;
    
    try {
      setIsLoading(true);
      setError(null);
      
      await audioRef.current.play();
      setIsPlaying(true);
      
      // Initialize visualization
      if (!audioContextRef.current) {
        initializeVisualization();
      }
      
    } catch (err) {
      console.error('Error playing audio:', err);
      setError('Error al reproducir el audio');
      setIsPlaying(false);
    } finally {
      setIsLoading(false);
    }
  };

  const pauseAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  };

  const togglePlayPause = () => {
    if (isPlaying) {
      pauseAudio();
    } else {
      playAudio();
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };

  const handleEnded = () => {
    setIsPlaying(false);
    setCurrentTime(0);
    
    if (onEnded) {
      onEnded();
    }
  };

  const handleProgressClick = (e) => {
    if (!progressBarRef.current || !audioRef.current) return;
    
    const bounds = progressBarRef.current.getBoundingClientRect();
    const x = e.clientX - bounds.left;
    const percentage = x / bounds.width;
    const newTime = percentage * duration;
    
    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const handleVolumeChange = (e) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    
    if (audioRef.current) {
      audioRef.current.volume = newVolume;
    }
    
    setIsMuted(newVolume === 0);
  };

  const toggleMute = () => {
    if (audioRef.current) {
      if (isMuted) {
        audioRef.current.volume = volume;
        setIsMuted(false);
      } else {
        audioRef.current.volume = 0;
        setIsMuted(true);
      }
    }
  };

  const handlePlaybackRateChange = (rate) => {
    setPlaybackRate(rate);
    if (audioRef.current) {
      audioRef.current.playbackRate = rate;
    }
  };

  const resetAudio = () => {
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
      setCurrentTime(0);
      pauseAudio();
    }
  };

  const downloadAudio = () => {
    const link = document.createElement('a');
    link.href = fullAudioUrl;
    link.download = audioUrl?.split('/').pop() || 'audio.mp3';
    document.body.appendChild(link);
    link.click();
    if (link.parentNode) {
      document.body.removeChild(link);
    }
  };

  const initializeVisualization = () => {
    if (!audioRef.current || !canvasRef.current) return;
    
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const analyzer = audioContext.createAnalyser();
      const source = audioContext.createMediaElementSource(audioRef.current);
      
      analyzer.fftSize = 256;
      source.connect(analyzer);
      analyzer.connect(audioContext.destination);
      
      audioContextRef.current = audioContext;
      analyzerRef.current = analyzer;
      sourceRef.current = source;
      
      drawVisualization();
    } catch (err) {
      console.error('Error initializing visualization:', err);
    }
  };

  const drawVisualization = () => {
    if (!canvasRef.current || !analyzerRef.current) return;
    
    const canvas = canvasRef.current;
    const canvasCtx = canvas.getContext('2d');
    const analyzer = analyzerRef.current;
    
    const bufferLength = analyzer.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    const draw = () => {
      if (!isPlaying) return;
      
      animationRef.current = requestAnimationFrame(draw);
      
      analyzer.getByteFrequencyData(dataArray);
      
      // Clear canvas
      canvasCtx.fillStyle = 'rgba(17, 24, 39, 0.1)';
      canvasCtx.fillRect(0, 0, canvas.width, canvas.height);
      
      // Draw bars
      const barWidth = (canvas.width / bufferLength) * 2.5;
      let x = 0;
      
      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height;
        
        // Gradient for bars
        const gradient = canvasCtx.createLinearGradient(0, canvas.height - barHeight, 0, canvas.height);
        gradient.addColorStop(0, 'rgb(139, 92, 246)');
        gradient.addColorStop(1, 'rgb(99, 102, 241)');
        
        canvasCtx.fillStyle = gradient;
        canvasCtx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
        
        x += barWidth + 1;
      }
    };
    
    draw();
  };

  const formatTime = (seconds) => {
    if (isNaN(seconds)) return '0:00';
    
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!audioUrl) return null;

  return (
    <div className="audio-player bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 rounded-lg p-4 shadow-lg border border-gray-200 dark:border-gray-700">
      {/* Hidden Audio Element */}
      <audio
        ref={audioRef}
        src={fullAudioUrl}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={handleEnded}
        onError={(e) => {
          console.error('[AudioPlayer] Audio error:', e);
          console.error('[AudioPlayer] Error details:', e.target.error);
          setError(`Error al cargar el audio: ${e.target.error?.message || 'Desconocido'}`);
        }}
        onLoadStart={() => console.log('[AudioPlayer] Audio load started')}
        onCanPlay={() => console.log('[AudioPlayer] Audio can play')}
        onLoadedData={() => console.log('[AudioPlayer] Audio data loaded')}
        preload="metadata"
        crossOrigin="anonymous"
      />

      {/* Visualization Canvas */}
      <div className="mb-4">
        <canvas
          ref={canvasRef}
          width={400}
          height={80}
          className="w-full rounded-lg bg-gray-900/5 dark:bg-gray-950/50"
        />
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div
          ref={progressBarRef}
          onClick={handleProgressClick}
          className="w-full h-2 bg-gray-300 dark:bg-gray-700 rounded-full cursor-pointer relative group"
        >
          <div
            className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full transition-all relative"
            style={{ width: `${(currentTime / duration) * 100 || 0}%` }}
          >
            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-4 h-4 bg-white dark:bg-gray-200 rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>
        
        {/* Time Display */}
        <div className="flex justify-between mt-2 text-xs text-gray-600 dark:text-gray-400">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between gap-4">
        {/* Left Controls */}
        <div className="flex items-center gap-2">
          {/* Play/Pause Button */}
          <button
            onClick={togglePlayPause}
            disabled={isLoading || error}
            className="p-2 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            title={isPlaying ? 'Pausar' : 'Reproducir'}
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : isPlaying ? (
              <Pause className="w-5 h-5" />
            ) : (
              <Play className="w-5 h-5 ml-0.5" />
            )}
          </button>

          {/* Reset Button */}
          <button
            onClick={resetAudio}
            className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            title="Reiniciar"
          >
            <RotateCcw className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          </button>

          {/* Playback Speed */}
          <div className="flex items-center gap-1 ml-2">
            {[0.75, 1, 1.25, 1.5].map(rate => (
              <button
                key={rate}
                onClick={() => handlePlaybackRateChange(rate)}
                className={`
                  px-2 py-1 text-xs rounded transition-colors
                  ${playbackRate === rate 
                    ? 'bg-purple-500 text-white' 
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                  }
                `}
              >
                {rate}x
              </button>
            ))}
          </div>
        </div>

        {/* Right Controls */}
        <div className="flex items-center gap-3">
          {/* Volume Control */}
          <div className="flex items-center gap-2">
            <button
              onClick={toggleMute}
              className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              title={isMuted ? 'Activar sonido' : 'Silenciar'}
            >
              {isMuted || volume === 0 ? (
                <VolumeX className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              ) : (
                <Volume2 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              )}
            </button>
            
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={isMuted ? 0 : volume}
              onChange={handleVolumeChange}
              className="w-20 h-1 bg-gray-300 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-600"
            />
          </div>

          {/* Download Button */}
          <button
            onClick={downloadAudio}
            className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            title="Descargar audio"
          >
            <Download className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-3 p-2 bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 rounded text-sm text-danger-600 dark:text-danger-400">
          {error}
        </div>
      )}
    </div>
  );
}
