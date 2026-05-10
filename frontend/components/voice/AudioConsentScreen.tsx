"use client";
/**
 * AudioConsentScreen — full-screen consent overlay shown before joining a voice session.
 *
 * Appears when a participant clicks "Join voice" for the first time in a session.
 * Captures explicit consent before the microphone is activated.
 *
 * Privacy design principles:
 *  - Consent is session-scoped (resets if both leave)
 *  - Audio is not recorded — only transcribed in real time
 *  - Participants can leave voice at any time without leaving the session
 */
import React, { useState } from "react";

interface AudioConsentScreenProps {
  onAccept: () => void;
  onDecline: () => void;
  facilitatorName?: string;
}

export function AudioConsentScreen({
  onAccept,
  onDecline,
  facilitatorName = "Feltabout",
}: AudioConsentScreenProps) {
  const [dontShowAgain, setDontShowAgain] = useState(false);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="consent-title"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(6px)",
      }}
    >
      <div
        style={{
          background: "#0f172a",
          border: "1px solid rgba(255,255,255,0.1)",
          borderRadius: 16,
          padding: "32px 28px",
          maxWidth: 440,
          width: "90%",
          color: "#f1f5f9",
          boxShadow: "0 24px 48px rgba(0,0,0,0.5)",
        }}
      >
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
          <div
            style={{
              width: 40, height: 40, borderRadius: "50%",
              background: "rgba(34,197,94,0.15)",
              border: "1px solid rgba(34,197,94,0.3)",
              display: "flex", alignItems: "center", justifyContent: "center",
              flexShrink: 0,
            }}
          >
            {/* Microphone icon */}
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" y1="19" x2="12" y2="23" />
              <line x1="8" y1="23" x2="16" y2="23" />
            </svg>
          </div>
          <div>
            <h2 id="consent-title" style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>
              Enable voice?
            </h2>
            <p style={{ margin: 0, fontSize: 12, color: "#64748b", marginTop: 2 }}>
              Audio consent required
            </p>
          </div>
        </div>

        {/* Body */}
        <div style={{ fontSize: 14, lineHeight: 1.6, color: "#cbd5e1", marginBottom: 24 }}>
          <p style={{ marginTop: 0 }}>
            You're about to join a <strong style={{ color: "#f1f5f9" }}>voice session</strong> with {facilitatorName}.
          </p>

          <p style={{ marginBottom: 8, fontWeight: 500, color: "#f1f5f9" }}>
            What this means:
          </p>
          <ul style={{ margin: "0 0 16px 0", paddingLeft: 20, color: "#94a3b8" }}>
            <li style={{ marginBottom: 6 }}>
              Your microphone will be active so you can speak naturally.
            </li>
            <li style={{ marginBottom: 6 }}>
              Your speech is <strong style={{ color: "#e2e8f0" }}>transcribed in real time</strong> and
              shared with the facilitator — not stored long-term.
            </li>
            <li style={{ marginBottom: 6 }}>
              <strong style={{ color: "#f1f5f9" }}>No audio is recorded.</strong> Transcripts are
              used only for this session's facilitation.
            </li>
            <li style={{ marginBottom: 6 }}>
              You can leave voice at any time by clicking the mic button — you don't need to leave the session.
            </li>
            <li>
              Your partner in this session will hear your voice directly.
            </li>
          </ul>

          <p style={{ color: "#f1f5f9", marginBottom: 0 }}>
            {facilitatorName} may also speak to guide the conversation.
          </p>
        </div>

        {/* Don't show again (persisted to localStorage) */}
        <label
          style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", marginBottom: 20 }}
        >
          <input
            type="checkbox"
            checked={dontShowAgain}
            onChange={(e) => setDontShowAgain(e.target.checked)}
            style={{ width: 16, height: 16, accentColor: "#22c55e" }}
          />
          <span style={{ fontSize: 13, color: "#64748b" }}>
            Remember this choice for future sessions
          </span>
        </label>

        {/* Actions */}
        <div style={{ display: "flex", gap: 10 }}>
          <button
            type="button"
            onClick={() => {
              if (dontShowAgain) {
                try { localStorage.setItem("feltabout_audio_consent", "accepted"); } catch {}
              }
              onAccept();
            }}
            style={{
              flex: 1,
              padding: "10px 16px",
              borderRadius: 8,
              border: "none",
              background: "#22c55e",
              color: "#fff",
              fontSize: 14,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Enable voice
          </button>
          <button
            type="button"
            onClick={() => {
              if (dontShowAgain) {
                try { localStorage.setItem("feltabout_audio_consent", "declined"); } catch {}
              }
              onDecline();
            }}
            style={{
              flex: 1,
              padding: "10px 16px",
              borderRadius: 8,
              border: "1px solid rgba(255,255,255,0.1)",
              background: "transparent",
              color: "#94a3b8",
              fontSize: 14,
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            Stay in text
          </button>
        </div>

        <p style={{ fontSize: 11, color: "#475569", marginTop: 16, marginBottom: 0, textAlign: "center" }}>
          Your consent can be withdrawn at any time.
        </p>
      </div>
    </div>
  );
}

/**
 * Hook to check if audio consent has been previously granted.
 * Returns null if no prior choice, true if accepted, false if declined.
 */
export function useAudioConsent(): boolean | null {
  if (typeof window === "undefined") return null;
  try {
    const stored = localStorage.getItem("feltabout_audio_consent");
    if (stored === "accepted") return true;
    if (stored === "declined") return false;
  } catch {}
  return null;
}
