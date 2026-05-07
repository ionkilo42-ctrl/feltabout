"use client";
/**
 * VoiceErrorBanner — displays a voice service error with appropriate severity.
 *
 * Props:
 *  - error: { code, message, transient } from backend voice_error
 *  - onRetry?: () => void — shown for TRANSIENT errors
 *  - onDismiss: () => void
 *
 * Severity mapping:
 *  - TRANSIENT → amber warning banner, retry button
 *  - PERMANENT → red error banner, no retry
 *  - (no error) → null (renders nothing)
 */
import React from "react";

interface VoiceErrorProps {
  error: {
    code: string;
    message: string;
    transient: boolean;
  } | null;
  onRetry?: () => void;
  onDismiss: () => void;
}

export function VoiceErrorBanner({ error, onRetry, onDismiss }: VoiceErrorProps) {
  if (!error) return null;

  const isTransient = error.transient !== false; // default to transient if undefined
  const isPermanent = !isTransient;

  return (
    <div
      role="alert"
      aria-live="polite"
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "8px 14px",
        borderRadius: 8,
        background: isPermanent ? "rgba(239,68,68,0.12)" : "rgba(245,158,11,0.12)",
        border: `1px solid ${isPermanent ? "rgba(239,68,68,0.3)" : "rgba(245,158,11,0.3)"}`,
        color: isPermanent ? "#fca5a5" : "#fcd34d",
        fontSize: 13,
        lineHeight: 1.4,
        backdropFilter: "blur(4px)",
      }}
    >
      {/* Warning icon */}
      <svg
        width="16" height="16" viewBox="0 0 24 24" fill="none"
        stroke={isPermanent ? "#ef4444" : "#f59e0b"}
        strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
        style={{ flexShrink: 0 }}
      >
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
        <line x1="12" y1="9" x2="12" y2="13" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </svg>

      {/* Message */}
      <span style={{ flex: 1 }}>{error.message}</span>

      {/* Actions */}
      <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
        {isTransient && onRetry && (
          <button
            type="button"
            onClick={onRetry}
            style={{
              padding: "4px 10px",
              borderRadius: 6,
              border: "1px solid rgba(245,158,11,0.4)",
              background: "rgba(245,158,11,0.15)",
              color: "#fcd34d",
              fontSize: 12,
              cursor: "pointer",
              fontWeight: 500,
            }}
          >
            Retry
          </button>
        )}
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Dismiss"
          style={{
            width: 24, height: 24,
            borderRadius: "50%",
            border: "1px solid rgba(255,255,255,0.1)",
            background: "transparent",
            color: "#94a3b8",
            cursor: "pointer",
            display: "flex", alignItems: "center", justifyContent: "center",
            padding: 0,
            fontSize: 14,
            lineHeight: 1,
          }}
        >
          ×
        </button>
      </div>
    </div>
  );
}