import { SEAgentFactoryLogo } from './SEAgentFactoryLogo'

export function Header() {
  return (
    <header className="bg-figma-black border-b border-figma-medium-gray">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <SEAgentFactoryLogo className="w-6 h-6" />
            <div className="flex flex-col md:flex-row md:items-center">
              <span className="text-lg font-medium text-figma-text-primary">Foundry Apps</span>
              <span className="text-sm text-figma-text-secondary md:ml-4 md:pl-4 md:border-l md:border-figma-light-gray">
                Customize AI solution accelerators for your scenario using SWE Agents
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
