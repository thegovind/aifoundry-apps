import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

export function AuthCallback() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code')
      const error = searchParams.get('error')

      if (error) {
        setError(`Authentication failed: ${error}`)
        setLoading(false)
        return
      }

      if (!code) {
        setError('No authorization code received')
        setLoading(false)
        return
      }

      try {
        const response = await fetch(`${(import.meta as any).env.VITE_API_URL}/api/auth/github/callback`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ code }),
        })

        if (!response.ok) {
          throw new Error('Failed to authenticate')
        }

        const data = await response.json()
        
        localStorage.setItem('github_access_token', data.access_token)
        localStorage.setItem('github_user', JSON.stringify(data.user))
        
        navigate('/dashboard')
      } catch (err) {
        setError('Authentication failed. Please try again.')
        console.error('Auth callback error:', err)
      } finally {
        setLoading(false)
      }
    }

    handleCallback()
  }, [searchParams, navigate])

  if (loading) {
    return <div className="flex justify-center items-center min-h-screen">
      <div className="text-white">Authenticating...</div>
    </div>
  }

  if (error) {
    return <div className="flex justify-center items-center min-h-screen">
      <div className="text-red-500">{error}</div>
    </div>
  }

  return null
}
