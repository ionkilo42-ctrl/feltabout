/**
 * Feltabout Design System - Source of Truth
 * 
 * Emotionally grounded, warm minimalism.
 * The UI should feel like a deep breath before a hard conversation.
 * 
 * Design keywords: Soft, Reflective, Airy, Intentional, Human, Calm, Elegant, Warm minimalism
 */

export const tokens = {
  // ═══════════════════════════════════════════════════════════
  // COLORS
  // ═══════════════════════════════════════════════════════════
  
  colors: {
    // Primary Background - Warm paper tone
    background: '#F7F5F2',
    backgroundSoft: '#FDFCFB',
    backgroundDeep: '#F0EDE8',
    
    // Card Surfaces - Soft floating elements
    card: 'rgba(255, 255, 255, 0.82)',
    cardSolid: '#FFFFFF',
    cardSubtle: 'rgba(255, 255, 255, 0.65)',
    
    // Gradient Language - Emotional accent system
    // Used sparingly: icons, CTAs, selected states, highlights
    gradient: {
      start: '#00C2FF',      // Turquoise
      mid1: '#33D6C8',       // Cyan/teal
      mid2: '#FF6B6B',       // Coral
      end: '#FFB547',        // Amber
    },
    
    // Typography - Dark charcoal for primary, muted for secondary
    text: '#1E1E1E',
    textSoft: '#4A4A4A',
    textMuted: '#666666',
    textQuiet: '#A3A3A3',
    
    // Borders & Dividers
    border: '#E8E4DF',
    borderSubtle: 'rgba(0, 0, 0, 0.04)',
    borderStrong: 'rgba(0, 0, 0, 0.08)',
    
    // Semantic Colors
    accent: '#33D6C8',
    accentSoft: 'rgba(51, 214, 200, 0.12)',
    accentBorder: 'rgba(51, 214, 200, 0.25)',
    
    success: '#5BA88D',
    successSoft: 'rgba(91, 168, 141, 0.12)',
    
    warning: '#D4A055',
    warningSoft: 'rgba(212, 160, 85, 0.12)',
    
    error: '#D46B6B',
    errorSoft: 'rgba(212, 107, 107, 0.12)',
  },
  
  // ═══════════════════════════════════════════════════════════
  // TYPOGRAPHY
  // ═══════════════════════════════════════════════════════════
  
  typography: {
    fontFamily: "'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    
    // Font weights - medium focus, not bold headlines
    weights: {
      regular: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    
    // Font sizes with responsive scaling
    sizes: {
      xs: '0.75rem',     // 12px
      sm: '0.85rem',     // 13-14px
      base: '1rem',      // 16px
      md: '1.125rem',    // 18px
      lg: '1.25rem',     // 20px
      xl: '1.5rem',      // 24px
      '2xl': '2rem',     // 32px
      '3xl': '2.5rem',   // 40px
      '4xl': '3rem',     // 48px
    },
    
    // Line heights - slightly larger for breathing room
    lineHeights: {
      tight: 1.15,
      normal: 1.5,
      relaxed: 1.65,
      loose: 1.75,
    },
    
    // Letter spacing
    letterSpacing: {
      tight: '-0.03em',
      normal: '-0.01em',
      wide: '0.01em',
      wider: '0.05em',
      widest: '0.1em',
    },
  },
  
  // ═══════════════════════════════════════════════════════════
  // SPACING
  // ═══════════════════════════════════════════════════════════
  
  spacing: {
    // Base unit: 4px
    0: '0',
    px: '1px',
    0.5: '0.125rem',   // 2px
    1: '0.25rem',      // 4px
    1.5: '0.375rem',   // 6px
    2: '0.5rem',       // 8px
    2.5: '0.625rem',   // 10px
    3: '0.75rem',      // 12px
    3.5: '0.875rem',   // 14px
    4: '1rem',         // 16px
    5: '1.25rem',      // 20px
    6: '1.5rem',       // 24px
    8: '2rem',         // 32px
    10: '2.5rem',      // 40px
    12: '3rem',        // 48px
    16: '4rem',        // 64px
    20: '5rem',        // 80px
    24: '6rem',        // 96px
  },
  
  // ═══════════════════════════════════════════════════════════
  // RADIUS
  // ═══════════════════════════════════════════════════════════
  
  radius: {
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '20px',
    '2xl': '24px',
    '3xl': '28px',
    full: '999px',
  },
  
  // ═══════════════════════════════════════════════════════════
  // SHADOWS - Soft, floating elevation
  // ═══════════════════════════════════════════════════════════
  
  shadows: {
    sm: '0 2px 8px rgba(0, 0, 0, 0.04)',
    md: '0 8px 32px rgba(0, 0, 0, 0.06)',
    lg: '0 16px 48px rgba(0, 0, 0, 0.08)',
    card: '0 4px 24px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02)',
    glow: '0 4px 16px rgba(51, 214, 200, 0.25)',
    glowStrong: '0 8px 24px rgba(51, 214, 200, 0.35)',
  },
  
  // ═══════════════════════════════════════════════════════════
  // MOTION - Fluid, organic, emotionally soft
  // ═══════════════════════════════════════════════════════════
  
  motion: {
    // Easing curves
    ease: {
      soft: 'cubic-bezier(0.4, 0, 0.2, 1)',
      spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
      gentle: 'cubic-bezier(0.25, 0.1, 0.25, 1)',
    },
    
    // Durations - slower for calm feel
    duration: {
      fast: '150ms',
      normal: '300ms',
      slow: '500ms',
      slower: '700ms',
    },
  },
  
  // ═══════════════════════════════════════════════════════════
  // GRADIENT PRESETS
  // ═══════════════════════════════════════════════════════════
  
  gradients: {
    // Core gradient: Turquoise → Cyan → Coral → Amber
    core: 'linear-gradient(135deg, #00C2FF 0%, #33D6C8 30%, #FF6B6B 65%, #FFB547 100%)',
    
    // Soft gradient for backgrounds/hover states
    soft: 'linear-gradient(135deg, rgba(0, 194, 255, 0.15) 0%, rgba(51, 214, 200, 0.15) 30%, rgba(255, 107, 107, 0.15) 65%, rgba(255, 181, 71, 0.15) 100%)',
    
    // Subtle gradient for cards
    subtle: 'linear-gradient(180deg, rgba(255, 255, 255, 0.4) 0%, rgba(255, 255, 255, 0.1) 100%)',
  },
} as const;

// Helper to create CSS custom properties string
export function toCSSVariables(prefix = '--feltabout'): string {
  const vars: string[] = [];
  
  // Colors
  Object.entries(tokens.colors).forEach(([key, value]) => {
    if (typeof value === 'object' && value !== null) {
      Object.entries(value).forEach(([subKey, subValue]) => {
        vars.push(`${prefix}-${key}-${subKey}: ${subValue}`);
      });
    } else {
      vars.push(`${prefix}-${key}: ${value}`);
    }
  });
  
  // Typography
  vars.push(`${prefix}-font: ${tokens.typography.fontFamily}`);
  
  // Weights & Sizes
  Object.entries(tokens.typography.weights).forEach(([key, value]) => {
    vars.push(`${prefix}-weight-${key}: ${value}`);
  });
  Object.entries(tokens.typography.sizes).forEach(([key, value]) => {
    vars.push(`${prefix}-size-${key}: ${value}`);
  });
  
  // Spacing
  Object.entries(tokens.spacing).forEach(([key, value]) => {
    vars.push(`${prefix}-space-${key}: ${value}`);
  });
  
  // Radius
  Object.entries(tokens.radius).forEach(([key, value]) => {
    vars.push(`${prefix}-radius-${key}: ${value}`);
  });
  
  // Shadows
  Object.entries(tokens.shadows).forEach(([key, value]) => {
    vars.push(`${prefix}-shadow-${key}: ${value}`);
  });
  
  // Motion
  vars.push(`${prefix}-ease-soft: ${tokens.motion.ease.soft}`);
  vars.push(`${prefix}-ease-spring: ${tokens.motion.ease.spring}`);
  vars.push(`${prefix}-ease-gentle: ${tokens.motion.ease.gentle}`);
  vars.push(`${prefix}-duration-fast: ${tokens.motion.duration.fast}`);
  vars.push(`${prefix}-duration-normal: ${tokens.motion.duration.normal}`);
  vars.push(`${prefix}-duration-slow: ${tokens.motion.duration.slow}`);
  
  // Gradients
  Object.entries(tokens.gradients).forEach(([key, value]) => {
    vars.push(`${prefix}-gradient-${key}: ${value}`);
  });
  
  return vars.join(';\n');
}

// Type exports for consumption
export type DesignTokens = typeof tokens;