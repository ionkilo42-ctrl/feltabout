# ═══════════════════════════════════════════════════════════════════════════════
# Feltabout Frontend — Next.js Production Image
# ═══════════════════════════════════════════════════════════════════════════════

# ─── Dependencies stage ───────────────────────────────────────────────────────
FROM node:20-alpine AS deps

WORKDIR /app

# Install pnpm globally
RUN corepack enable && corepack prepare pnpm@10.32.1 --activate

# Copy package files
COPY package.json pnpm-lock.yaml* ./

# Install dependencies (use npm as fallback if pnpm-lock.yaml missing)
RUN \
  if [ -f pnpm-lock.yaml ]; then \
    pnpm install --frozen-lockfile; \
  else \
    npm install; \
  fi

# ─── Builder stage ────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Install pnpm globally
RUN corepack enable && corepack prepare pnpm@10.32.1 --activate

# Copy node_modules from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy application code
COPY . .

# Build the Next.js application
RUN \
  if [ -f pnpm-lock.yaml ]; then \
    pnpm build; \
  else \
    npm run build; \
  fi


# ─── Runner stage ────────────────────────────────────────────────────────────
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000

# Set NEXT_PUBLIC_API_URL for Docker standalone builds.
# In local dev without this env, Next.js rewrites handle proxying (/api/* → localhost:8000).
# In Docker, we need the absolute Docker network hostname for API calls.
ENV NEXT_PUBLIC_API_URL="http://api:8000"

# Create non-root user for security
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Set correct permissions for Next.js standalone output
COPY --from=builder --chown=appuser:appgroup /app/public ./public
COPY --from=builder --chown=appuser:appgroup /app/.next/standalone ./
COPY --from=builder --chown=appuser:appgroup /app/.next/static ./.next/static

USER appuser

EXPOSE 3000

CMD ["node", "server.js"]