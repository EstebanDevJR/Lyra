/**
 * Storage utility for persisting messages and sessions
 */

const STORAGE_KEYS = {
  MESSAGES: 'lyra_messages',
  SESSIONS: 'lyra-sessions', // Changed to match component's localStorage key
  CURRENT_SESSION: 'lyra_current_session',
} as const

export interface Message {
  id?: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export interface Session {
  id: string
  name: string
  messages: Message[]
  createdAt: Date
  lastUpdated: Date
}

class StorageManager {
  private isAvailable(): boolean {
    if (typeof window === 'undefined') return false
    try {
      const test = '__storage_test__'
      localStorage.setItem(test, test)
      localStorage.removeItem(test)
      return true
    } catch {
      return false
    }
  }

  saveMessages(sessionId: string, messages: Message[]): void {
    if (!this.isAvailable()) return

    try {
      const key = `${STORAGE_KEYS.MESSAGES}_${sessionId}`
      const serialized = JSON.stringify(messages.map(msg => ({
        ...msg,
        timestamp: msg.timestamp.toISOString()
      })))
      localStorage.setItem(key, serialized)
    } catch (error) {
      console.error('Error saving messages:', error)
    }
  }

  loadMessages(sessionId: string): Message[] {
    if (!this.isAvailable()) return []

    try {
      const key = `${STORAGE_KEYS.MESSAGES}_${sessionId}`
      const stored = localStorage.getItem(key)
      if (!stored) return []

      const parsed = JSON.parse(stored) as Array<Omit<Message, 'timestamp'> & { timestamp: string }>
      return parsed.map((msg, index) => ({
        ...msg,
        // Generate unique ID if missing (for backward compatibility)
        id: msg.id || `${new Date(msg.timestamp).getTime()}-${index}-${msg.role}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date(msg.timestamp)
      }))
    } catch (error) {
      console.error('Error loading messages:', error)
      return []
    }
  }

  saveSessions(sessions: Session[]): void {
    if (!this.isAvailable()) return

    try {
      const serialized = JSON.stringify(sessions.map(session => ({
        ...session,
        createdAt: session.createdAt.toISOString(),
        lastUpdated: session.lastUpdated.toISOString(),
        messages: session.messages.map(msg => ({
          ...msg,
          timestamp: msg.timestamp.toISOString()
        }))
      })))
      localStorage.setItem(STORAGE_KEYS.SESSIONS, serialized)
    } catch (error) {
      console.error('Error saving sessions:', error)
    }
  }

  loadSessions(): Session[] {
    if (!this.isAvailable()) return []

    try {
      const stored = localStorage.getItem(STORAGE_KEYS.SESSIONS)
      if (!stored) return []

      const parsed = JSON.parse(stored) as Array<Omit<Session, 'createdAt' | 'lastUpdated'> & {
        createdAt: string
        lastUpdated: string
        messages: Array<Omit<Message, 'timestamp'> & { timestamp: string }>
      }>

      return parsed.map(session => ({
        ...session,
        createdAt: new Date(session.createdAt),
        lastUpdated: new Date(session.lastUpdated),
        messages: session.messages.map((msg, index) => ({
          ...msg,
          // Generate unique ID if missing (for backward compatibility)
          id: msg.id || `${new Date(msg.timestamp).getTime()}-${index}-${msg.role}-${Math.random().toString(36).substr(2, 9)}`,
          timestamp: new Date(msg.timestamp)
        }))
      }))
    } catch (error) {
      console.error('Error loading sessions:', error)
      return []
    }
  }

  saveCurrentSession(sessionId: string): void {
    if (!this.isAvailable()) return

    try {
      localStorage.setItem(STORAGE_KEYS.CURRENT_SESSION, sessionId)
    } catch (error) {
      console.error('Error saving current session:', error)
    }
  }

  loadCurrentSession(): string | null {
    if (!this.isAvailable()) return null

    try {
      return localStorage.getItem(STORAGE_KEYS.CURRENT_SESSION)
    } catch (error) {
      console.error('Error loading current session:', error)
      return null
    }
  }

  clearAll(): void {
    if (!this.isAvailable()) return

    try {
      Object.values(STORAGE_KEYS).forEach(key => {
        localStorage.removeItem(key)
      })
      // Clear all message keys
      const keys = Object.keys(localStorage)
      keys.forEach(key => {
        if (key.startsWith(`${STORAGE_KEYS.MESSAGES}_`)) {
          localStorage.removeItem(key)
        }
      })
    } catch (error) {
      console.error('Error clearing storage:', error)
    }
  }
}

export const storageManager = new StorageManager()
export default storageManager

