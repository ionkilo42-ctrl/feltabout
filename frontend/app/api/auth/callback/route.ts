import { NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/auth.config'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const next = searchParams.get('next') || '/reflections'
  
  // Get the session from NextAuth
  const session = await getServerSession(authOptions)
  
  if (!session?.user?.email) {
    // No valid session, redirect to login
    return NextResponse.redirect(new URL('/login', request.url))
  }
  
  // Call Feltabout backend to get/create user and return JWT
  try {
    const backendRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/social-login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        provider: session.provider || 'google',
        email: session.user.email,
        name: session.user.name || session.user.email,
        provider_user_id: '', // Not tracked for MVP
        avatar_url: session.user.image || null,
      }),
    })
    
    if (!backendRes.ok) {
      console.error('Social login failed:', await backendRes.text())
      return NextResponse.redirect(new URL('/login?error=auth_failed', request.url))
    }
    
    const authData = await backendRes.json()
    
    // Redirect to the destination with the token as a query param
    // The client will read this and store in Zustand
    const redirectUrl = new URL(next, request.url)
    redirectUrl.searchParams.set('feltabout_token', authData.token)
    redirectUrl.searchParams.set('feltabout_user_id', authData.user.id)
    redirectUrl.searchParams.set('feltabout_user_name', authData.user.name)
    redirectUrl.searchParams.set('feltabout_user_email', authData.user.email)
    
    return NextResponse.redirect(redirectUrl)
  } catch (error) {
    console.error('Social login error:', error)
    return NextResponse.redirect(new URL('/login?error=server_error', request.url))
  }
}