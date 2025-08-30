import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { Link } from 'react-router-dom'

interface Repository {
  id: number
  name: string
  full_name: string
  description: string
  html_url: string
  stargazers_count: number
  forks_count: number
  updated_at: string
  private: boolean
}

export function UserDashboard() {
  const { user, accessToken, isAuthenticated } = useAuth()
  const [repositories, setRepositories] = useState<Repository[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (isAuthenticated && accessToken) {
      fetchRepositories()
    }
  }, [isAuthenticated, accessToken])

  const fetchRepositories = async () => {
    try {
      const response = await fetch(`${(import.meta as any).env.VITE_API_URL}/api/user/repositories`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setRepositories(data)
      }
    } catch (error) {
      console.error('Failed to fetch repositories:', error)
    } finally {
      setLoading(false)
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-figma-black flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-figma-text-primary mb-4">
            Please sign in to view your dashboard
          </h1>
          <p className="text-figma-text-secondary">
            Sign in with GitHub to deploy AI agents to your repositories
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-figma-black py-8">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-figma-text-primary mb-2">
            Welcome back, {user?.name || user?.login}!
          </h1>
          <p className="text-figma-text-secondary">
            Deploy AI agents to your GitHub repositories and manage your automated workflows
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div>
            <h2 className="text-xl font-semibold text-figma-text-primary mb-4">
              Your Repositories
            </h2>
            {loading ? (
              <div className="text-figma-text-secondary">Loading repositories...</div>
            ) : (
              <div className="space-y-4">
                {repositories.slice(0, 10).map((repo) => (
                  <div key={repo.id} className="bg-figma-medium-gray border border-figma-light-gray rounded-lg p-4">
                    <div className="mb-3">
                      <h3 className="text-figma-text-primary text-lg font-medium">
                        {repo.name}
                      </h3>
                      <p className="text-figma-text-secondary text-sm">
                        {repo.description || 'No description available'}
                      </p>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4 text-sm text-figma-text-secondary">
                        <div className="flex items-center space-x-1">
                          <span>⭐</span>
                          <span>{repo.stargazers_count}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <span>🍴</span>
                          <span>{repo.forks_count}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <span>📅</span>
                          <span>{new Date(repo.updated_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <button 
                        className="text-figma-text-secondary border border-figma-light-gray hover:bg-figma-light-gray px-3 py-1 rounded text-sm"
                        onClick={() => window.open(repo.html_url, '_blank')}
                      >
                        View on GitHub
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <h2 className="text-xl font-semibold text-figma-text-primary mb-4">
              Deployed Agents
            </h2>
            <div className="bg-figma-medium-gray border border-figma-light-gray rounded-lg p-6">
              <div className="text-center text-figma-text-secondary">
                <p>No agents deployed yet.</p>
                <p className="mt-2">Browse templates and deploy your first AI agent!</p>
                <Link to="/templates">
                  <button className="mt-4 bg-white text-black hover:bg-gray-200 px-4 py-2 rounded-md">
                    Browse Templates
                  </button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
