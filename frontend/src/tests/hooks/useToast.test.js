import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useToast } from '../../hooks/useToast';

describe('useToast', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it('should initialize with no toast', () => {
    const { result } = renderHook(() => useToast());
    expect(result.current.toasts).toEqual([]);
  });

  it('should show a toast with custom message', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showToast('Test message', 'info');
    });

    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0]).toMatchObject({
      message: 'Test message',
      type: 'info',
    });
  });

  it('should show an error toast', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showError('Error occurred');
    });

    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0]).toMatchObject({
      message: 'Error occurred',
      type: 'error',
    });
  });

  it('should show a success toast', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showSuccess('Success!');
    });

    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0]).toMatchObject({
      message: 'Success!',
      type: 'success',
    });
  });

  it('should show a warning toast', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showWarning('Warning!');
    });

    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0]).toMatchObject({
      message: 'Warning!',
      type: 'warning',
    });
  });

  it('should show an info toast', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showInfo('Info message');
    });

    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0]).toMatchObject({
      message: 'Info message',
      type: 'info',
    });
  });

  it('should hide toast manually', () => {
    const { result } = renderHook(() => useToast());

    let toastId;
    act(() => {
      toastId = result.current.showToast('Test message');
    });

    expect(result.current.toasts).toHaveLength(1);

    act(() => {
      result.current.hideToast(toastId);
    });

    expect(result.current.toasts).toHaveLength(0);
  });

  it('should auto-dismiss toast after duration', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showToast('Test message', 'info', 3000);
    });

    expect(result.current.toasts).toHaveLength(1);

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(result.current.toasts).toHaveLength(0);
  });

  it('should use default duration when not provided', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showToast('Test message');
    });

    expect(result.current.toasts).toHaveLength(1);

    // Default duration should be 5000ms
    act(() => {
      vi.advanceTimersByTime(4999);
    });

    expect(result.current.toasts).toHaveLength(1);

    act(() => {
      vi.advanceTimersByTime(1);
    });

    expect(result.current.toasts).toHaveLength(0);
  });

  it('should show multiple toasts at once', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showToast('First message', 'info', 5000);
    });

    act(() => {
      result.current.showToast('Second message', 'success', 5000);
    });

    expect(result.current.toasts).toHaveLength(2);
    expect(result.current.toasts[0].message).toBe('First message');
    expect(result.current.toasts[1].message).toBe('Second message');
  });
});
