import { redirect } from 'next/navigation'

// Dashboard redirect — Feltabout uses Library as the main signed-in hub.
// If someone lands on /dashboard, send them to Library.
export default function DashboardPage() {
  redirect('/library')
}