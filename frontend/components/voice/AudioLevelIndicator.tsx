"use client";
/**
 * AudioLevelIndicator — Animated bar/ring that reflects the current audio level.
 *
 * Used to show remote participants' speaking activity and the local user's
 * own voice detection. Renders N bars that animate proportionally to `level` (0-1).
 *
 * Variants:
 *  - "bars": vertical bar meter (classic VU meter style)
 *  - "ring": circular ripple effect (more modern)
 */
import React, { useEffect, useRef } from "react";

interface AudioLevelIndicatorProps {
  level: number;        // 0–1
  variant?: "bars" | "ring";
  size?: number;        // px, default 40
  activeColor?: string; // default "#22c55e"
  inactiveColor?: string; // default "#374151"
  /** Whether this indicator represents the local user */
  isLocal?: boolean;
  className?: string;
}

export function AudioLevelIndicator({
  level,
  variant = "bars",
  size = 40,
  activeColor = "#22c55e",
  inactiveColor = "#374151",
  isLocal = false,
  className,
}: AudioLevelIndicatorProps) {
  if (variant === "ring") {
    const r = size / 2;
    const strokeWidth = 3;
    const circumference = 2 * Math.PI * (r - strokeWidth / 2);
    const activeOffset = circumference * (1 - Math.max(0, Math.min(1, level)));

    return (
      <svg
        width={size} height={size}
        viewBox={`0 0 ${size} ${size}`}
        style={{ transform: "rotate(-90deg)", display: "block" }}
        className={className}
        aria-hidden="true"
      >
        {/* Track */}
        <circle
          cx={r} cy={r}
          r={r - strokeWidth / 2}
          fill="none"
          stroke={inactiveColor}
          strokeWidth={strokeWidth}
        />
        {/* Active arc */}
        <circle
          cx={r} cy={r}
          r={r - strokeWidth / 2}
          fill="none"
          stroke={level > 0.05 ? activeColor : inactiveColor}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={activeOffset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 80ms ease, stroke 80ms ease" }}
        />
      </svg>
    );
  }

  // Bars variant — 5 vertical bars, each scaling with level
  const BAR_COUNT = 5;
  const BAR_GAP = 2;
  const BAR_WIDTH = (size - BAR_GAP * (BAR_COUNT - 1)) / BAR_COUNT;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-end",
        gap: BAR_GAP,
        height: size,
        width: size,
      }}
      className={className}
      aria-hidden="true"
    >
      {Array.from({ length: BAR_COUNT }).map((_, i) => {
        // Bar i corresponds to a level threshold: 0.2, 0.4, 0.6, 0.8, 1.0
        const threshold = (i + 1) / BAR_COUNT;
        const isActive = level >= threshold - 0.2;
        const barHeightFraction = isActive
          ? Math.min(1, (level - (threshold - 0.2)) / 0.2) * 0.4 + 0.5
          : 0.3; // dimmed height when inactive

        return (
          <div
            key={i}
            style={{
              width: BAR_WIDTH,
              height: `${barHeightFraction * 100}%`,
              background: isActive && level > 0.05 ? activeColor : inactiveColor,
              borderRadius: 2,
              alignSelf: "flex-end",
              transition: "background 80ms ease, height 80ms ease",
            }}
          />
        );
      })}
    </div>
  );
}