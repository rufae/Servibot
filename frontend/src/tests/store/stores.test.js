import { describe, it, expect, beforeEach } from 'vitest';
import { act } from '@testing-library/react';
import { useChatStore, useUploadStore, useSettingsStore } from '../../store';

describe('useChatStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useChatStore.setState({
      messages: [],
      agentActivity: null,
      isLoading: false,
      audioUrlForMessage: {},
    });
  });

  it('should initialize with default values', () => {
    const state = useChatStore.getState();
    expect(state.messages).toEqual([]);
    expect(state.agentActivity).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.audioUrlForMessage).toEqual({});
  });

  it('should add a message', () => {
    act(() => {
      useChatStore.getState().addMessage({
        role: 'user',
        content: 'Hello',
      });
    });

    const state = useChatStore.getState();
    expect(state.messages).toHaveLength(1);
    expect(state.messages[0]).toEqual({
      role: 'user',
      content: 'Hello',
    });
  });

  it('should add multiple messages', () => {
    act(() => {
      useChatStore.getState().addMessage({
        role: 'user',
        content: 'Hello',
      });
      useChatStore.getState().addMessage({
        role: 'assistant',
        content: 'Hi there',
      });
    });

    const state = useChatStore.getState();
    expect(state.messages).toHaveLength(2);
    expect(state.messages[1].content).toBe('Hi there');
  });

  it('should set loading state', () => {
    act(() => {
      useChatStore.getState().setIsLoading(true);
    });

    expect(useChatStore.getState().isLoading).toBe(true);

    act(() => {
      useChatStore.getState().setIsLoading(false);
    });

    expect(useChatStore.getState().isLoading).toBe(false);
  });

  it('should set agent activity', () => {
    const activity = {
      steps: [{ action: 'search', status: 'completed' }],
    };

    act(() => {
      useChatStore.getState().setAgentActivity(activity);
    });

    expect(useChatStore.getState().agentActivity).toEqual(activity);
  });

  it('should clear agent activity', () => {
    act(() => {
      useChatStore.getState().setAgentActivity({
        steps: [{ action: 'search', status: 'completed' }],
      });
      useChatStore.getState().setAgentActivity(null);
    });

    expect(useChatStore.getState().agentActivity).toBeNull();
  });

  it('should set audio URL for specific message', () => {
    act(() => {
      useChatStore.getState().setAudioUrl(0, 'audio-url-1');
      useChatStore.getState().setAudioUrl(1, 'audio-url-2');
    });

    const state = useChatStore.getState();
    expect(state.audioUrlForMessage[0]).toBe('audio-url-1');
    expect(state.audioUrlForMessage[1]).toBe('audio-url-2');
  });

  it('should clear messages', () => {
    act(() => {
      useChatStore.getState().addMessage({ role: 'user', content: 'Test' });
      useChatStore.getState().clearMessages();
    });

    expect(useChatStore.getState().messages).toEqual([]);
  });
});

