import { setupServer } from 'msw/node'
import { handlers } from './handlers'

/**
 * Setup MSW server for Node.js test environment
 * This intercepts HTTP requests during tests and returns mock responses
 */
export const server = setupServer(...handlers)

/**
 * Establish API mocking before all tests
 */
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'warn' })
})

/**
 * Reset handlers after each test
 */
afterEach(() => {
  server.resetHandlers()
})

/**
 * Clean up after all tests are done
 */
afterAll(() => {
  server.close()
})
