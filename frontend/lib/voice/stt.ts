/**
 * Browser Speech Recognition Abstraction
 * 
 * Uses the Web Speech API (SpeechRecognition) for push-to-talk input.
 * Falls back gracefully when not supported.
 * 
 * Attribution: Speaker is determined by who pressed the talk button,
 * not by voice analysis.
 */

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList
  resultIndex: number
}

interface SpeechRecognitionResultList {
  length: number
  item(index: number): SpeechRecognitionResult
  [index: number]: SpeechRecognitionResult
}

interface SpeechRecognitionResult {
  length: number
  item(index: number): SpeechRecognitionAlternative
  [index: number]: SpeechRecognitionAlternative
  isFinal: boolean
}

interface SpeechRecognitionAlternative {
  transcript: string
  confidence: number
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string
  message?: string
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
declare global {
  interface Window {
    SpeechRecognition: any
    webkitSpeechRecognition: any
  }
}

/**
 * Check if speech recognition is supported in this browser
 */
export function isSttSupported(): boolean {
  if (typeof window === 'undefined') return false
  return !!(window.SpeechRecognition || window.webkitSpeechRecognition)
}

/**
 * Get the speech recognition API (webkit prefix handling)
 */
function getRecognitionApi(): typeof window.SpeechRecognition | null {
  return window.SpeechRecognition || window.webkitSpeechRecognition || null
}

/**
 * Continuous listening mode - for hands-free voice input
 */
export function startListening(
  onResult: (transcript: string, isFinal: boolean) => void,
  onError?: (error: string) => void
): () => void {
  const Recognition = getRecognitionApi()
  if (!Recognition) {
    onError?.('Speech recognition not supported')
    return () => {}
  }

  const recognition = new Recognition()
  recognition.continuous = true
  recognition.interimResults = true
  recognition.lang = 'en-US'

  recognition.onresult = (event: SpeechRecognitionEvent) => {
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const result = event.results[i]
      const transcript = result[0].transcript.trim()
      if (transcript) {
        onResult(transcript, result.isFinal)
      }
    }
  }

  recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
    // Ignore 'no-speech' and 'aborted' errors - these are normal
    if (event.error !== 'no-speech' && event.error !== 'aborted') {
      onError?.(event.error)
    }
  }

  recognition.onend = () => {
    // Restart if we were in continuous mode
    // recognition will be garbage collected when stop is called
  }

  try {
    recognition.start()
  } catch {
    onError?.('Failed to start speech recognition')
  }

  // Return stop function
  return () => {
    try {
      recognition.stop()
    } catch {
      // Ignore errors on stop
    }
  }
}

/**
 * Single utterance mode - for hold-to-talk
 * Starts listening and returns a promise that resolves with the transcript
 * when the user stops speaking (or after a timeout)
 */
export function listenOnce(timeoutMs = 10000): Promise<string> {
  return new Promise((resolve, reject) => {
    const Recognition = getRecognitionApi()
    if (!Recognition) {
      reject(new Error('Speech recognition not supported'))
      return
    }

    const recognition = new Recognition()
    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = 'en-US'

    let finalTranscript = ''
    let timeoutId: ReturnType<typeof setTimeout>

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal) {
          finalTranscript += ' ' + result[0].transcript.trim()
        }
      }
    }

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      clearTimeout(timeoutId)
      if (event.error === 'no-speech') {
        resolve('')
      } else {
        reject(new Error(event.error))
      }
    }

    recognition.onend = () => {
      clearTimeout(timeoutId)
      resolve(finalTranscript.trim())
    }

    recognition.start()

    // Timeout for long utterances
    timeoutId = setTimeout(() => {
      try {
        recognition.stop()
      } catch {
        // Already stopped
      }
      resolve(finalTranscript.trim())
    }, timeoutMs)
  })
}

/**
 * Stop any active speech recognition
 */
export function stopListening(): void {
  // Speech recognition doesn't have a global stop,
  // but we can check if recognition is running
  // The stop function returned by startListening handles cleanup
}