describe('useUploadStore', () => {
  beforeEach(() => {
    useUploadStore.setState({
      uploadedFiles: [],
    });
  });

  it('should initialize with empty array', () => {
    const state = useUploadStore.getState();
    expect(state.uploadedFiles).toEqual([]);
  });

  it('should add uploaded file', () => {
    const file = {
      file_id: '123',
      filename: 'test.txt',
      status: 'uploaded',
    };

    act(() => {
      useUploadStore.getState().addUploadedFile(file);
    });

    const state = useUploadStore.getState();
    expect(state.uploadedFiles).toHaveLength(1);
    expect(state.uploadedFiles[0]).toEqual(file);
  });

  it('should update file by name', () => {
    act(() => {
      useUploadStore.getState().addUploadedFile({
        file_id: '123',
        name: 'test.txt',
        status: 'uploaded',
      });
      useUploadStore.getState().updateUploadedFile('test.txt', {
        status: 'indexed',
        progress: 100,
      });
    });

    const state = useUploadStore.getState();
    expect(state.uploadedFiles[0].status).toBe('indexed');
    expect(state.uploadedFiles[0].progress).toBe(100);
  });

  it('should update file by ID', () => {
    act(() => {
      useUploadStore.getState().addUploadedFile({
        file_id: '123',
        name: 'test.txt',
        status: 'uploaded',
      });
      useUploadStore.getState().updateUploadedFileById('123', {
        status: 'indexing',
        progress: 50,
      });
    });

    const state = useUploadStore.getState();
    expect(state.uploadedFiles[0].status).toBe('indexing');
    expect(state.uploadedFiles[0].progress).toBe(50);
  });

  it('should not update if file not found by name', () => {
    act(() => {
      useUploadStore.getState().addUploadedFile({
        file_id: '123',
        name: 'test.txt',
        status: 'uploaded',
      });
      useUploadStore.getState().updateUploadedFile('nonexistent.txt', {
        status: 'indexed',
      });
    });

    const state = useUploadStore.getState();
    expect(state.uploadedFiles[0].status).toBe('uploaded');
  });

  it('should not update if file not found by ID', () => {
    act(() => {
      useUploadStore.getState().addUploadedFile({
        file_id: '123',
        name: 'test.txt',
        status: 'uploaded',
      });
      useUploadStore.getState().updateUploadedFileById('999', {
        status: 'indexed',
      });
    });

    const state = useUploadStore.getState();
    expect(state.uploadedFiles[0].status).toBe('uploaded');
  });

  it('should clear all files', () => {
    act(() => {
      useUploadStore.getState().addUploadedFile({
        file_id: '123',
        name: 'test.txt',
        status: 'uploaded',
      });
      useUploadStore.getState().clearUploadedFiles();
    });

    const state = useUploadStore.getState();
    expect(state.uploadedFiles).toHaveLength(0);
  });

  it('should add multiple files', () => {
    act(() => {
      useUploadStore.getState().addUploadedFile({
        file_id: '1',
        name: 'test1.txt',
        status: 'uploaded',
      });
      useUploadStore.getState().addUploadedFile({
        file_id: '2',
        name: 'test2.txt',
        status: 'uploaded',
      });
    });

    const state = useUploadStore.getState();
    expect(state.uploadedFiles).toHaveLength(2);
  });
});

describe('useSettingsStore', () => {
  beforeEach(() => {
    useSettingsStore.setState({
      voiceEnabled: false,
      theme: 'light',
      showFileManager: true,
    });
  });

  it('should initialize with default values', () => {
    const state = useSettingsStore.getState();
    expect(state.voiceEnabled).toBe(false);
    expect(state.theme).toBe('light');
    expect(state.showFileManager).toBe(true);
  });

  it('should toggle voice enabled', () => {
    act(() => {
      useSettingsStore.getState().setVoiceEnabled(true);
    });

    expect(useSettingsStore.getState().voiceEnabled).toBe(true);

    act(() => {
      useSettingsStore.getState().setVoiceEnabled(false);
    });

    expect(useSettingsStore.getState().voiceEnabled).toBe(false);
  });

  it('should change theme', () => {
    act(() => {
      useSettingsStore.getState().setTheme('dark');
    });

    expect(useSettingsStore.getState().theme).toBe('dark');

    act(() => {
      useSettingsStore.getState().setTheme('light');
    });

    expect(useSettingsStore.getState().theme).toBe('light');
  });

  it('should toggle file manager visibility', () => {
    act(() => {
      useSettingsStore.getState().setShowFileManager(false);
    });

    expect(useSettingsStore.getState().showFileManager).toBe(false);

    act(() => {
      useSettingsStore.getState().setShowFileManager(true);
    });

    expect(useSettingsStore.getState().showFileManager).toBe(true);
  });

  it('should update multiple settings independently', () => {
    act(() => {
      useSettingsStore.getState().setVoiceEnabled(true);
      useSettingsStore.getState().setTheme('dark');
      useSettingsStore.getState().setShowFileManager(false);
    });

    const state = useSettingsStore.getState();
    expect(state.voiceEnabled).toBe(true);
    expect(state.theme).toBe('dark');
    expect(state.showFileManager).toBe(false);
  });
});
