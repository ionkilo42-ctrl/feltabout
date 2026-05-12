import NextAuth, { DefaultSession } from 'next-auth'

declare module 'next-auth' {
  interface Session {
    provider?: string
    accessToken?: string
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    provider?: string
    accessToken?: string
  }
}