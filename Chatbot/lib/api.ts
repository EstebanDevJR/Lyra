/**
 * API client for connecting to the Lyra backend
 */

import logger from './logger'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const REQUEST_TIMEOUT = 60000 // 60 seconds
const MAX_RETRIES = 3
const RETRY_DELAY = 1000 // 1 second

export interface MessageHistory {
  role: 'user' | 'assistant'
  content: string
}

export interface QueryRequest {
  query: string
  file_path?: string
  chat_history?: MessageHistory[]
}

export interface QueryResponse {
  response: string
  status: string
}

export interface FileUploadResponse {
  file_path: string
  extracted_text?: string
  status: string
  message: string
}

export interface HealthResponse {
  name: string
  version: string
  status: string
  description: string
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  /**
   * Create a fetch request with timeout
   */
  private async fetchWithTimeout(
    url: string,
    options: RequestInit,
    timeout: number = REQUEST_TIMEOUT
  ): Promise<Response> {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), timeout)

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      })
      clearTimeout(timeoutId)
      return response
    } catch (error) {
      clearTimeout(timeoutId)
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error(`Request timeout after ${timeout}ms`)
      }
      throw error
    }
  }

  /**
   * Retry a request with exponential backoff
   */
  private async retryRequest<T>(
    fn: () => Promise<T>,
    retries: number = MAX_RETRIES,
    delay: number = RETRY_DELAY
  ): Promise<T> {
    try {
      return await fn()
    } catch (error) {
      if (retries === 0) {
        throw error
      }

      // Don't retry on client errors (4xx)
      if (error instanceof Error && error.message.includes('4')) {
        throw error
      }

      logger.warn(`Request failed, retrying... (${retries} retries left)`, error)
      await new Promise(resolve => setTimeout(resolve, delay))
      return this.retryRequest(fn, retries - 1, delay * 2)
    }
  }

  /**
   * Check if the API is healthy
   */
  async healthCheck(): Promise<HealthResponse> {
    try {
      const response = await this.fetchWithTimeout(`${this.baseUrl}/health`, {
        method: 'GET',
      })

      if (!response.ok) {
        throw new Error(`Health check failed: ${response.statusText}`)
      }

      return response.json()
    } catch (error) {
      logger.error('Health check failed', error)
      throw error
    }
  }

  /**
   * Send a query to the Lyra agent
   */
  async sendQuery(query: string, filePath?: string, chatHistory?: MessageHistory[]): Promise<string> {
    // Validate input
    if (!query || !query.trim()) {
      throw new Error('Query cannot be empty')
    }

    if (query.length > 5000) {
      throw new Error('Query is too long (max 5000 characters)')
    }

    return this.retryRequest(async () => {
      try {
        const requestBody: QueryRequest = { query: query.trim() }
        if (filePath) {
          requestBody.file_path = filePath
        }
        if (chatHistory && chatHistory.length > 0) {
          // Send all chat history (no limit)
          requestBody.chat_history = chatHistory
        }

        logger.info('Sending query to API', { 
          queryLength: query.length, 
          hasFile: !!filePath,
          historyLength: chatHistory?.length || 0
        })

        const response = await this.fetchWithTimeout(
          `${this.baseUrl}/query`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
          },
          REQUEST_TIMEOUT * 2 // Longer timeout for queries
        )

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: response.statusText }))
          const errorMessage = errorData.detail || `API error: ${response.status}`
          logger.error('Query failed', { status: response.status, error: errorMessage })
          throw new Error(errorMessage)
        }

        const data: QueryResponse = await response.json()
        logger.info('Query successful', { responseLength: data.response.length })
        return data.response
      } catch (error) {
        if (error instanceof Error) {
          throw error
        }
        throw new Error('Unknown error occurred while sending query')
      }
    })
  }

  /**
   * Upload a file to the backend
   */
  async uploadFile(file: File): Promise<FileUploadResponse> {
    // Validate file
    const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB
    if (file.size > MAX_FILE_SIZE) {
      throw new Error(`File is too large. Maximum size: ${MAX_FILE_SIZE / (1024 * 1024)}MB`)
    }

    const allowedTypes = [
      'application/pdf',
      'image/png',
      'image/jpeg',
      'image/jpg',
      'image/tiff',
      'image/bmp',
      'image/gif'
    ]

    if (!allowedTypes.includes(file.type)) {
      throw new Error(`File type not allowed: ${file.type}`)
    }

    return this.retryRequest(async () => {
      try {
        const formData = new FormData()
        formData.append('file', file)

        logger.info('Uploading file', { fileName: file.name, fileSize: file.size, fileType: file.type })

        const response = await this.fetchWithTimeout(
          `${this.baseUrl}/upload`,
          {
            method: 'POST',
            body: formData,
          },
          REQUEST_TIMEOUT * 3 // Longer timeout for file uploads
        )

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: response.statusText }))
          const errorMessage = errorData.detail || `Upload error: ${response.status}`
          logger.error('File upload failed', { status: response.status, error: errorMessage })
          throw new Error(errorMessage)
        }

        const data = await response.json()
        logger.info('File upload successful', { filePath: data.file_path })
        return data
      } catch (error) {
        if (error instanceof Error) {
          throw error
        }
        throw new Error('Unknown error occurred while uploading file')
      }
    })
  }

  /**
   * Get vector store statistics
   */
  async getVectorStoreStats() {
    try {
      const response = await this.fetchWithTimeout(`${this.baseUrl}/vectorstore/stats`, {
        method: 'GET',
      })

      if (!response.ok) {
        throw new Error(`Failed to get stats: ${response.statusText}`)
      }

      return response.json()
    } catch (error) {
      logger.error('Error getting vector store stats', error)
      throw error
    }
  }
}

// Export singleton instance
export const apiClient = new ApiClient()

// Export default instance
export default apiClient

