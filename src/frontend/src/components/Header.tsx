import { SEAgentFactoryLogo } from './SEAgentFactoryLogo'
import { useAuth } from '../contexts/AuthContext'
import { Link } from 'react-router-dom'

export function Header() {
  const { user, login, logout, isAuthenticated } = useAuth()

  return (
    <header className="bg-figma-black border-b border-figma-medium-gray">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center space-x-3 hover:opacity-80 transition-opacity">
            <SEAgentFactoryLogo className="w-6 h-6" />
            <div className="flex flex-col md:flex-row md:items-center">
              <span className="text-lg font-medium text-figma-text-primary">Foundry Apps</span>
              <span className="text-sm text-figma-text-secondary md:ml-4 md:pl-4 md:border-l md:border-figma-light-gray">
                Customize AI solution accelerators for your scenario using SWE Agents
              </span>
            </div>
          </Link>
          
          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                <Link to="/">
                  <button className="text-figma-text-secondary hover:text-figma-text-primary px-3 py-2 rounded-md text-sm font-medium">
                    Home
                  </button>
                </Link>
                <Link to="/dashboard">
                  <button className="text-figma-text-secondary hover:text-figma-text-primary px-3 py-2 rounded-md text-sm font-medium">
                    Dashboard
                  </button>
                </Link>
                <div className="flex items-center space-x-2">
                  <img 
                    src={user?.avatar_url} 
                    alt={user?.login} 
                    className="w-8 h-8 rounded-full"
                  />
                  <span className="text-figma-text-secondary text-sm">{user?.login}</span>
                </div>
                <button 
                  onClick={logout}
                  className="text-figma-text-secondary border border-figma-light-gray hover:bg-figma-medium-gray px-3 py-2 rounded-md text-sm font-medium"
                >
                  Sign Out
                </button>
              </>
            ) : (
              <button 
                onClick={login}
                className="bg-white text-black hover:bg-gray-200 px-4 py-2 rounded-md text-sm font-medium"
              >
                Sign in with GitHub
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
