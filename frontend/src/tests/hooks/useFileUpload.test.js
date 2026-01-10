import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useFileUpload } from '../../hooks/useFileUpload';
import * as services from '../../services';

// Mock the services
vi.mock('../../services', () => ({
  uploadService: {
    uploadFile: vi.fn(),
    getUploadStatus: vi.fn(),
    reindexFile: vi.fn(),
  },
}));

describe('useFileUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize correctly', () => {
    const { result } = renderHook(() => useFileUpload());

    expect(result.current.uploadedFiles).toEqual([]);
    expect(result.current.isUploading).toBe(false);
  });

  it('should upload a file successfully', async () => {
    const mockFile = new File(['content'], 'test.txt', { type: 'text/plain' });
    const mockResponse = {
      success: true,
      data: {
        file_id: '123',
        filename: 'test.txt',
      },
    };

    services.uploadService.uploadFile.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useFileUpload());

    await act(async () => {
      await result.current.uploadFile(mockFile);
    });

    expect(services.uploadService.uploadFile).toHaveBeenCalledWith(
      mockFile,
      expect.any(Function)
    );

    expect(result.current.uploadedFiles).toHaveLength(1);
    expect(result.current.uploadedFiles[0].status).toBe('success');
    expect(result.current.isUploading).toBe(false);
  });

  it('should handle upload errors', async () => {
    const mockFile = new File(['content'], 'test.txt', { type: 'text/plain' });

    services.uploadService.uploadFile.mockResolvedValue({
      success: false,
      error: 'Upload failed',
    });

    const { result } = renderHook(() => useFileUpload());

    await act(async () => {
      await result.current.uploadFile(mockFile);
    });

    expect(result.current.isUploading).toBe(false);
    const errorFile = result.current.uploadedFiles.find(f => f.name === 'test.txt');
    expect(errorFile.status).toBe('error');
  });

  it('should reindex a file', async () => {
    services.uploadService.reindexFile.mockResolvedValue({
      success: true,
      data: {
        message: 'Reindexing started',
      },
    });

    const { result } = renderHook(() => useFileUpload());

    // Add a file first
    await act(async () => {
      result.current.setUploadedFiles([
        {
          name: 'test.txt',
          file_id: 'test-file-id',
          status: 'success',
        },
      ]);
    });

    await act(async () => {
      await result.current.reindexFile('test-file-id');
    });

    expect(services.uploadService.reindexFile).toHaveBeenCalledWith(
      'test-file-id'
    );
  });
});
