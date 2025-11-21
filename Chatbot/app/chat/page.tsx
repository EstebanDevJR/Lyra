'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Send, Upload, Minimize2, Phone, PhoneOff, Mic, MicOff, Plus, Trash2, MessageSquare, Menu, X, Home } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import apiClient from '@/lib/api'
import logger from '@/lib/logger'
import storageManager, { type Message as StorageMessage, type Session as StorageSession } from '@/lib/storage'
import { RealtimeClient } from '@/lib/realtime'

interface Message {
  id?: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface Session {
  id: string
  name: string
  messages: Message[]
  createdAt: Date
  lastUpdated: Date
}

import NewsGrid from '@/components/news/NewsGrid'
import AstronomyImage from '@/components/astronomy/AstronomyImage'
import ResearchPapers from '@/components/astronomy/ResearchPapers'
import AstroAlerts from '@/components/astronomy/AstroAlerts'

export default function LyraChatbot() {
  // ... (resto del código)
  const router = useRouter()
  const [sessions, setSessions] = useState<Session[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string>('')
  const [showSidebar, setShowSidebar] = useState(false)
  
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isMinimized, setIsMinimized] = useState(true)
  const [isCallMode, setIsCallMode] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [callDuration, setCallDuration] = useState(0)
  const [callState, setCallState] = useState<'connecting' | 'connected' | 'listening' | 'speaking' | 'processing' | 'error'>('connecting')
  const [audioLevel, setAudioLevel] = useState(0)
  const [volume, setVolume] = useState(1.0)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const realtimeClientRef = useRef<RealtimeClient | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const parallaxRef = useRef<HTMLDivElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isResizing, setIsResizing] = useState(false)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [size, setSize] = useState({ width: 896, height: 600 })
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const containerCenterRef = useRef<{ x: number; y: number } | null>(null)
  const [windowSize, setWindowSize] = useState(() => {
    if (typeof window !== 'undefined') {
      return { width: window.innerWidth || 896, height: window.innerHeight || 600 }
    }
    return { width: 896, height: 600 }
  })
  const [isMounted, setIsMounted] = useState(false)
  const chatboxRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Resetear scroll al montar el componente
    window.scrollTo(0, 0)
    // Permitir scroll cuando está minimizado (estado inicial)
    document.body.style.overflow = isMinimized ? 'auto' : 'hidden'
    
    // Inicializar tamaño de ventana inmediatamente
    const updateWindowSize = () => {
      setWindowSize({ width: window.innerWidth, height: window.innerHeight })
    }
    
    // Actualizar múltiples veces para asegurar que se ejecute correctamente
    updateWindowSize()
    requestAnimationFrame(() => {
      updateWindowSize()
      requestAnimationFrame(updateWindowSize)
    })
    
    // También actualizar después de un pequeño delay
    setTimeout(updateWindowSize, 100)
    setTimeout(updateWindowSize, 300)
    
    window.addEventListener('resize', updateWindowSize)
    
    // Marcar como montado después de asegurar que el tamaño está inicializado
    setTimeout(() => {
      setIsMounted(true)
    }, 100)
    
    // Interceptar el botón "atrás" del navegador para hacer refresh de la página principal
    const handlePopState = () => {
      // Redirigir a la página principal y hacer refresh completo
      window.location.href = '/'
    }
    
    window.addEventListener('popstate', handlePopState)
    
