import axios from 'axios'

const API_URL = 'http://localhost:8000/api/google'

const getAuthHeaders = () => {
  const token = localStorage.getItem('auth_token')
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
}

export const googleContactsService = {
  /**
   * Get user contacts from Google with pagination
   * @param {number} pageSize - Number of contacts per page (default: 100)
   * @param {string} pageToken - Token for next page (optional)
   * @returns {Promise<{contacts: Array, nextPageToken: string}>}
   */
  async getContacts(pageSize = 100, pageToken = null) {
    try {
      const params = { page_size: pageSize }
      if (pageToken) {
        params.page_token = pageToken
      }

      const response = await axios.get(`${API_URL}/contacts`, {
        headers: getAuthHeaders(),
        params
      })

      return response.data
    } catch (error) {
      console.error('Error fetching contacts:', error)
      throw error
    }
  },

  /**
   * Search contacts by name
   * @param {string} query - Name to search for
   * @returns {Promise<{contacts: Array}>}
   */
  async searchContacts(query) {
    try {
      const response = await axios.post(
        `${API_URL}/contacts/search`,
        { query },
        { headers: getAuthHeaders() }
      )

      return response.data
    } catch (error) {
      console.error('Error searching contacts:', error)
      throw error
    }
  },

  /**
   * Get detailed information for a specific contact
   * @param {string} resourceName - The resource name of the contact (e.g., "people/c123456789")
   * @returns {Promise<{contact: Object}>}
   */
  async getContactDetail(resourceName) {
    try {
      const encodedResourceName = encodeURIComponent(resourceName)
      const response = await axios.get(`${API_URL}/contacts/${encodedResourceName}`, {
        headers: getAuthHeaders()
      })

      return response.data
    } catch (error) {
      console.error('Error fetching contact detail:', error)
      throw error
    }
  }
}
