import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'
import '../mocks/server'

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Mock matchMedia
global.matchMedia = global.matchMedia || function () {
  return {
    matches: false,
    addListener: function () {},
    removeListener: function () {},
  }
}

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
  takeRecords() {
    return []
  }
}

// Mock MediaRecorder for voice tests
global.MediaRecorder = class MediaRecorder {
  constructor() {
    this.state = 'inactive'
  }
  start() {
    this.state = 'recording'
  }
  stop() {
    this.state = 'inactive'
  }
  addEventListener() {}
  removeEventListener() {}
}

// Mock scrollIntoView
Element.prototype.scrollIntoView = function() {}

