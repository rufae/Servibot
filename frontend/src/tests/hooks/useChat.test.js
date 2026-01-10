import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useChat } from '../../hooks/useChat';
import * as services from '../../services';

// Mock the services
vi.mock('../../services', () => ({
  chatService: {
    sendMessage: vi.fn(),
  },
  voiceService: {
    synthesize: vi.fn(),
  },
}));

describe('useChat', () => {
  let mockSetAgentActivity;

  beforeEach(() => {
    vi.clearAllMocks();
    mockSetAgentActivity = vi.fn();
  });

  it('should initialize with empty messages and not loading', () => {
    const { result } = renderHook(() => useChat(mockSetAgentActivity));

    expect(result.current.messages).toEqual([]);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.audioUrlForMessage).toEqual({});
  });

  it('should send a message successfully', async () => {
    const mockResponse = {
      success: true,
      data: {
        response: 'Assistant response',
        sources: [],
        plan: null,
        timestamp: new Date().toISOString(),
      },
    };

    services.chatService.sendMessage.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useChat(mockSetAgentActivity));

    await act(async () => {
      await result.current.sendMessage('Hello');
    });

    // Check that user message was added (with timestamp)
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].role).toBe('user');
    expect(result.current.messages[0].content).toBe('Hello');

    // Check that assistant message was added
    expect(result.current.messages[1].role).toBe('assistant');
    expect(result.current.messages[1].content).toBe('Assistant response');

    expect(result.current.isLoading).toBe(false);
  });

  it('should handle API errors gracefully', async () => {
    services.chatService.sendMessage.mockResolvedValue({
      success: false,
      error: 'API Error',
    });

    const { result } = renderHook(() => useChat(mockSetAgentActivity));

    await act(async () => {
      await result.current.sendMessage('Hello');
    });

    // User message should be added
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].role).toBe('user');

    // Error message should be added
    expect(result.current.messages[1].role).toBe('assistant');
    expect(result.current.messages[1].content).toContain('error');
    expect(result.current.isLoading).toBe(false);
  });

  it('should not send empty messages', async () => {
    const { result } = renderHook(() => useChat(mockSetAgentActivity));

    await act(async () => {
      await result.current.sendMessage('');
    });

    expect(services.chatService.sendMessage).not.toHaveBeenCalled();
    expect(result.current.messages).toHaveLength(0);
  });

  it('should generate TTS for assistant messages', async () => {
    const mockAudioUrl = 'http://example.com/audio.mp3';

    services.voiceService.synthesize.mockResolvedValue({
      success: true,
      data: {
        status: 'success',
        audio_url: mockAudioUrl,
      },
    });

    const { result } = renderHook(() => useChat(mockSetAgentActivity));

    await act(async () => {
      await result.current.generateTTS(0, 'Test message');
    });

    expect(result.current.audioUrlForMessage[0]).toBe(mockAudioUrl);
  });
});
