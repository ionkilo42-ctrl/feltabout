/**
 * useVoiceSession — React hook for LiveKit voice room integration.
 *
 * Manages the full voice lifecycle:
 *  - Fetching a LiveKit token from the backend
 *  - Connecting to a LiveKit room
 *  - Publishing microphone audio
 *  - Subscribing to remote audio tracks
 *  - Detecting crosstalk (multiple simultaneous speakers)
 *  - Cleaning up on disconnect
 *
 * Usage:
 *   const voice = useVoiceSession({ sessionId, userId });
 *   // voice.connect() → joins the LiveKit room
 *   // voice.mute() / voice.unmute() → toggles mic
 *   // voice.isConnected → boolean
 *   // voice.audioTracks → remote audio tracks
 */
import { useEffect, useRef, useState, useCallback } from "react";
import { Room, RoomEvent, LocalParticipant, Participant } from "livekit-client";

export interface VoiceSessionState {
  isConnected: boolean;
  isConnecting: boolean;
  isMuted: boolean;
  isSpeaking: boolean;       // true when local mic detects voice activity
  audioLevel: number;        // 0-1, local mic level
  remoteAudioLevels: Map<string, number>;  // participantId → level
  error: string | null;
  connect: () => Promise<void>;
  disconnect: () => void;
  mute: () => void;
  unmute: () => void;
  toggleMute: () => void;
  room: Room | null;
}

interface UseVoiceSessionOptions {
  sessionId: string;
  userId: string;
  userName?: string;
  /** Called when the hook detects simultaneous audio from 2+ participants */
  onCrosstalk?: () => void;
  /** Called when a remote participant starts/stops speaking */
  onSpeakingChange?: (participantId: string, isSpeaking: boolean) => void;
}

export function useVoiceSession({
  sessionId,
  userId,
  userName,
  onCrosstalk,
  onSpeakingChange,
}: UseVoiceSessionOptions): VoiceSessionState {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [remoteAudioLevels, setRemoteAudioLevels] = useState<Map<string, number>>(new Map());
  const [error, setError] = useState<string | null>(null);

  const roomRef = useRef<Room | null>(null);
  const localParticipantRef = useRef<LocalParticipant | null>(null);
  const crosstalkTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const activeSpeakersRef = useRef<Set<string>>(new Set());

  // ─── Connect to LiveKit room ─────────────────────────────────────────────

  const connect = useCallback(async () => {
    setIsConnecting(true);
    setError(null);

    try {
      // 1. Fetch LiveKit token from backend
      const resp = await fetch(
        `/api/sessions/${sessionId}/join-voice`,
        { credentials: "include" }
      );
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.error || `HTTP ${resp.status}`);
      }
      const { token, livekit_url, room_name } = await resp.json();

      // 2. Create LiveKit room
      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
        audioCaptureDefaults: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      roomRef.current = room;

      // 3. Connect
      await room.connect(livekit_url, token);
      setIsConnected(true);

      const local = room.localParticipant;
      localParticipantRef.current = local;
      await local.setMicrophoneEnabled(true, {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      });

      // Track audio level (0-1) every 200ms
      const levelInterval = setInterval(() => {
        setAudioLevel(Math.min(1, Math.max(0, local.audioLevel ?? 0)));
        setIsSpeaking(local.isSpeaking || (local.audioLevel ?? 0) > 0.08);
      }, 200);

      // ─── Remote participant events ───────────────────────────────────────

      room.on(RoomEvent.ActiveSpeakersChanged, (speakers: Participant[]) => {
        const activeRemoteIds = new Set(
          speakers
            .filter((participant) => !participant.isLocal)
            .map((participant) => participant.identity)
        );
        activeSpeakersRef.current = new Set(speakers.map((participant) => participant.identity));

        setRemoteAudioLevels((prev) => {
          const next = new Map(prev);
          speakers.forEach((participant) => {
            if (!participant.isLocal) {
              next.set(participant.identity, Math.min(1, Math.max(0, participant.audioLevel ?? 0.5)));
            }
          });
          prev.forEach((_level, pid) => {
            if (!activeRemoteIds.has(pid)) next.set(pid, 0);
          });
          return next;
        });

        speakers.forEach((participant) => {
          if (!participant.isLocal) {
            onSpeakingChange?.(participant.identity, true);
          }
        });

        if (activeSpeakersRef.current.size > 1) {
          if (crosstalkTimerRef.current) clearTimeout(crosstalkTimerRef.current);
          crosstalkTimerRef.current = setTimeout(() => {
            onCrosstalk?.();
          }, 500);
        }
      });

      // ─── Cleanup on disconnect ───────────────────────────────────────────

      room.on(RoomEvent.Disconnected, () => {
        setIsConnected(false);
        setIsSpeaking(false);
        setAudioLevel(0);
        clearInterval(levelInterval);
        roomRef.current = null;
      });

    } catch (err: any) {
      setError(err?.message ?? "Failed to connect to voice room");
      setIsConnected(false);
    } finally {
      setIsConnecting(false);
    }
  }, [sessionId, userId, userName, onCrosstalk, onSpeakingChange]);

  // ─── Disconnect ───────────────────────────────────────────────────────────

  const disconnect = useCallback(() => {
    roomRef.current?.disconnect();
    roomRef.current = null;
    setIsConnected(false);
    setIsSpeaking(false);
    setAudioLevel(0);
    activeSpeakersRef.current.clear();
    if (crosstalkTimerRef.current) clearTimeout(crosstalkTimerRef.current);
  }, []);

  // ─── Mute / Unmute ────────────────────────────────────────────────────────

  const mute = useCallback(() => {
    roomRef.current?.localParticipant.setMicrophoneEnabled(false);
    setIsMuted(true);
    setIsSpeaking(false);
  }, []);

  const unmute = useCallback(() => {
    roomRef.current?.localParticipant.setMicrophoneEnabled(true);
    setIsMuted(false);
  }, []);

  const toggleMute = useCallback(() => {
    if (isMuted) unmute();
    else mute();
  }, [isMuted, mute, unmute]);

  // ─── Cleanup on unmount ───────────────────────────────────────────────────

  useEffect(() => {
    return () => {
      roomRef.current?.disconnect();
      if (crosstalkTimerRef.current) clearTimeout(crosstalkTimerRef.current);
    };
  }, []);

  return {
    isConnected,
    isConnecting,
    isMuted,
    isSpeaking,
    audioLevel,
    remoteAudioLevels,
    error,
    connect,
    disconnect,
    mute,
    unmute,
    toggleMute,
    room: roomRef.current,
  };
}
