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
  language?: string
  default_branch?: string
}

export function UserDashboard() {
  const { user, accessToken, isAuthenticated } = useAuth()
  const [repositories, setRepositories] = useState<Repository[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<Repository[] | null>(null)
  const [searchLoading, setSearchLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const [searchPage, setSearchPage] = useState(1)
  const [searchHasMore, setSearchHasMore] = useState(true)

  useEffect(() => {
    if (isAuthenticated && accessToken) {
      fetchRepositories()
    }
  }, [isAuthenticated, accessToken])

  const fetchRepositories = async (nextPage = 1, append = false) => {
    try {
      const url = `${(import.meta as any).env.VITE_API_URL}/api/user/repositories?limit=10&page=${nextPage}`
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setRepositories((prev) => append ? [...prev, ...data] : data)
        setHasMore(Array.isArray(data) && data.length === 10)
        setPage(nextPage)
      }
    } catch (error) {
      console.error('Failed to fetch repositories:', error)
    } finally {
      setLoading(false)
    }
  }

  // Debounced search
  useEffect(() => {
    if (!isAuthenticated || !accessToken) return
    const controller = new AbortController()
    const handler = setTimeout(async () => {
      const q = searchQuery.trim()
      if (q.length < 2) {
        setSearchResults(null)
        setSearchLoading(false)
        setSearchPage(1)
        setSearchHasMore(true)
        return
      }
      try {
        setSearchLoading(true)
        const url = `${(import.meta as any).env.VITE_API_URL}/api/user/repositories/search?q=${encodeURIComponent(q)}&limit=10&page=1`
        const response = await fetch(url, {
          headers: { 'Authorization': `Bearer ${accessToken}` },
          signal: controller.signal
        })
        if (response.ok) {
          const data = await response.json()
          setSearchResults(data)
          setSearchHasMore(Array.isArray(data) && data.length === 10)
          setSearchPage(1)
        }
      } catch (e) {
        if ((e as any).name !== 'AbortError') {
          console.error('Search failed:', e)
        }
      } finally {
        setSearchLoading(false)
      }
    }, 300)
    return () => {
      controller.abort()
      clearTimeout(handler)
    }
  }, [searchQuery, isAuthenticated, accessToken])

  const loadMoreRecent = async () => {
    await fetchRepositories(page + 1, true)
  }

  const loadMoreSearch = async () => {
    if (!searchResults) return
    const nextPage = searchPage + 1
    try {
      setSearchLoading(true)
      const url = `${(import.meta as any).env.VITE_API_URL}/api/user/repositories/search?q=${encodeURIComponent(searchQuery.trim())}&limit=10&page=${nextPage}`
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${accessToken}` }
      })
      if (response.ok) {
        const data: Repository[] = await response.json()
        setSearchResults([...searchResults, ...data])
        setSearchHasMore(Array.isArray(data) && data.length === 10)
        setSearchPage(nextPage)
      }
    } catch (e) {
      console.error('Load more search failed:', e)
    } finally {
      setSearchLoading(false)
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
            <h2 className="text-xl font-semibold text-figma-text-primary mb-1">
              Your Repositories
            </h2>
            <p className="text-xs text-figma-text-secondary mb-4">
              Showing your 10 most recently updated repositories. Use search to find others.
            </p>

            <div className="mb-4 flex items-center gap-2">
              <input
                className="w-full bg-figma-medium-gray border border-figma-light-gray rounded px-3 py-2 text-sm text-figma-text-primary placeholder-figma-text-secondary focus:outline-none"
                placeholder="Search your repositories (min 2 chars)"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button
                  className="text-figma-text-secondary border border-figma-light-gray hover:bg-figma-light-gray px-3 py-2 rounded text-sm"
                  onClick={() => setSearchQuery('')}
                >
                  Clear
                </button>
              )}
            </div>

            {loading ? (
              <div className="text-figma-text-secondary">Loading repositories...</div>
            ) : (
              <div className="space-y-4">
                {(searchResults ?? repositories).map((repo) => (
                  <div key={repo.id} className="bg-figma-medium-gray border border-figma-light-gray rounded-lg p-4">
                    <div className="mb-3">
                      <div className="flex items-center gap-2">
                        <h3 className="text-figma-text-primary text-lg font-medium">
                          {repo.name}
                        </h3>
                        <a
                          href={repo.html_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          aria-label="View on GitHub"
                          title="View on GitHub"
                          className="text-figma-text-secondary hover:text-figma-text-primary"
                        >
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 16 16"
                            width="16"
                            height="16"
                            fill="currentColor"
                            aria-hidden="true"
                          >
                            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49C3.73 14.91 3.27 13.73 3.27 13.73c-.36-.91-.88-1.15-.88-1.15-.72-.49.06-.48.06-.48.79.06 1.21.82 1.21.82.71 1.21 1.87.86 2.33.66.07-.51.28-.86.51-1.06-2.66-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.12-.3-.54-1.52.12-3.17 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 0 1 3.01-.4c1.02 0 2.05.14 3.01.4 2.29-1.55 3.3-1.23 3.3-1.23.66 1.65.24 2.87.12 3.17.77.84 1.24 1.91 1.24 3.22 0 4.61-2.81 5.62-5.49 5.92.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8Z"/>
                          </svg>
                        </a>
                      </div>
                      <p className="text-figma-text-secondary text-sm">
                        {repo.description || 'No description available'}
                      </p>
                    </div>
                    <div className="flex items-center justify-start">
                      <div className="flex items-center space-x-4 text-sm text-figma-text-secondary">
                        <span className={`px-2 py-0.5 rounded border ${repo.private ? 'border-red-400 text-red-300' : 'border-green-400 text-green-300'}`}>
                          {repo.private ? 'Private' : 'Public'}
                        </span>
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
                        {repo.language && (
                          <div className="flex items-center space-x-1">
                            <span>🗣️</span>
                            <span>{repo.language}</span>
                          </div>
                        )}
                        {repo.default_branch && (
                          <div className="flex items-center space-x-1">
                            <span>🌿</span>
                            <span>{repo.default_branch}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                {searchResults && !searchLoading && searchResults.length === 0 && (
                  <div className="text-figma-text-secondary text-sm">No repositories match "{searchQuery}"</div>
                )}
                {searchLoading && (
                  <div className="text-figma-text-secondary text-sm">Searching…</div>
                )}
                {!searchResults && hasMore && (
                  <div className="flex justify-center">
                    <button
                      className="text-figma-text-secondary border border-figma-light-gray hover:bg-figma-light-gray px-4 py-2 rounded text-sm"
                      onClick={loadMoreRecent}
                    >
                      Load more
                    </button>
                  </div>
                )}
                {searchResults && searchHasMore && (
                  <div className="flex justify-center">
                    <button
                      className="text-figma-text-secondary border border-figma-light-gray hover:bg-figma-light-gray px-4 py-2 rounded text-sm"
                      onClick={loadMoreSearch}
                      disabled={searchLoading}
                    >
                      {searchLoading ? 'Loading…' : 'Load more'}
                    </button>
                  </div>
                )}
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
