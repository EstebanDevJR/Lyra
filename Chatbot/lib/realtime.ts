/**
 * OpenAI Realtime API client for voice conversations.
 */

import logger from './logger'

export interface RealtimeMessage {
  type: string
  [key: string]: any
}

export interface RealtimeCallbacks {
  onTranscript?: (text: string, role: 'user' | 'assistant') => void
  onMessage?: (text: string) => void // For partial text updates (deltas)
  onAudio?: (audioData: ArrayBuffer) => void
  onError?: (error: Error) => void
  onClose?: () => void
  onStateChange?: (state: 'connecting' | 'connected' | 'listening' | 'speaking' | 'processing' | 'error') => void
  onAudioLevel?: (level: number) => void // Audio level for visualization (0-1)
}

export class RealtimeClient {
  private ws: WebSocket | null = null
  private audioContext: AudioContext | null = null // Audio context for capture
  private playbackAudioContext: AudioContext | null = null // Separate audio context for playback
  private mediaStream: MediaStream | null = null
  private audioWorkletNode: AudioWorkletNode | null = null
  private analyserNode: AnalyserNode | null = null
  private isConnected = false
  private callbacks: RealtimeCallbacks = {}
  private baseUrl: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private currentState: 'connecting' | 'connected' | 'listening' | 'speaking' | 'processing' | 'error' = 'connecting'
  private audioLevelInterval: number | null = null
  private isSpeaking = false
  private volumeGainNode: GainNode | null = null
  private audioQueue: Float32Array[] = []
  private isPlayingAudio = false
  private audioDestinationNode: AudioDestinationNode | null = null
  private audioSourceNode: AudioBufferSourceNode | null = null
  private isManuallyDisconnected = false // Track if user manually disconnected

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl.replace('http://', 'ws://').replace('https://', 'wss://')
  }

  /**
   * Connect to the realtime WebSocket endpoint.
   */
  async connect(callbacks: RealtimeCallbacks = {}): Promise<void> {
    if (this.isConnected) {
      throw new Error('Already connected')
    }

    this.callbacks = callbacks

    try {
      const wsUrl = `${this.baseUrl}/ws/realtime`
      logger.info('Connecting to Realtime API', { url: wsUrl })
      
      this.ws = new WebSocket(wsUrl)

      // Set up message handler before connection opens
      this.ws.onmessage = (event) => {
        try {
          logger.debug('WebSocket message received', { 
            type: typeof event.data, 
            length: typeof event.data === 'string' ? event.data.length : 'N/A'
          })
          this.handleMessage(event.data)
        } catch (error) {
          logger.error('Error in onmessage handler', error)
        }
      }

      // Wait for connection to be established and send start message
      await new Promise<void>((resolve, reject) => {
        if (!this.ws) {
          reject(new Error('WebSocket not initialized'))
          return
        }

        const timeout = setTimeout(() => {
          reject(new Error('Connection timeout'))
        }, 10000)

      this.ws.onopen = () => {
        clearTimeout(timeout)
        logger.info('Realtime WebSocket connected')
        this.isConnected = true
        // Reset reconnect attempts and manual disconnect flag on successful connection
        this.reconnectAttempts = 0
        this.isManuallyDisconnected = false
        
        // Send start message to backend immediately after connection is established
        try {
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'start', action: 'start' }))
            logger.debug('Start message sent to backend')
          }
        } catch (error) {
          logger.error('Error sending start message', error)
          reject(error)
          return
        }
        
        this.setState('connected')
        resolve()
      }

        this.ws.onerror = (error) => {
          clearTimeout(timeout)
          logger.error('Realtime WebSocket error', error)
          this.setState('error')
          this.callbacks.onError?.(new Error('WebSocket error'))
          reject(error)
        }

      this.ws.onclose = (event) => {
        logger.info('Realtime WebSocket closed', { code: event.code, reason: event.reason })
        this.isConnected = false
        this.setState('error')
        
        // Only attempt reconnection if not manually disconnected and not a normal closure
        if (!this.isManuallyDisconnected && event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.attemptReconnect()
        } else {
          this.callbacks.onClose?.()
        }
      }
      })

    } catch (error) {
      logger.error('Error connecting to Realtime API', error)
      throw error
    }
  }

  /**
   * Start audio capture and streaming.
   */
  async startAudio(): Promise<void> {
    try {
      // Request microphone access with optimal settings for speech
      try {
        this.mediaStream = await navigator.mediaDevices.getUserMedia({
          audio: {
            channelCount: 1,
            sampleRate: 24000,
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            latency: 0
          }
        })
      } catch (err) {
        logger.warn('Failed to get optimal audio settings, trying basic settings', err)
        // Fallback to basic settings
        this.mediaStream = await navigator.mediaDevices.getUserMedia({
          audio: true
        })
      }

      // Create audio context
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 })

      // Try to load audio worklet processor, fallback to ScriptProcessorNode if not available
      try {
        await this.audioContext.audioWorklet.addModule('/audio-processor.js')
        
        // Create audio worklet node
        this.audioWorkletNode = new AudioWorkletNode(this.audioContext, 'audio-processor')

        // Handle audio data from worklet
        this.audioWorkletNode.port.onmessage = (event) => {
          if (event.data.type === 'audio') {
            this.sendAudio(event.data.audioData)
          }
        }

        // Create analyser for audio level visualization
        this.analyserNode = this.audioContext.createAnalyser()
        this.analyserNode.fftSize = 256
        this.analyserNode.smoothingTimeConstant = 0.8
        
        // Create gain node for volume control
        this.volumeGainNode = this.audioContext.createGain()
        this.volumeGainNode.gain.value = 1.0
        
        // Connect microphone to worklet
        const source = this.audioContext.createMediaStreamSource(this.mediaStream)
        source.connect(this.audioWorkletNode)
        
        // Also connect to analyser for visualization
        source.connect(this.analyserNode)
        
        // Start monitoring audio levels
        this.startAudioLevelMonitoring()
      } catch (workletError) {
        // Fallback to ScriptProcessorNode for browsers that don't support AudioWorklet
        logger.warn('AudioWorklet not available, using ScriptProcessorNode', workletError)
        
        // Create analyser for audio level visualization
        this.analyserNode = this.audioContext.createAnalyser()
        this.analyserNode.fftSize = 256
        this.analyserNode.smoothingTimeConstant = 0.8
        
        // Create gain node for volume control
        this.volumeGainNode = this.audioContext.createGain()
        this.volumeGainNode.gain.value = 1.0
        
        const source = this.audioContext.createMediaStreamSource(this.mediaStream)
        const processor = this.audioContext.createScriptProcessor(4096, 1, 1)
        
        processor.onaudioprocess = (e) => {
          const inputData = e.inputBuffer.getChannelData(0)
          const audioData = new Float32Array(inputData)
          this.sendAudio(audioData.buffer)
        }
        
        source.connect(processor)
        source.connect(this.analyserNode)
        processor.connect(this.audioContext.destination)
        
        // Start monitoring audio levels
        this.startAudioLevelMonitoring()
      }

      logger.info('Audio capture started')

    } catch (error) {
      logger.error('Error starting audio capture', error)
      throw error
    }
  }

  /**
   * Stop audio capture.
   */
  stopAudio(): void {
    this.stopAudioLevelMonitoring()
    
    // Clear audio queue
    this.audioQueue = []
    this.isPlayingAudio = false
    
    // Stop current audio source if playing
    if (this.audioSourceNode) {
      try {
        this.audioSourceNode.stop()
      } catch (e) {
        // Ignore if already stopped
      }
      this.audioSourceNode = null
    }
    
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop())
      this.mediaStream = null
    }

    if (this.audioWorkletNode) {
      this.audioWorkletNode.disconnect()
      this.audioWorkletNode = null
    }
    
    if (this.analyserNode) {
      this.analyserNode.disconnect()
      this.analyserNode = null
    }
    
    if (this.volumeGainNode) {
      this.volumeGainNode.disconnect()
      this.volumeGainNode = null
    }

    // Don't close audio context if it's being used for playback
    // Only close if we're completely stopping everything
    logger.info('Audio capture stopped')
  }
  
  /**
   * Set volume (0.0 to 1.0).
   */
  setVolume(volume: number): void {
    const clampedVolume = Math.max(0, Math.min(1, volume))
    
    // Ensure playback audio context exists
    if (!this.playbackAudioContext) {
      this.playbackAudioContext = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 })
      this.audioDestinationNode = this.playbackAudioContext.destination
    }
    
    // Create volume gain node if it doesn't exist
    if (!this.volumeGainNode || this.volumeGainNode.context !== this.playbackAudioContext) {
      this.volumeGainNode = this.playbackAudioContext.createGain()
      this.volumeGainNode.connect(this.audioDestinationNode || this.playbackAudioContext.destination)
    }
    
    if (this.volumeGainNode) {
      this.volumeGainNode.gain.value = clampedVolume
      logger.info('Volume set to', clampedVolume)
    }
  }
  
  /**
   * Get current volume.
   */
  getVolume(): number {
    return this.volumeGainNode?.gain.value ?? 1.0
  }
  
  /**
   * Start monitoring audio levels for visualization.
   */
  private startAudioLevelMonitoring(): void {
    if (this.audioLevelInterval) {
      return
    }
    
    const dataArray = new Uint8Array(this.analyserNode?.frequencyBinCount ?? 0)
    
    const updateLevel = () => {
      if (!this.analyserNode) return
      
      this.analyserNode.getByteFrequencyData(dataArray)
      
      // Calculate average volume
      let sum = 0
      for (let i = 0; i < dataArray.length; i++) {
        sum += dataArray[i]
      }
      const average = sum / dataArray.length
      const normalizedLevel = average / 255
      
      this.callbacks.onAudioLevel?.(normalizedLevel)
      
      this.audioLevelInterval = requestAnimationFrame(updateLevel) as any
    }
    
    updateLevel()
  }
  
  /**
   * Stop monitoring audio levels.
   */
  private stopAudioLevelMonitoring(): void {
    if (this.audioLevelInterval) {
      cancelAnimationFrame(this.audioLevelInterval)
      this.audioLevelInterval = null
    }
  }
  
  /**
   * Attempt to reconnect to the WebSocket.
   */
  private async attemptReconnect(): Promise<void> {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      logger.error('Max reconnection attempts reached')
      this.callbacks.onError?.(new Error('Max reconnection attempts reached'))
      return
    }
    
    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1) // Exponential backoff
    
    logger.info(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`)
    this.setState('connecting')
    
    await new Promise(resolve => setTimeout(resolve, delay))
    
    try {
      await this.connect(this.callbacks)
      await this.startAudio()
    } catch (error) {
      logger.error('Reconnection failed', error)
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        await this.attemptReconnect()
      } else {
        this.callbacks.onError?.(new Error('Failed to reconnect'))
      }
    }
  }
  
  /**
   * Set connection state and notify callbacks.
   */
  private setState(state: 'connecting' | 'connected' | 'listening' | 'speaking' | 'processing' | 'error'): void {
    if (this.currentState !== state) {
      this.currentState = state
      this.callbacks.onStateChange?.(state)
    }
  }

  /**
   * Send audio data to the server.
   */
  private sendAudio(audioData: ArrayBuffer): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      // Convert Float32Array to Int16Array (PCM16)
      const float32Data = new Float32Array(audioData)
      const int16Data = new Int16Array(float32Data.length)
      
      for (let i = 0; i < float32Data.length; i++) {
        // Clamp and convert to 16-bit integer
        const sample = Math.max(-1, Math.min(1, float32Data[i]))
        int16Data[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF
      }

      // Send as base64 encoded audio
      const base64Audio = this.arrayBufferToBase64(int16Data.buffer)
      
      const message = {
        type: 'input_audio_buffer.append',
        audio: base64Audio
      }

      this.ws.send(JSON.stringify(message))
    }
  }

  /**
   * Send a text message.
   */
  sendMessage(text: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = {
        type: 'conversation.item.create',
        item: {
          type: 'message',
          role: 'user',
          content: text
        }
      }
      this.ws.send(JSON.stringify(message))
    }
  }

  /**
   * Request response generation.
   */
  requestResponse(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = {
        type: 'response.create'
      }
      this.ws.send(JSON.stringify(message))
    }
  }

  /**
   * Handle incoming WebSocket messages.
   */
  private handleMessage(data: string | ArrayBuffer): void {
    try {
      if (typeof data === 'string') {
        const message: RealtimeMessage = JSON.parse(data)
        logger.debug('Parsed WebSocket message', { type: message.type })
        this.handleRealtimeMessage(message)
      } else {
        // Binary audio data (shouldn't happen with OpenAI Realtime API, but handle it)
        logger.debug('Received binary data (unexpected)')
        this.callbacks.onAudio?.(data)
      }
    } catch (error) {
      logger.error('Error handling message', error, { 
        dataType: typeof data, 
        dataLength: typeof data === 'string' ? data.length : 'N/A' 
      })
    }
  }

  /**
   * Handle Realtime API messages.
   */
  private handleRealtimeMessage(message: RealtimeMessage): void {
    switch (message.type) {
      case 'session.created':
        logger.info('Session created', message)
        break

      case 'session.updated':
        logger.info('Session updated', message)
        break

      case 'conversation.item.input_audio_transcription.completed':
        // User speech transcribed
        const transcript = message.transcript
        if (transcript) {
          logger.info('User transcript received', { transcript })
          
          // If assistant is speaking, interrupt it
          // Only interrupt if the transcript is substantial to avoid false positives from echo
          if (this.isSpeaking && transcript.trim().length > 2) {
            logger.info('User spoke while assistant was speaking, interrupting...', { transcript })
            this.interrupt()
          }
          
          this.setState('processing')
          this.callbacks.onTranscript?.(transcript, 'user')
        }
        break

      case 'response.audio_transcript.delta':
        // Assistant speech transcript (partial)
        const delta = message.delta
        if (delta) {
          logger.info('Response transcript delta', { delta })
          this.callbacks.onMessage?.(delta)
        }
        break

      case 'response.audio_transcript.done':
        // Assistant speech transcript (complete)
        const transcript_done = message.transcript
        if (transcript_done) {
          logger.info('Assistant transcript complete', { transcript: transcript_done })
          this.callbacks.onTranscript?.(transcript_done, 'assistant')
        }
        break

      case 'response.audio.delta':
        // Audio data from assistant
        logger.info('response.audio.delta message received', { hasDelta: !!message.delta, deltaLength: message.delta?.length || 0 })
        if (message.delta) {
          if (!this.isSpeaking) {
            this.isSpeaking = true
            this.setState('speaking')
            logger.info('Started receiving audio deltas from assistant', { deltaLength: message.delta?.length || 0 })
            // Ensure playback audio context is resumed when we start receiving audio
            if (this.playbackAudioContext && this.playbackAudioContext.state === 'suspended') {
              this.playbackAudioContext.resume().then(() => {
                logger.info('Playback audio context resumed for first audio delta')
              }).catch(err => {
                logger.error('Failed to resume playback audio context', err)
              })
            } else if (!this.playbackAudioContext) {
              // Create separate playback audio context if it doesn't exist
              this.playbackAudioContext = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 })
              this.audioDestinationNode = this.playbackAudioContext.destination
              logger.info('Created new playback audio context for first audio delta')
            }
          }
          logger.info('Calling handleAudioDelta', { deltaLength: message.delta?.length || 0 })
          this.handleAudioDelta(message.delta)
        } else {
          logger.warn('response.audio.delta received but delta is empty or missing', { message })
        }
        break

      case 'response.done':
        logger.info('Response done', message)
        this.isSpeaking = false
        // Don't change state if we're processing user input
        if (this.currentState !== 'processing') {
          this.setState('listening')
        }
        break
        
      case 'response.audio_transcript.delta':
        // Partial transcript update
        if (message.delta) {
          // Could show partial transcripts if needed
          logger.debug('Partial transcript delta', { delta: message.delta })
        }
        break

      case 'error':
        logger.error('Realtime API error', message)
        this.callbacks.onError?.(new Error(message.error || 'Unknown error'))
        break

      default:
        logger.debug('Unhandled message type', { type: message.type })
    }
  }

  /**
   * Handle audio delta from assistant.
   */
  private handleAudioDelta(base64Audio: string): void {
    try {
      if (!base64Audio || base64Audio.length === 0) {
        logger.warn('Empty audio delta received')
        return
      }

      logger.info('Processing audio delta', { length: base64Audio.length })
      
      // Decode base64 audio
      const binaryString = atob(base64Audio)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }

      // Convert Int16 PCM to Float32
      // Note: bytes.buffer might not be aligned for Int16Array, so we need to create a new buffer
      // PCM16 is little-endian, so we need to read bytes in pairs
      const int16Buffer = new ArrayBuffer(bytes.length)
      const int16View = new Int8Array(int16Buffer)
      int16View.set(bytes)
      
      // Create Int16Array view (little-endian by default in JavaScript)
      const int16Data = new Int16Array(int16Buffer)
      const float32Data = new Float32Array(int16Data.length)
      
      // Convert Int16 (-32768 to 32767) to Float32 (-1.0 to 1.0)
      for (let i = 0; i < int16Data.length; i++) {
        float32Data[i] = int16Data[i] / 32768.0
      }
      
      // Verify we have valid audio data (not all zeros or NaN)
      const hasValidData = float32Data.some(sample => Math.abs(sample) > 0.001)
      if (!hasValidData) {
        logger.warn('Audio delta contains only zeros or invalid data')
      }

      logger.info('Audio delta decoded', { samples: float32Data.length, maxSample: Math.max(...Array.from(float32Data.map(Math.abs))).toFixed(4) })
      
      // Add to queue instead of playing immediately
      this.queueAudio(float32Data)

    } catch (error) {
      logger.error('Error handling audio delta', error)
    }
  }

  /**
   * Queue audio data for sequential playback.
   * Combines small chunks to reduce audio glitches.
   */
  private queueAudio(audioData: Float32Array): void {
    // Use separate audio context for playback to avoid conflicts with capture
    if (!this.playbackAudioContext || this.playbackAudioContext.state === 'closed') {
      // Create new context specifically for playback
      this.playbackAudioContext = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 })
      this.audioDestinationNode = this.playbackAudioContext.destination
      logger.info('Created separate playback audio context', { sampleRate: 24000 })
    }

    // Resume context if suspended (browser autoplay policy)
    if (this.playbackAudioContext.state === 'suspended') {
      this.playbackAudioContext.resume().then(() => {
        logger.info('Playback audio context resumed', { state: this.playbackAudioContext?.state })
      }).catch(err => {
        logger.error('Failed to resume playback audio context', err)
      })
    }

    // Ensure destination node exists
    if (!this.audioDestinationNode) {
      this.audioDestinationNode = this.playbackAudioContext.destination
    }

    // Create or reconnect volume gain node for playback
    if (!this.volumeGainNode || this.volumeGainNode.context !== this.playbackAudioContext) {
      this.volumeGainNode = this.playbackAudioContext.createGain()
      this.volumeGainNode.gain.value = 1.0
      this.volumeGainNode.connect(this.audioDestinationNode)
      logger.info('Volume gain node created/connected in queueAudio', { 
        gainValue: this.volumeGainNode.gain.value,
        contextState: this.playbackAudioContext.state,
        destinationConnected: this.volumeGainNode.numberOfOutputs > 0
      })
    } else {
      // Ensure gain is not 0
      if (this.volumeGainNode.gain.value === 0) {
        logger.warn('Volume gain is 0 in queueAudio, setting to 1.0')
        this.volumeGainNode.gain.value = 1.0
      }
    }

    // Combine small chunks to reduce audio glitches
    // If the last chunk in queue is small (< 9600 samples = 400ms at 24kHz), combine with new chunk
    // Increased from 200ms to 400ms to buffer more audio before playing
    const MIN_CHUNK_SIZE = 9600 // 400ms at 24kHz
    if (this.audioQueue.length > 0 && this.audioQueue[this.audioQueue.length - 1].length < MIN_CHUNK_SIZE) {
      const lastChunk = this.audioQueue.pop()!
      const combined = new Float32Array(lastChunk.length + audioData.length)
      combined.set(lastChunk, 0)
      combined.set(audioData, lastChunk.length)
      this.audioQueue.push(combined)
      logger.debug('Combined small audio chunks', { 
        lastChunkSize: lastChunk.length, 
        newChunkSize: audioData.length,
        combinedSize: combined.length 
      })
    } else {
      // Add to queue
      this.audioQueue.push(audioData)
    }
    
    logger.debug('Audio chunk queued', { queueLength: this.audioQueue.length, dataLength: audioData.length })

    // Start playing if not already playing
    if (!this.isPlayingAudio) {
      logger.info('Starting audio queue processing')
      this.processAudioQueue()
    }
  }

  /**
   * Process audio queue sequentially.
   */
  private async processAudioQueue(): Promise<void> {
    if (this.isPlayingAudio || this.audioQueue.length === 0) {
      return
    }

    this.isPlayingAudio = true
    logger.info('Starting audio queue processing', { queueLength: this.audioQueue.length })

    // Ensure playback audio context is ready
    if (this.playbackAudioContext && this.playbackAudioContext.state === 'suspended') {
      try {
        await this.playbackAudioContext.resume()
        logger.debug('Playback audio context resumed for queue processing')
      } catch (err) {
        logger.warn('Failed to resume playback audio context', err)
      }
    }

    while (this.audioQueue.length > 0 && this.isPlayingAudio) {
      const audioData = this.audioQueue.shift()
      if (!audioData || audioData.length === 0) {
        continue
      }

      try {
        await this.playAudioChunk(audioData)
        logger.debug('Audio chunk played', { remaining: this.audioQueue.length })
      } catch (error) {
        logger.error('Error playing audio chunk', error)
        // Continue with next chunk even if one fails
      }
    }

    this.isPlayingAudio = false
    logger.info('Audio queue processing completed', { remaining: this.audioQueue.length })
  }

  /**
   * Play a single audio chunk.
   */
  private playAudioChunk(audioData: Float32Array): Promise<void> {
    return new Promise(async (resolve, reject) => {
      try {
        // Use separate playback audio context
        if (!this.playbackAudioContext) {
          this.playbackAudioContext = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 })
          this.audioDestinationNode = this.playbackAudioContext.destination
          logger.info('Created playback audio context in playAudioChunk')
        }

        // Resume audio context if suspended (required by browser autoplay policy)
        // This MUST be awaited to ensure context is ready before playing
        if (this.playbackAudioContext.state === 'suspended') {
          await this.playbackAudioContext.resume()
          logger.info('Playback audio context resumed in playAudioChunk', { newState: this.playbackAudioContext.state })
        }
        
        // Verify context is running
        if (this.playbackAudioContext.state !== 'running') {
          logger.warn('Playback audio context is not running', { state: this.playbackAudioContext.state })
          // Try to resume again
          try {
            await this.playbackAudioContext.resume()
            logger.info('Playback audio context resumed after warning', { newState: this.playbackAudioContext.state })
          } catch (err) {
            logger.error('Failed to resume playback audio context', err)
          }
        }

        if (!this.audioDestinationNode) {
          this.audioDestinationNode = this.playbackAudioContext.destination
        }

        // Create audio buffer using playback context
        const audioBuffer = this.playbackAudioContext.createBuffer(1, audioData.length, 24000)
        audioBuffer.copyToChannel(audioData, 0)

        // Create source node using playback context
        const source = this.playbackAudioContext.createBufferSource()
        source.buffer = audioBuffer
        
        // Store reference to current source for interruption
        this.audioSourceNode = source

        // Ensure volume gain node exists and is connected
        if (!this.volumeGainNode || this.volumeGainNode.context !== this.playbackAudioContext) {
          this.volumeGainNode = this.playbackAudioContext.createGain()
          this.volumeGainNode.gain.value = 1.0
          this.volumeGainNode.connect(this.audioDestinationNode)
        }

        // Verify gain node is still connected
        if (this.volumeGainNode.gain.value === 0) {
          this.volumeGainNode.gain.value = 1.0
        }
        
        // Connect source through gain node to destination
        source.connect(this.volumeGainNode)

        // Handle completion
        source.onended = () => {
          // Clear reference if this is the current source
          if (this.audioSourceNode === source) {
            this.audioSourceNode = null
          }
          resolve()
        }

        // Handle errors
        source.onerror = (error) => {
          logger.error('Audio source error', error)
          // Clear reference if this is the current source
          if (this.audioSourceNode === source) {
            this.audioSourceNode = null
          }
          reject(error)
        }

        // Start playback immediately with a tiny offset to prevent overlap clicks
        // Scheduling slightly in the future allows the audio thread to catch up
        const startTime = Math.max(this.playbackAudioContext.currentTime, this.nextNoteTime || 0)
        source.start(startTime)
        
        // Update next expected start time
        this.nextNoteTime = startTime + audioBuffer.duration
        
        // If we fall too far behind, reset nextNoteTime
        if (this.nextNoteTime < this.playbackAudioContext.currentTime) {
            this.nextNoteTime = this.playbackAudioContext.currentTime
        }
        
        logger.info('Audio chunk playback started', { 
          bufferLength: audioData.length, 
          duration: audioBuffer.duration
        })

      } catch (error) {
        logger.error('Error in playAudioChunk', error)
        reject(error)
      }
    })
  }

  /**
   * Convert ArrayBuffer to base64 string.
   */
  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer)
    let binary = ''
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i])
    }
    return btoa(binary)
  }

  /**
   * Disconnect from the WebSocket.
   */
  disconnect(): void {
    // Mark as manually disconnected to prevent auto-reconnection
    this.isManuallyDisconnected = true
    this.reconnectAttempts = this.maxReconnectAttempts // Prevent reconnection attempts
    
    this.stopAudio()
    
    // Clear audio queue
    this.audioQueue = []
    this.isPlayingAudio = false
    
    // Stop any playing audio
    if (this.audioSourceNode) {
      try {
        this.audioSourceNode.stop()
      } catch (e) {
        // Ignore if already stopped
      }
      this.audioSourceNode = null
    }
    
    // Close playback audio context if it exists
    if (this.playbackAudioContext && this.playbackAudioContext.state !== 'closed') {
      this.playbackAudioContext.close()
      this.playbackAudioContext = null
    }
    
    // Close capture audio context if it exists
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close()
      this.audioContext = null
    }
    
    this.audioDestinationNode = null
    
    if (this.ws) {
      // Close with normal closure code to indicate intentional disconnect
      this.ws.close(1000, 'User disconnected')
      this.ws = null
    }

    this.isConnected = false
    logger.info('Disconnected from Realtime API')
  }

  /**
   * Check if connected.
   */
  get connected(): boolean {
    return this.isConnected && this.ws?.readyState === WebSocket.OPEN
  }
  
  /**
   * Get current state.
   */
  get state(): 'connecting' | 'connected' | 'listening' | 'speaking' | 'processing' | 'error' {
    return this.currentState
  }
  
  /**
   * Interrupt current response.
   */
  interrupt(): void {
    logger.info('Interrupting response', { isSpeaking: this.isSpeaking, queueLength: this.audioQueue.length })
    
    // Stop current audio playback
    if (this.audioSourceNode) {
      try {
        this.audioSourceNode.stop()
        logger.info('Stopped current audio source')
      } catch (e) {
        // Ignore if already stopped
      }
      this.audioSourceNode = null
    }
    
    // Clear audio queue
    this.audioQueue = []
    this.isPlayingAudio = false
    this.isSpeaking = false
    
    // Send cancel message to backend/OpenAI
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = {
        type: 'response.cancel'
      }
      this.ws.send(JSON.stringify(message))
      logger.info('Sent response.cancel message')
    }
    
    this.setState('listening')
  }
}

