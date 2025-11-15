/**
 * Audio Worklet Processor for capturing and processing microphone audio.
 */

class AudioProcessor extends AudioWorkletProcessor {
  constructor() {
    super()
    this.bufferSize = 4096
    this.buffer = new Float32Array(this.bufferSize)
    this.bufferIndex = 0
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0]
    
    if (input.length > 0) {
      const inputChannel = input[0]
      
      // Copy input samples to buffer
      for (let i = 0; i < inputChannel.length; i++) {
        this.buffer[this.bufferIndex++] = inputChannel[i]
        
        // When buffer is full, send it
        if (this.bufferIndex >= this.bufferSize) {
          // Create a copy of the buffer
          const audioData = new Float32Array(this.buffer)
          
          // Send to main thread
          this.port.postMessage({
            type: 'audio',
            audioData: audioData.buffer
          }, [audioData.buffer])
          
          // Reset buffer
          this.bufferIndex = 0
        }
      }
    }
    
    return true
  }
}

registerProcessor('audio-processor', AudioProcessor)

