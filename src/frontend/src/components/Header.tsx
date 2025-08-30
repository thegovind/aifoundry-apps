import { SEAgentFactoryLogo } from './SEAgentFactoryLogo'
import { useAuth } from '../contexts/AuthContext'
import { Link } from 'react-router-dom'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from './ui/dropdown-menu'

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
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button className="flex items-center gap-2 border border-figma-light-gray hover:bg-figma-medium-gray px-3 py-1.5 rounded-full">
                      <img
                        src={user?.avatar_url}
                        alt={user?.login}
                        className="w-8 h-8 rounded-full"
                      />
                      <span className="text-figma-text-secondary text-sm">{user?.login}</span>
                      {/* simple caret */}
                      <svg width="12" height="12" viewBox="0 0 20 20" fill="currentColor" className="text-figma-text-secondary">
                        <path d="M5.23 7.21a.75.75 0 0 1 1.06.02L10 10.143l3.71-2.912a.75.75 0 1 1 .94 1.166l-4.2 3.296a.75.75 0 0 1-.94 0l-4.2-3.296a.75.75 0 0 1-.02-1.06z" />
                      </svg>
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="bg-figma-medium-gray border-figma-light-gray text-figma-text-primary">
                    <DropdownMenuLabel className="text-xs text-figma-text-secondary">Signed in as <span className="text-figma-text-primary">{user?.login}</span></DropdownMenuLabel>
                    <DropdownMenuSeparator className="bg-figma-light-gray" />
                    <DropdownMenuItem asChild>
                      <Link to="/" className="cursor-pointer">Home</Link>
                    </DropdownMenuItem>
                    <DropdownMenuItem asChild>
                      <Link to="/dashboard" className="cursor-pointer">Dashboard</Link>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator className="bg-figma-light-gray" />
                    <DropdownMenuItem onSelect={() => logout()} className="cursor-pointer text-red-300 focus:text-red-300">
                      Sign Out
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            ) : (
              <button
                onClick={login}
                aria-label="Sign in with GitHub"
                className="group flex items-center gap-2 bg-black text-white px-4 py-2 rounded-full text-sm font-medium border border-gray-700 shadow-sm transition-all duration-200 hover:border-white/80 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-white/70 focus:ring-offset-2 focus:ring-offset-figma-black"
              >
                {/* GitHub mark */}
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  width="20"
                  height="20"
                  fill="currentColor"
                  stroke="none"
                  aria-hidden="true"
                  focusable="false"
                  className="text-white fill-white block"
                  shapeRendering="geometricPrecision"
                >
                  <path d="M12 .297C5.37.297 0 5.667 0 12.297c0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.016-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.387-1.333-1.756-1.333-1.756-1.09-.745.083-.73.083-.73 1.205.085 1.84 1.237 1.84 1.237 1.07 1.835 2.807 1.305 3.492.998.108-.775.42-1.306.763-1.606-2.665-.305-5.466-1.332-5.466-5.93 0-1.31.468-2.382 1.236-3.222-.124-.303-.536-1.524.116-3.176 0 0 1.008-.322 3.3 1.23.957-.266 1.984-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.29-1.552 3.296-1.23 3.296-1.23.654 1.652.242 2.873.118 3.176.77.84 1.235 1.912 1.235 3.222 0 4.61-2.806 5.624-5.479 5.92.43.372.816 1.102.816 2.222 0 1.606-.014 2.902-.014 3.296 0 .322.216.694.826.576C20.565 22.094 24 17.6 24 12.297 24 5.667 18.627.297 12 .297z"/>
                </svg>
                Sign in with GitHub
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
