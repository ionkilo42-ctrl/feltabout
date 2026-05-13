# Voice Strategy - Feltabout MVP + Future

> Last updated: 2026-05-13

## Overview

Feltabout is moving toward voice-first interaction in solo sessions and shared spaces. This document outlines the MVP approach and the upgrade path to paid voice providers.

---

## MVP Voice Implementation

### Browser Web Speech API (Current)

**Status:** Implemented in `frontend/lib/voice/tts.ts`

**Capabilities:**
- Text-to-speech for AI responses
- Free, no billing required
- Works in Chrome, Edge, Safari (limited in Firefox)
- Graceful fallback when unsupported

**Functions:**
```ts
import { speak, stopSpeaking, isTtsSupported } from '@/lib/voice/tts'

// Speak AI response
speak('I hear that this situation has been building up.')
stopSpeaking() // Stop at any time
```

**Limitations:**
- Voice quality varies by browser/OS
- No advanced emotional tone control
- No streaming
- Speech recognition (STT) not included in MVP

---

## Walkie-Talkie Speaker Model

### Problem
Automatic speaker recognition via voice fingerprinting raises privacy concerns and is technically complex.

### Solution
Use a walkie-talkie / push-to-talk model where the **active speaker is determined by who pressed the button**, not by voice identification.

### MVP UX Design

```
┌─────────────────────────────────────┐
│  🔴 Jonathan is speaking            │  ← Visual indicator
│  ────────────────────────────────  │
│  [ HOLD TO TALK ]  ← press/hold    │  ← Primary interaction
│  [ RELEASE ]        ← auto on lift │
└─────────────────────────────────────┘
```

**States:**
1. **Idle** — No one speaking, input keyboard available
2. **Speaking** — User holding PTT, their message being captured
3. **Processing** — Speech being transcribed/processed
4. **AI Response** — Aimee speaking/responding

**Interaction Flow:**
1. User presses/holds "Hold to talk" button
2. Visual indicator shows "Jonathan is speaking"
3. User releases button
4. Message is sent/transcribed
5. Aimee responds (optionally with TTS)

### Shared Session Extension
```
┌─────────────────────────────────────┐
│  Session: "Dinner conversation"     │
│  ────────────────────────────────  │
│  👤 Jonathan    🔴 Speaking        │
│  👤 Guest       ○ Waiting           │
└─────────────────────────────────────┘
```

The current speaker is always identifiable from UI state — no voice fingerprinting needed.

---

## Future Voice Providers

### Upgrade Path

| Provider | Use Case | When to Add |
|---|---|---|
| Browser Web Speech | MVP TTS | Now ✅ |
| Browser Speech Recognition | MVP STT | Future |
| ElevenLabs | Premium TTS | Post-MVP |
| OpenAI Realtime | Voice sessions | Post-MVP |
| Deepgram/Whisper | STT | Post-MVP |

### Integration Pattern

All providers implement the same interface:

```ts
interface VoiceProvider {
  speak(text: string, options?: SpeakOptions): Promise<void>
  stopSpeaking(): void
  // STT interface would be similar
}
```

**Current implementation:** `frontend/lib/voice/tts.ts`

**Future additions:**
- `frontend/lib/voice/elevenlabs.ts` — ElevenLabs TTS
- `frontend/lib/voice/openai-realtime.ts` — OpenAI Realtime voice
- `frontend/lib/voice/deepgram-stt.ts` — STT provider

The provider is selected via environment variable or feature flag, allowing easy switching.

---

## Architecture Notes

### Voice Components

```
frontend/lib/voice/
├── tts.ts              # Browser TTS (current MVP)
├── elevenlabs.ts       # [Future] ElevenLabs integration
├── openai-realtime.ts  # [Future] OpenAI Realtime
└── stt.ts             # [Future] Speech-to-text abstraction
```

### Safety Considerations

- Voice input passes through same safety checks as text input
- Crisis detection works on transcribed speech
- No voice biometric data stored
- Walkie-talkie model avoids voice fingerprinting

---

## Testing

**Browser TTS:**
```ts
import { speak, isTtsSupported } from '@/lib/voice/tts'

if (isTtsSupported()) {
  speak('Hello from Feltabout')
}
```

**Accessibility:**
- Voice is progressive enhancement — text always works
- Screen reader users can disable TTS
- Keyboard navigation works without voice

---

## Limitations

| Limitation | Browser Support | Notes |
|---|---|---|
| TTS Quality | Chrome/Edge > Safari > Firefox | Varies by OS voice engine |
| STT (future) | Chrome best, Safari partial | Firefox limited |
| Streaming | Not in Web Speech API | Future providers needed |
| Emotional TTS | Not in Web Speech | ElevenLabs/OpenAI later |

---

## Next Steps (Post-MVP)

1. Add STT abstraction (`lib/voice/stt.ts`)
2. Implement walkie-talkie UI component
3. Integrate Deepgram or similar for STT
4. Add ElevenLabs for premium TTS
5. Consider OpenAI Realtime for voice sessions