    return () => {
      window.removeEventListener('resize', updateWindowSize)
      window.removeEventListener('popstate', handlePopState)
      document.body.style.overflow = ''
    }
  }, [isMinimized])

  // Efecto adicional para asegurar que el tamaño se actualice después de la navegación
  useEffect(() => {
    if (isMounted) {
      // Forzar actualización del tamaño cuando el componente está montado
      const forceUpdateSize = () => {
        setWindowSize({ width: window.innerWidth, height: window.innerHeight })
      }
      
      // Actualizar inmediatamente y con delays
      forceUpdateSize()
      setTimeout(forceUpdateSize, 50)
      setTimeout(forceUpdateSize, 200)
      setTimeout(forceUpdateSize, 500)
    }
  }, [isMounted])

  // Controlar overflow del body según el estado de minimizado
  useEffect(() => {
    document.body.style.overflow = isMinimized ? 'auto' : 'hidden'
    return () => {
      // No resetear aquí, se hace en el cleanup del useEffect principal
    }
  }, [isMinimized])

  useEffect(() => {
    // Load sessions from storageManager (unified storage)
    const loadedSessions = storageManager.loadSessions()
    if (loadedSessions.length > 0) {
      setSessions(loadedSessions)
      const currentSessionId = storageManager.loadCurrentSession()
      if (currentSessionId && loadedSessions.find(s => s.id === currentSessionId)) {
        // Load messages from storageManager for the current session
        const sessionMessages = storageManager.loadMessages(currentSessionId)
        // Ensure all messages have unique IDs
        const messagesWithIds = sessionMessages.map((msg, idx) => ({
          ...msg,
          id: msg.id || `${msg.timestamp.getTime()}-${idx}-${msg.role}-${Math.random().toString(36).substr(2, 9)}`
        }))
        setCurrentSessionId(currentSessionId)
        setMessages(messagesWithIds.length > 0 ? messagesWithIds : loadedSessions.find(s => s.id === currentSessionId)?.messages.map((msg, idx) => ({
          ...msg,
          id: msg.id || `${msg.timestamp.getTime()}-${idx}-${msg.role}-${Math.random().toString(36).substr(2, 9)}`
        })) || [])
      } else {
        // Use first session
        const firstSession = loadedSessions[0]
        const sessionMessages = storageManager.loadMessages(firstSession.id)
        // Ensure all messages have unique IDs
        const messagesWithIds = sessionMessages.map((msg, idx) => ({
          ...msg,
          id: msg.id || `${msg.timestamp.getTime()}-${idx}-${msg.role}-${Math.random().toString(36).substr(2, 9)}`
        }))
        setCurrentSessionId(firstSession.id)
        setMessages(messagesWithIds.length > 0 ? messagesWithIds : firstSession.messages.map((msg, idx) => ({
          ...msg,
          id: msg.id || `${msg.timestamp.getTime()}-${idx}-${msg.role}-${Math.random().toString(36).substr(2, 9)}`
        })))
        storageManager.saveCurrentSession(firstSession.id)
      }
    } else {
      createNewSession()
    }
  }, [])

  useEffect(() => {
    // Save sessions to storageManager (unified storage)
    if (sessions.length > 0) {
      storageManager.saveSessions(sessions)
    }
  }, [sessions])

  useEffect(() => {
    if (currentSessionId && messages.length > 0) {
      // Ensure all messages have unique IDs before saving
      const messagesWithIds = messages.map((msg, idx) => ({
        ...msg,
        id: msg.id || `${msg.timestamp.getTime()}-${idx}-${msg.role}-${Math.random().toString(36).substr(2, 9)}`
      }))
      
      // Update session in state
      setSessions(prev => prev.map(session => 
        session.id === currentSessionId 
          ? { ...session, messages: messagesWithIds, lastUpdated: new Date() }
          : session
      ))
      // Also save to storageManager
      storageManager.saveMessages(currentSessionId, messagesWithIds)
    }
  }, [messages, currentSessionId])

  const createNewSession = () => {
    const newSession: Session = {
      id: Date.now().toString(),
      name: `Sesión ${sessions.length + 1}`,
      messages: [{
        id: `${Date.now()}-welcome-${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: '¡Hola! Soy **Lyra**, tu asistente de inteligencia artificial especializado en astrofísica. Puedo analizar, resumir y contextualizar información sobre agujeros negros, galaxias y fenómenos del espacio. ¿En qué puedo ayudarte?',
        timestamp: new Date()
      }],
      createdAt: new Date(),
      lastUpdated: new Date()
    }
    setSessions(prev => {
      const updated = [newSession, ...prev]
      storageManager.saveSessions(updated)
      return updated
    })
    setCurrentSessionId(newSession.id)
    setMessages(newSession.messages)
    storageManager.saveMessages(newSession.id, newSession.messages)
    storageManager.saveCurrentSession(newSession.id)
  }

  const loadSession = (sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId)
    if (session) {
      // Load messages from storageManager first, fallback to session messages
      const storedMessages = storageManager.loadMessages(sessionId)
      // Ensure all messages have unique IDs
      const messagesWithIds = storedMessages.length > 0 
        ? storedMessages.map((msg, idx) => ({
            ...msg,
            id: msg.id || `${msg.timestamp.getTime()}-${idx}-${msg.role}-${Math.random().toString(36).substr(2, 9)}`
          }))
        : session.messages.map((msg, idx) => ({
            ...msg,
            id: msg.id || `${msg.timestamp.getTime()}-${idx}-${msg.role}-${Math.random().toString(36).substr(2, 9)}`
          }))
      setCurrentSessionId(sessionId)
      setMessages(messagesWithIds)
      storageManager.saveCurrentSession(sessionId)
      setShowSidebar(false)
    }
  }

  const deleteSession = (sessionId: string) => {
    setSessions(prev => {
      const filtered = prev.filter(s => s.id !== sessionId)
      if (filtered.length === 0) {
        createNewSession()
        return filtered
      }
      if (currentSessionId === sessionId) {
        setCurrentSessionId(filtered[0].id)
        setMessages(filtered[0].messages)
      }
      return filtered
    })
  }

  const getSessionName = (session: Session) => {
    const firstUserMessage = session.messages.find(m => m.role === 'user')
    if (firstUserMessage) {
      return firstUserMessage.content.slice(0, 40) + (firstUserMessage.content.length > 40 ? '...' : '')
    }
    return session.name
  }

  useEffect(() => {
    const handleScroll = () => {
      if (parallaxRef.current) {
        const scrolled = window.scrollY
        parallaxRef.current.style.transform = `translateY(${scrolled * 0.3}px)`
      }
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    const container = document.querySelector('.particles-container')
    if (!container) return

    for (let i = 0; i < 30; i++) {
      const particle = document.createElement('div')
      particle.className = 'particle'
      particle.style.left = `${Math.random() * 100}%`
      particle.style.animationDuration = `${15 + Math.random() * 20}s`
      particle.style.animationDelay = `${Math.random() * 5}s`
      particle.style.opacity = `${0.2 + Math.random() * 0.4}`
      container.appendChild(particle)
    }
  }, [])

  useEffect(() => {
    let interval: NodeJS.Timeout
    if (isCallMode) {
      interval = setInterval(() => {
        setCallDuration(prev => prev + 1)
      }, 1000)
    } else {
      setCallDuration(0)
    }
    return () => clearInterval(interval)
  }, [isCallMode])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    // Messages are saved in the sessions effect above
  }, [messages])

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage: Message = {
      id: `${Date.now()}-user-${Math.random().toString(36).substr(2, 9)}`,
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    const queryText = input
    setInput('')
    setIsLoading(true)

    try {
      // Prepare chat history (exclude the current message we just added)
      const chatHistory = messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }))
      
      // Call backend API with chat history
      logger.info('Sending query', { 
        query: queryText.substring(0, 100),
        historyLength: chatHistory.length
      })
      const response = await apiClient.sendQuery(queryText, undefined, chatHistory)
      
      const assistantMessage: Message = {
        id: `${Date.now()}-assistant-${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: response,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, assistantMessage])
      logger.info('Query successful')
    } catch (error) {
      logger.error('Error sending query', error)
      
      let errorMessage = 'Lo siento, ocurrió un error al procesar tu consulta.'
      
      if (error instanceof Error) {
        if (error.message.includes('timeout')) {
          errorMessage = 'La consulta está tomando demasiado tiempo. Por favor, intenta con una consulta más corta o específica.'
        } else if (error.message.includes('fetch')) {
          errorMessage = 'No se pudo conectar con el servidor. Por favor, verifica que el backend esté ejecutándose en http://localhost:8000'
        } else {
          errorMessage = `Error: ${error.message}`
        }
      }
      
      const errorMsg: Message = {
        id: `${Date.now()}-error-${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: errorMessage,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setIsLoading(true)
    try {
      const result = await apiClient.uploadFile(file)
      
      // Add file info message
      const fileMessage: Message = {
        id: `${Date.now()}-file-${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: `✅ Archivo "${file.name}" subido exitosamente.\n\n${result.extracted_text ? `Texto extraído (${result.extracted_text.length} caracteres):\n${result.extracted_text.substring(0, 500)}...` : 'El archivo se procesó correctamente.'}\n\nAhora puedes hacer preguntas sobre este documento.`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, fileMessage])
    } catch (error) {
      logger.error('Error uploading file', error)
      
      let errorMessage = 'Error al subir el archivo.'
      if (error instanceof Error) {
        if (error.message.includes('too large')) {
          errorMessage = 'El archivo es demasiado grande. Tamaño máximo: 50MB'
        } else if (error.message.includes('not allowed')) {
          errorMessage = 'Tipo de archivo no permitido. Formatos permitidos: PDF, PNG, JPG, JPEG, TIFF, BMP, GIF'
        } else {
          errorMessage = `Error: ${error.message}`
        }
      }
      
      const errorMsg: Message = {
        id: `${Date.now()}-error-${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: errorMessage,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setIsLoading(false)
      // Reset file input
      if (event.target) {
        event.target.value = ''
      }
    }
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const toggleCallMode = async () => {
    if (!isCallMode) {
      // Starting call mode
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const client = new RealtimeClient(baseUrl)
        realtimeClientRef.current = client

        // Connect to Realtime API
        await client.connect({
          onTranscript: (text: string, role: 'user' | 'assistant') => {
            // Handle final transcripts only (when conversation.item.input_audio_transcription.completed)
            // Or intermediate?
            // The 'transcript' event in RealtimeClient is emitted for user input transcription (completed)
            logger.info('Transcript received', { text, role })
            if (role === 'user') {
               setMessages(prev => [...prev, {
                  id: `${Date.now()}-transcript-${Math.random().toString(36).substr(2, 9)}`,
                  role: role,
                  content: text,
                  timestamp: new Date()
                }])
            }
          },
          // 'onAudio' is not used as RealtimeClient handles playback internally
          onError: (error: Error) => {
            logger.error('Realtime API error', error)
            setCallState('error')
            setMessages(prev => [...prev, {
              id: `${Date.now()}-error-${Math.random().toString(36).substr(2, 9)}`,
              role: 'assistant',
              content: `Error en modo llamada: ${error.message}`,
              timestamp: new Date()
            }])
          },
          onClose: () => {
            logger.info('Realtime connection closed')
            setIsCallMode(false)
            setCallState('error')
          },
          onStateChange: (state) => {
            setCallState(state)
            logger.info('Call state changed', { state })
          },
          onAudioLevel: (level: number) => {
            setAudioLevel(level)
          },
          onMessage: (text: string) => {
             // Handle partial assistant response (delta)
             setMessages(prev => {
              const newMessages = [...prev]
              const lastMsg = newMessages[newMessages.length - 1]
              
              if (lastMsg && lastMsg.id === 'realtime-temp') {
                 lastMsg.content += text
              } else if (lastMsg && lastMsg.role === 'assistant' && !lastMsg.id) {
                 lastMsg.content += text
                 lastMsg.id = 'realtime-temp'
              } else {
                newMessages.push({
                  id: 'realtime-temp',
                  role: 'assistant',
                  content: text,
                  timestamp: new Date()
                })
              }
              return newMessages
            })
          }
        })
        
        // Remove manual client.on listeners since they are not supported
        // and we are using callbacks in connect()

        // Start audio capture
        await client.startAudio()

        setIsCallMode(true)
        setMessages(prev => [...prev, {
          id: `${Date.now()}-call-${Math.random().toString(36).substr(2, 9)}`,
          role: 'assistant',
          content: 'Modo llamada activado. Puedo escucharte ahora.',
          timestamp: new Date()
        }])
        logger.info('Call mode started')
      } catch (error) {
        logger.error('Error starting call mode', error)
        const errorMessage = error instanceof Error ? error.message : 'Error desconocido'
        alert(`Error al iniciar el modo llamada: ${errorMessage}. Asegúrate de permitir el acceso al micrófono.`)
      }
    } else {
      // Stopping call mode
      if (realtimeClientRef.current) {
        realtimeClientRef.current.disconnect()
        realtimeClientRef.current = null
      }
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current = null
      }
      setIsCallMode(false)
      setMessages(prev => [...prev, {
        id: `${Date.now()}-call-end-${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: 'Modo llamada desactivado.',
        timestamp: new Date()
      }])
      logger.info('Call mode stopped')
    }
  }

  const handleMuteToggle = () => {
    setIsMuted(!isMuted)
    if (realtimeClientRef.current) {
      if (isMuted) {
        // Unmute: restart audio
        realtimeClientRef.current.startAudio().catch(err => {
          logger.error('Error restarting audio', err)
        })
      } else {
        // Mute: stop audio
        realtimeClientRef.current.stopAudio()
      }
    }
  }
  
  const handleVolumeChange = (newVolume: number) => {
    setVolume(newVolume)
    if (realtimeClientRef.current) {
      realtimeClientRef.current.setVolume(newVolume)
    }
  }
  
  const handleInterrupt = () => {
    if (realtimeClientRef.current) {
      realtimeClientRef.current.interrupt()
    }
  }

  const handleMouseDown = (e: React.MouseEvent) => {
    const target = e.target as HTMLElement
    const rect = chatboxRef.current?.getBoundingClientRect()
    if (!rect || !containerRef.current) return

    if (target.closest('.draggable-header')) {
      e.preventDefault()
      e.stopPropagation()
      setIsDragging(true)
      // Almacenar el centro del contenedor al inicio del arrastre para evitar recalcularlo
      const containerRect = containerRef.current.getBoundingClientRect()
      containerCenterRef.current = {
        x: containerRect.left + containerRect.width / 2,
        y: containerRect.top + containerRect.height / 2
      }
      const chatboxCenterX = rect.left + rect.width / 2
      const chatboxCenterY = rect.top + rect.height / 2
      // El offset es la diferencia entre donde está el mouse y donde está el centro del chatbox relativo al contenedor
      setDragOffset({
        x: e.clientX - containerCenterRef.current.x - (chatboxCenterX - containerCenterRef.current.x),
        y: e.clientY - containerCenterRef.current.y - (chatboxCenterY - containerCenterRef.current.y)
      })
    }
  }

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (isDragging && containerCenterRef.current) {
      e.preventDefault()
      // Usar el centro del contenedor almacenado para evitar getBoundingClientRect en cada movimiento
      setPosition({
        x: e.clientX - containerCenterRef.current.x - dragOffset.x,
        y: e.clientY - containerCenterRef.current.y - dragOffset.y
      })
    } else if (isResizing) {
      e.preventDefault()
      const rect = chatboxRef.current?.getBoundingClientRect()
      if (rect) {
        const newWidth = Math.max(400, e.clientX - rect.left)
        const newHeight = Math.max(400, e.clientY - rect.top)
        setSize({ width: newWidth, height: newHeight })
      }
    }
  }, [isDragging, isResizing, dragOffset])

  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
    setIsResizing(false)
    containerCenterRef.current = null
  }, [])

  useEffect(() => {
    if (isDragging || isResizing) {
      let rafId: number | null = null
      let lastX = 0
      let lastY = 0
      
      const handleMove = (e: MouseEvent) => {
        // Throttle usando requestAnimationFrame para evitar vibraciones
        if (rafId === null) {
          rafId = requestAnimationFrame(() => {
            handleMouseMove(e)
            rafId = null
          })
        }
      }
      
      const handleUp = () => {
        if (rafId !== null) {
          cancelAnimationFrame(rafId)
          rafId = null
        }
        handleMouseUp()
      }
      
      window.addEventListener('mousemove', handleMove, { passive: false })
      window.addEventListener('mouseup', handleUp)
      document.body.style.userSelect = 'none'
      document.body.style.cursor = isDragging ? 'grabbing' : 'default'
      document.body.style.pointerEvents = 'auto'
      
      return () => {
        if (rafId !== null) {
          cancelAnimationFrame(rafId)
        }
        window.removeEventListener('mousemove', handleMove)
        window.removeEventListener('mouseup', handleUp)
        document.body.style.userSelect = ''
        document.body.style.cursor = ''
        document.body.style.pointerEvents = ''
      }
    }
  }, [isDragging, isResizing, handleMouseMove, handleMouseUp])

  const handleResizeMouseDown = (e: React.MouseEvent) => {
    e.stopPropagation()
    setIsResizing(true)
  }

  return (
    <>
      <div className="parallax-container">
        <div 
          ref={parallaxRef}
          className="parallax-bg black-hole-pulse"
          style={{
            backgroundImage: 'url(https://hebbkx1anhila5yf.public.blob.vercel-storage.com/background-THuPBurvAOBET5b2ftB2ODMREbpDiN.png)',
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-[#0C0B18]/60 via-[#0C0B18]/80 to-[#0C0B18]/95" />
      </div>

      <div className="particles-container fixed inset-0 pointer-events-none z-10" />

      {/* Floating Chat Button when minimized */}
      {isMinimized && (
        <div className="fixed bottom-6 right-6 z-50 fade-blur-in">
          <Button
            onClick={() => setIsMinimized(false)}
            className="w-16 h-16 rounded-full bg-gradient-to-br from-[#FF914D] to-[#FFD8A9] hover:scale-110 transition-transform shadow-2xl glow-pulse"
          >
            <img 
              src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/logo-VU3ODJoqYZG46efDeEvqdHHNA1ntpv.png"
              alt="Lyra"
              className="w-10 h-10 object-contain"
            />
          </Button>
        </div>
      )}

      {!isMinimized && isMounted && (
        <div ref={containerRef} className="fixed inset-0 z-20 overflow-hidden pointer-events-none" style={{ padding: '32px' }}>
          <div 
            ref={chatboxRef}
            className="flex liquid-glass rounded-3xl overflow-hidden fade-blur-in pointer-events-auto"
            style={{
              width: `${Math.min(
                size.width, 
                (windowSize.width > 0 ? windowSize.width : window.innerWidth || 896) - 64
              )}px`,
              height: `${Math.min(
                size.height, 
                (windowSize.height > 0 ? windowSize.height : window.innerHeight || 600) - 64
              )}px`,
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: `translate(calc(-50% + ${position.x}px), calc(-50% + ${position.y}px))`,
              cursor: isDragging ? 'grabbing' : 'default',
              boxShadow: '0 40px 100px rgba(12, 11, 24, 0.8), inset 0 0 80px rgba(40, 37, 69, 0.3)',
              maxWidth: 'calc(100% - 0px)',
              maxHeight: 'calc(100% - 0px)'
            }}
          >
            <div className="absolute inset-0 pointer-events-none border-4 border-transparent hover:border-[#FF914D]/20 rounded-3xl transition-colors" 
                 style={{ borderWidth: '15px' }} />

            <div className={`${showSidebar ? 'w-80' : 'w-0'} transition-all duration-300 overflow-hidden border-r border-[#98A7DD]/20 bg-[#282545]/40 backdrop-blur-sm flex flex-col`}>
              <div className="p-4 border-b border-[#98A7DD]/20 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-[#FFD8A9]">Sesiones</h2>
                <Button
                  onClick={() => setShowSidebar(false)}
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-[#98A7DD] hover:text-[#FFD8A9]"
                >
                  <X className="w-5 h-5" />
                </Button>
              </div>

              <div className="p-3">
                <Button
                  onClick={createNewSession}
                  className="w-full bg-[#FF914D] hover:bg-[#FF914D]/90 text-[#0C0B18] font-semibold space-warp"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Nueva Sesión
                </Button>
              </div>

              <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-2">
                {sessions.map(session => (
                  <div
                    key={session.id}
                    className={`group relative p-3 rounded-lg cursor-pointer transition-all tilt-card ${
                      currentSessionId === session.id
                        ? 'bg-[#FF914D]/20 border border-[#FF914D]/40'
                        : 'bg-[#282545]/60 border border-[#98A7DD]/10 hover:bg-[#282545]/80'
                    }`}
                    onClick={() => loadSession(session.id)}
                  >
                    <div className="flex items-start gap-2">
                      <MessageSquare className="w-4 h-4 text-[#98A7DD] mt-1 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-[#FFD8A9] font-medium truncate">
                          {getSessionName(session)}
                        </p>
                        <p className="text-xs text-[#98A7DD] mt-1">
                          {session.lastUpdated.toLocaleDateString('es-ES', { 
                            day: 'numeric', 
                            month: 'short' 
                          })}
                        </p>
                      </div>
                      <Button
                        onClick={(e) => {
                          e.stopPropagation()
                          deleteSession(session.id)
                        }}
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity text-red-400 hover:text-red-300 hover:bg-red-400/10"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex-1 flex flex-col no-drag">
              <header 
                className="draggable-header border-b border-[#98A7DD]/20 bg-gradient-to-r from-[#282545]/60 to-[#282545]/40 backdrop-blur-sm cursor-move"
                onMouseDown={handleMouseDown}
              >
                <div className="px-6 py-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Button
                      onClick={() => setShowSidebar(!showSidebar)}
                      variant="ghost"
                      size="icon"
                      className="h-10 w-10 text-[#98A7DD] hover:text-[#FFD8A9] space-warp cursor-pointer"
                    >
                      <Menu className="w-5 h-5" />
                    </Button>
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#FF914D]/20 to-[#FFD8A9]/20 flex items-center justify-center glow-pulse">
                      <img 
                        src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/logo-VU3ODJoqYZG46efDeEvqdHHNA1ntpv.png"
                        alt="Lyra"
                        className="w-10 h-10 object-contain"
                      />
                    </div>
                    <div>
                      <h1 className="text-2xl font-bold text-[#FFD8A9]">Lyra</h1>
                      <p className="text-xs text-[#98A7DD]">
                        {isCallMode ? `En llamada - ${formatDuration(callDuration)}` : 'Asistente Astrofísico IA'}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Button
                      onClick={() => router.push('/')}
                      variant="outline"
                      size="icon"
                      className="space-warp h-10 w-10 border-[#98A7DD]/30 bg-[#282545]/70 hover:bg-[#FF914D] hover:border-[#FF914D] text-[#FFD8A9] hover:text-[#0C0B18] backdrop-blur-sm cursor-pointer"
                      title="Regresar a inicio"
                    >
                      <Home className="w-5 h-5" />
                    </Button>
                    <Button
                      onClick={toggleCallMode}
                      variant="outline"
                      size="icon"
                      className={`space-warp h-10 w-10 border-[#98A7DD]/30 backdrop-blur-sm transition-all cursor-pointer ${
                        isCallMode 
                          ? 'bg-[#FF914D] border-[#FF914D] text-[#0C0B18]' 
                          : 'bg-[#282545]/70 hover:bg-[#FF914D] text-[#FFD8A9] hover:text-[#0C0B18]'
                      }`}
                    >
                      {isCallMode ? <PhoneOff className="w-5 h-5" /> : <Phone className="w-5 h-5" />}
                    </Button>
                    <Button
                      onClick={() => setIsMinimized(true)}
                      variant="outline"
                      size="icon"
                      className="space-warp h-10 w-10 border-[#98A7DD]/30 bg-[#282545]/70 hover:bg-[#FF914D] hover:border-[#FF914D] text-[#FFD8A9] hover:text-[#0C0B18] backdrop-blur-sm cursor-pointer"
                    >
                      <Minimize2 className="w-5 h-5" />
                    </Button>
                  </div>
                </div>
              </header>

              {isCallMode && (
                <div className="absolute inset-0 z-30 bg-[#0C0B18]/95 backdrop-blur-xl flex flex-col items-center justify-center fade-blur-in">
                  <div className="text-center space-y-8 w-full max-w-2xl px-6">
                    <div className="relative">
                      <div className={`w-40 h-40 rounded-full bg-gradient-to-br from-[#FF914D]/30 to-[#FFD8A9]/30 flex items-center justify-center glow-pulse shadow-2xl transition-all duration-300 ${
                        callState === 'speaking' ? 'scale-110' : callState === 'processing' ? 'scale-105' : ''
                      }`}>
                        <img 
                          src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/logo-VU3ODJoqYZG46efDeEvqdHHNA1ntpv.png"
                          alt="Lyra"
                          className="w-32 h-32 object-contain"
                        />
                      </div>
                      {/* Audio level visualization */}
                      <div className="absolute -bottom-4 left-1/2 transform -translate-x-1/2 flex gap-1 items-end justify-center h-6">
                        {[...Array(5)].map((_, i) => {
                          const level = Math.max(0.1, audioLevel * (i + 1) / 5)
                          return (
                            <div
                              key={i}
                              className="w-1 bg-[#FF914D] rounded-full transition-all duration-100"
                              style={{
                                height: `${level * 24}px`,
                                opacity: level > 0.1 ? 1 : 0.3
                              }}
                            />
                          )
                        })}
                      </div>
                    </div>

                    <div>
                      <h2 className="text-3xl font-bold text-[#FFD8A9] mb-2">
                        {callState === 'connecting' && 'Conectando...'}
                        {callState === 'connected' && 'Conectado'}
                        {callState === 'listening' && 'Lyra está escuchando'}
                        {callState === 'speaking' && 'Lyra está hablando'}
                        {callState === 'processing' && 'Procesando...'}
                        {callState === 'error' && 'Error de conexión'}
                      </h2>
                      <p className="text-[#98A7DD] text-lg">{formatDuration(callDuration)}</p>
                      {callState === 'error' && (
                        <p className="text-red-400 text-sm mt-2">Intenta reconectar o verifica tu conexión</p>
                      )}
                    </div>

                    {/* Volume control */}
                    <div className="flex items-center gap-4 w-full max-w-xs mx-auto">
                      <MicOff className="w-4 h-4 text-[#98A7DD]" />
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.01"
                        value={volume}
                        onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                        className="flex-1 h-2 bg-[#282545] rounded-lg appearance-none cursor-pointer accent-[#FF914D]"
                      />
                      <Mic className="w-4 h-4 text-[#98A7DD]" />
                    </div>

                    <div className="flex gap-4 justify-center">
                      <Button
                        onClick={handleMuteToggle}
                        variant="outline"
                        size="icon"
                        className={`space-warp h-14 w-14 rounded-full border-[#98A7DD]/30 backdrop-blur-sm transition-all ${
                          isMuted 
                            ? 'bg-red-500/20 border-red-500 text-red-500' 
                            : 'bg-[#282545]/70 text-[#FFD8A9] hover:bg-[#282545]'
                        }`}
                      >
                        {isMuted ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
                      </Button>
                      
                      {(callState === 'speaking' || callState === 'processing') && (
                        <Button
                          onClick={handleInterrupt}
                          variant="outline"
                          size="icon"
                          className="space-warp h-14 w-14 rounded-full border-orange-500/30 bg-orange-500/20 text-orange-400 hover:bg-orange-500/30"
                          title="Interrumpir respuesta"
                        >
                          <X className="w-6 h-6" />
                        </Button>
                      )}
                      
                      <Button
                        onClick={toggleCallMode}
                        size="icon"
                        className="space-warp h-14 w-14 rounded-full bg-red-500 hover:bg-red-600 text-white transition-all"
                      >
                        <PhoneOff className="w-6 h-6" />
                      </Button>
                    </div>

                    <p className="text-sm text-[#98A7DD] max-w-md mx-auto">
                      {callState === 'listening' && 'Habla claramente sobre tus preguntas de astrofísica. Lyra procesará tu voz en tiempo real.'}
                      {callState === 'speaking' && 'Escuchando la respuesta de Lyra...'}
                      {callState === 'processing' && 'Procesando tu mensaje...'}
                      {callState === 'connecting' && 'Estableciendo conexión...'}
                      {callState === 'connected' && 'Conexión establecida. Puedes comenzar a hablar.'}
                    </p>
                  </div>
                </div>
              )}

              <main className="flex-1 overflow-y-auto px-6 py-6">
                <div className="space-y-4">
                  {messages.map((message, index) => {
                    // Ensure unique key - use ID if available, otherwise generate one with index and random component
                    const uniqueKey = message.id || `${message.timestamp.getTime()}-${index}-${message.role}-${Math.random().toString(36).substr(2, 9)}`
                    return (
                    <div
                      key={uniqueKey}
                      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} fade-blur-in`}
                      style={{ animationDelay: `${index * 0.1}s` }}
                    >
                      <Card className={`max-w-[85%] p-4 tilt-card backdrop-blur-md ${
                        message.role === 'user' 
                          ? 'bg-[#FF914D]/90 text-[#0C0B18] border-[#FFD8A9]/30' 
                          : 'bg-[#282545]/70 text-[#FFD8A9] border-[#98A7DD]/30'
                      }`}>
                        <div className="text-sm leading-relaxed prose prose-invert prose-headings:text-[#FFD8A9] prose-p:text-[#FFD8A9] prose-strong:text-[#FFD8A9] prose-code:text-[#FF914D] prose-pre:bg-[#0C0B18]/50 prose-pre:text-[#FFD8A9] prose-a:text-[#98A7DD] prose-a:hover:text-[#FF914D] max-w-none">
                          {message.role === 'assistant' ? (
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {message.content}
                            </ReactMarkdown>
                          ) : (
                            <div className="whitespace-pre-wrap">{message.content}</div>
                          )}
                        </div>
                        <div className={`text-xs mt-2 ${
                          message.role === 'user' ? 'text-[#0C0B18]/70' : 'text-[#98A7DD]'
                        }`}>
                          {message.timestamp.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </Card>
                    </div>
                    )
                  })}

                  {isLoading && (
                    <div className="flex justify-start fade-blur-in">
                      <Card className="max-w-[85%] p-4 bg-[#282545]/70 border-[#98A7DD]/30 backdrop-blur-md">
                        <div className="flex items-center gap-2 text-[#98A7DD]">
                          <div className="flex gap-1">
                            <span className="w-2 h-2 bg-[#FF914D] rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
                            <span className="w-2 h-2 bg-[#FF914D] rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                            <span className="w-2 h-2 bg-[#FF914D] rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
                          </div>
                          <span className="text-sm">Lyra está pensando...</span>
                        </div>
                      </Card>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              </main>

              <div className="border-t border-[#98A7DD]/20 bg-gradient-to-r from-[#282545]/60 to-[#282545]/40 backdrop-blur-sm">
                <div className="px-6 py-4">
                  <div className="flex items-end gap-2">
                    <label htmlFor="file-upload">
                      <Button
                        type="button"
                        variant="outline"
                        size="icon"
                        className="space-warp h-12 w-12 border-[#98A7DD]/30 bg-[#282545]/70 hover:bg-[#FF914D] hover:border-[#FF914D] text-[#FFD8A9] hover:text-[#0C0B18] backdrop-blur-sm cursor-pointer"
                        asChild
                      >
                        <span>
                          <Upload className="w-5 h-5" />
                        </span>
                      </Button>
                      <input
                        id="file-upload"
                        type="file"
                        accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp"
                        className="hidden"
                        onChange={handleFileUpload}
                      />
                    </label>
                    
                    <div className="flex-1 relative">
                      <Input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Pregúntame sobre agujeros negros, galaxias o fenómenos astrofísicos..."
                        className="h-12 bg-[#282545]/70 border-[#98A7DD]/30 text-[#FFD8A9] placeholder:text-[#98A7DD]/60 pr-4 focus:ring-[#FF914D] focus:border-[#FF914D] backdrop-blur-sm"
                      />
                    </div>

                    <Button
                      onClick={handleSend}
                      disabled={!input.trim() || isLoading}
                      className="space-warp glow-pulse h-12 px-6 bg-[#FF914D] hover:bg-[#FF914D]/90 text-[#0C0B18] font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Send className="w-5 h-5" />
                    </Button>
                  </div>
                  
                  <p className="text-xs text-[#98A7DD] mt-2 text-center">
                    Lyra puede analizar PDFs, imágenes y artículos científicos sobre astrofísica
                  </p>
                </div>
              </div>
            </div>

            <div
              className="absolute bottom-0 right-0 w-6 h-6 cursor-nwse-resize z-50"
              onMouseDown={handleResizeMouseDown}
            >
              <div className="absolute bottom-2 right-2 w-4 h-4 border-r-2 border-b-2 border-[#98A7DD]/50 hover:border-[#FF914D] transition-colors" />
            </div>
          </div>
        </div>
      )}

      {/* Astronomy Data Dashboard - Visible when chatbot is minimized */}
      {isMinimized && (
        <div className="fixed inset-0 z-20 overflow-y-auto">
          <div className="min-h-screen w-full bg-gradient-to-b from-[#0C0B18] via-[#1a1830] to-[#0C0B18]">
            
            {/* Hero Section */}
            <div className="relative py-16 px-6 overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-b from-[#FF914D]/5 via-transparent to-transparent" />
              <div className="max-w-7xl mx-auto text-center space-y-4 relative z-10 fade-blur-in">
                <h1 className="text-5xl md:text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-[#FF914D] via-[#FFD8A9] to-[#FF914D] animate-gradient">
                  Space Intelligence Hub
                </h1>
                <p className="text-xl text-[#98A7DD] max-w-3xl mx-auto leading-relaxed">
                  Real-time astronomical data, breaking space news, and cutting-edge research — all in one place
                </p>
              </div>
            </div>

            {/* Alerts Banner - Full Width */}
            <div className="w-full px-6 mb-12 fade-blur-in" style={{ animationDelay: '0.1s' }}>
              <div className="max-w-7xl mx-auto">
                <AstroAlerts />
              </div>
            </div>

            {/* News Section - Dedicated Full-Width Area */}
            <div className="w-full bg-[#0C0B18]/50 backdrop-blur-sm border-y border-[#98A7DD]/10 py-16 px-6 fade-blur-in" style={{ animationDelay: '0.2s' }}>
              <div className="max-w-7xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                  <div>
                    <h2 className="text-3xl md:text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-[#FF914D] to-[#FFD8A9]">
                      🌌 Latest Space News
                    </h2>
                    <p className="text-[#98A7DD] mt-2">Breaking stories from across the cosmos</p>
                  </div>
                </div>
                <NewsGrid />
              </div>
            </div>

            {/* Astronomical Data Section - Two Column Layout */}
            <div className="w-full py-16 px-6">
              <div className="max-w-7xl mx-auto">
                <div className="text-center mb-12 fade-blur-in" style={{ animationDelay: '0.3s' }}>
                  <h2 className="text-3xl md:text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-[#98A7DD] to-[#FFD8A9]">
                    🔭 Scientific Data & Research
                  </h2>
                  <p className="text-[#98A7DD] mt-2">Today's discoveries and observations</p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
                  {/* Astronomy Image of the Day */}
                  <div className="space-y-6 fade-blur-in" style={{ animationDelay: '0.4s' }}>
                    <div className="flex items-center gap-3">
                      <div className="w-1 h-8 bg-gradient-to-b from-[#FF914D] to-[#FFD8A9] rounded-full" />
                      <h3 className="text-2xl font-bold text-[#FFD8A9]">Image of the Day</h3>
                    </div>
                    <AstronomyImage />
                  </div>

                  {/* Research Papers */}
                  <div className="space-y-6 fade-blur-in" style={{ animationDelay: '0.5s' }}>
                    <div className="flex items-center gap-3">
                      <div className="w-1 h-8 bg-gradient-to-b from-[#98A7DD] to-[#FFD8A9] rounded-full" />
                      <h3 className="text-2xl font-bold text-[#FFD8A9]">Recent Publications</h3>
                    </div>
                    <ResearchPapers />
                  </div>
                </div>
              </div>
            </div>

            {/* CTA Footer */}
            <div className="w-full bg-gradient-to-t from-[#0C0B18] via-[#1a1830]/50 to-transparent py-20 px-6 fade-blur-in" style={{ animationDelay: '0.6s' }}>
              <div className="max-w-4xl mx-auto text-center space-y-6">
                <h3 className="text-3xl font-bold text-[#FFD8A9]">
                  Want to know more?
                </h3>
                <p className="text-lg text-[#98A7DD]">
                  Ask Lyra anything about these topics and get detailed, AI-powered explanations
                </p>
                <Button
                  onClick={() => setIsMinimized(false)}
                  className="px-10 py-7 text-xl bg-gradient-to-r from-[#FF914D] to-[#FFD8A9] hover:from-[#FF914D]/90 hover:to-[#FFD8A9]/90 text-[#0C0B18] font-bold space-warp glow-pulse shadow-2xl"
                >
                  💬 Open Chat with Lyra
                </Button>
              </div>
            </div>

          </div>
        </div>
      )}
    </>
  )
}

