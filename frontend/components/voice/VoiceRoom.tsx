"use client";
/**
 * VoiceRoom — Orchestrates the full voice session UI.
 *
 * Wires together:
 *  - useVoiceSession (LiveKit lifecycle)
 *  - MicrophoneToggle (local mic control)
 *  - AudioLevelIndicator (speaking activity per participant)
 *
 * Sends `crosstalk_detected` WebSocket messages to the backend when
 * multiple participants are speaking simultaneously.
 *
 * Props:
 *  - sessionId, userId, userName, ws (WebSocket used for text messages)
 *  - onVoiceError?: (err: string) => void — surface errors to parent
 */
import React, { useCallback } from "react";
import { useVoiceSession } from "../../hooks/useVoiceSession";
import { MicrophoneToggle } from "./MicrophoneToggle";
import { AudioLevelIndicator } from "./AudioLevelIndicator";

interface ParticipantVoiceMeta {
  id: string;
  name: string;
  isLocal?: boolean;
}

interface VoiceRoomProps {
  sessionId: string;
  userId: string;
  userName?: string;
  /** The existing WebSocket used for text messages */
  ws: WebSocket | null;
  /** Called when a non-recoverable voice error occurs */
  onVoiceError?: (message: string) => void;
  /** Initial list of participants (from join message) */
  participants?: ParticipantVoiceMeta[];
}

export function VoiceRoom({
  sessionId,
  userId,
  userName,
  ws,
  onVoiceError,
  participants = [],
}: VoiceRoomProps) {
  // ─── Crosstalk handler ────────────────────────────────────────────────────
  // Sends crosstalk event to the backend via the text WebSocket
  const handleCrosstalk = useCallback(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "crosstalk_detected" }));
    }
  }, [ws]);

  // ─── Speaking change handler ───────────────────────────────────────────────
  const handleSpeakingChange = useCallback((_pid: string, _isSpeaking: boolean) => {
    // Could be used to highlight the active speaker in the participant list
  }, []);

  // ─── LiveKit voice session ─────────────────────────────────────────────────
  const voice = useVoiceSession({
    sessionId,
    userId,
    userName,
    onCrosstalk: handleCrosstalk,
    onSpeakingChange: handleSpeakingChange,
  });

  // Surface errors upward
  React.useEffect(() => {
    if (voice.error) onVoiceError?.(voice.error);
  }, [voice.error, onVoiceError]);

  // ─── Render ────────────────────────────────────────────────────────────────
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "8px 12px",
        background: "rgba(15, 23, 42, 0.8)",
        borderRadius: 12,
        backdropFilter: "blur(8px)",
        border: "1px solid rgba(255,255,255,0.06)",
      }}
      role="region"
      aria-label="Voice session controls"
    >
      {/* ── Local mic controls ──────────────────────────────────── */}
      <MicrophoneToggle
        isMuted={voice.isMuted}
        isConnecting={voice.isConnecting}
        isSpeaking={voice.isSpeaking}
        audioLevel={voice.audioLevel}
        onToggle={voice.toggleMute}
      />

      {/* Local audio level */}
      <AudioLevelIndicator
        level={voice.audioLevel}
        variant="bars"
        size={32}
        activeColor="#22c55e"
        inactiveColor="#374151"
        isLocal={true}
      />

      {/* ── Voice status label ─────────────────────────────────── */}
      <div style={{ minWidth: 80 }}>
        {voice.isConnecting && (
          <span style={{ color: "#94a3b8", fontSize: 12 }}>Joining…</span>
        )}
        {!voice.isConnecting && voice.isConnected && (
          <span style={{ color: "#22c55e", fontSize: 12, display: "flex", alignItems: "center", gap: 4 }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#22c55e", display: "inline-block" }} />
            Voice on
          </span>
        )}
        {!voice.isConnecting && !voice.isConnected && !voice.error && (
          <span style={{ color: "#64748b", fontSize: 12 }}>Voice off</span>
        )}
        {voice.error && (
          <span style={{ color: "#ef4444", fontSize: 11, maxWidth: 120 }} title={voice.error}>
            Voice error
          </span>
        )}
      </div>

      {/* ── Remote participant indicators ──────────────────────── */}
      {Array.from(voice.remoteAudioLevels.entries()).map(([pid, level]) => {
        const meta = participants.find((p) => p.id === pid);
        return (
          <div
            key={pid}
            title={meta?.name ?? pid}
            style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 2 }}
          >
            <AudioLevelIndicator
              level={level}
              variant="ring"
              size={28}
              activeColor="#60a5fa"
              inactiveColor="#374151"
            />
            {meta && (
              <span style={{ color: "#94a3b8", fontSize: 10, maxWidth: 48, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {meta.name}
              </span>
            )}
          </div>
        );
      })}

      {/* ── Join/leave voice button ────────────────────────────── */}
      {!voice.isConnected && !voice.isConnecting && (
        <button
          type="button"
          onClick={voice.connect}
          style={{
            padding: "6px 12px",
            borderRadius: 8,
            border: "1px solid rgba(255,255,255,0.1)",
            background: "rgba(34, 197, 94, 0.1)",
            color: "#22c55e",
            fontSize: 12,
            cursor: "pointer",
            fontWeight: 500,
          }}
        >
          Join voice
        </button>
      )}
      {voice.isConnected && (
        <button
          type="button"
          onClick={voice.disconnect}
          style={{
            padding: "6px 12px",
            borderRadius: 8,
            border: "1px solid rgba(239,68,68,0.3)",
            background: "rgba(239,68,68,0.1)",
            color: "#ef4444",
            fontSize: 12,
            cursor: "pointer",
            fontWeight: 500,
          }}
        >
          Leave voice
        </button>
      )}
    </div>
  );
}