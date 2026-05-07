"use client";
/**
 * MicrophoneToggle — Toggle button for the user's own microphone in a voice session.
 *
 * Visual states:
 *  - Idle / ready: neutral mic icon, full opacity
 *  - Muted: mic-off icon, red tint, strikethrough line
 *  - Connecting: spinning/loading state
 *  - Speaking: green glow / accent ring
 */
import React from "react";

interface MicrophoneToggleProps {
  isMuted: boolean;
  isConnecting: boolean;
  isSpeaking: boolean;
  audioLevel: number;  // 0–1
  onToggle: () => void;
  disabled?: boolean;
  /** Accessibility label overrides */
  labelMuted?: string;
  labelUnmuted?: string;
  labelConnecting?: string;
}

export function MicrophoneToggle({
  isMuted,
  isConnecting,
  isSpeaking,
  audioLevel,
  onToggle,
  disabled = false,
  labelMuted = "Unmute microphone",
  labelUnmuted = "Mute microphone",
  labelConnecting = "Connecting…",
}: MicrophoneToggleProps) {
  const isDisabled = disabled || isConnecting;
  const showActivityRing = !isMuted && !isConnecting && (isSpeaking || audioLevel > 0.1);

  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={isDisabled}
      aria-label={isConnecting ? labelConnecting : isMuted ? labelMuted : labelUnmuted}
      title={isConnecting ? labelConnecting : isMuted ? labelMuted : labelUnmuted}
      style={{
        position: "relative",
        width: 52,
        height: 52,
        borderRadius: "50%",
        border: "none",
        cursor: isDisabled ? "not-allowed" : "pointer",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: isMuted ? "#2d1a1a" : "#1a2d1a",
        outline: "none",
        transition: "background 200ms ease, box-shadow 200ms ease",
        boxShadow: showActivityRing
          ? `0 0 0 3px rgba(34, 197, 94, ${Math.min(1, audioLevel * 2)})`
          : "none",
        opacity: isConnecting ? 0.6 : 1,
      }}
    >
      {isConnecting ? (
        /* Spinner */
        <svg
          width="22" height="22" viewBox="0 0 24 24" fill="none"
          stroke="#94a3b8" strokeWidth="2" strokeLinecap="round"
          style={{ animation: "spin 1s linear infinite" }}
        >
          <path d="M21 12a9 9 0 1 1-6.219-8.56" />
        </svg>
      ) : isMuted ? (
        /* Mic off */
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="1" y1="1" x2="23" y2="23" />
          <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6" />
          <path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2a7 7 0 0 1-.11 1.23" />
          <line x1="12" y1="19" x2="12" y2="23" />
          <line x1="8" y1="23" x2="16" y2="23" />
        </svg>
      ) : (
        /* Mic on */
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" y1="19" x2="12" y2="23" />
          <line x1="8" y1="23" x2="16" y2="23" />
        </svg>
      )}

      {/* CSS keyframe for spinner */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </button>
  );
}