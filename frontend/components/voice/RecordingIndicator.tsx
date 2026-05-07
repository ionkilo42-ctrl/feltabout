"use client";
/**
 * RecordingIndicator — small persistent badge shown while voice session is active.
 *
 * Design principles:
 *  - Visible when voice is on, hidden when text-only
 *  - Does NOT claim "Recording" (which implies storage) — instead says "Voice on"
 *  - Red pulsing dot is the universal "live audio" signal
 *  - Shown in the header or voice bar, never hidden in a menu
 */
import React from "react";

interface RecordingIndicatorProps {
  isActive: boolean;   // true when voice is connected
  participantCount?: number;  // number of voice participants
  className?: string;
}

export function RecordingIndicator({
  isActive,
  participantCount,
  className,
}: RecordingIndicatorProps) {
  if (!isActive) return null;

  return (
    <div
      role="status"
      aria-label="Voice session active"
      className={className}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        padding: "3px 8px",
        borderRadius: 20,
        background: "rgba(239,68,68,0.1)",
        border: "1px solid rgba(239,68,68,0.25)",
      }}
    >
      {/* Pulsing red dot */}
      <span
        aria-hidden="true"
        style={{
          width: 7, height: 7,
          borderRadius: "50%",
          background: "#ef4444",
          display: "inline-block",
          animation: "recording-pulse 1.4s ease-in-out infinite",
        }}
      />

      <span style={{ fontSize: 11, color: "#fca5a5", fontWeight: 500, lineHeight: 1 }}>
        Voice on
      </span>

      {participantCount !== undefined && participantCount > 0 && (
        <span style={{ fontSize: 11, color: "#fca5a5", opacity: 0.7, lineHeight: 1 }}>
          · {participantCount}
        </span>
      )}

      <style>{`
        @keyframes recording-pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(0.85); }
        }
      `}</style>
    </div>
  );
}