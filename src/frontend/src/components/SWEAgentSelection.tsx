import { useState } from 'react'
import { ExternalLink, Loader2 } from 'lucide-react'
import { SiOpenai, SiReplit } from 'react-icons/si'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'

interface SWEAgent {
  id: string
  name: string
  description: string
  icon: string | React.ReactNode
  requiresApiKey: boolean
  configType?: 'api-key' | 'pat' | 'azure-openai' | 'azure-marketplace'
  instructions?: string
  comingSoon?: boolean
}

interface SWEAgentSelectionProps {
  selectedAgent: string
  setSelectedAgent: (agent: string) => void
  apiKey: string
  setApiKey: (key: string) => void
  customization: any
  workflowMode: 'breakdown' | 'oneshot'
  selectedTasks: Set<string>
  isAssigningTasks: boolean
  onAssignToSWEAgent: () => void
  validationField: string // The field name to validate (e.g., 'customer_scenario' or 'scenarioDescription')
}

const CognitionLogo = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="110 110 460 500">
    <path d="M418.73,332.37c9.84-5.68,22.07-5.68,31.91,0l25.49,14.71c.82.48,1.69.8,2.58,1.06.19.06.37.11.55.16.87.21,1.76.34,2.65.35.04,0,.08.02.13.02.1,0,.19-.03.29-.04.83-.02,1.64-.13,2.45-.32.14-.03.28-.05.42-.09.87-.24,1.7-.59,2.5-1.03.08-.04.17-.06.25-.1l50.97-29.43c3.65-2.11,5.9-6.01,5.9-10.22v-58.86c0-4.22-2.25-8.11-5.9-10.22l-50.97-29.43c-3.65-2.11-8.15-2.11-11.81,0l-50.97,29.43c-.08.04-.13.11-.2.16-.78.48-1.51,1.02-2.15,1.66-.1.1-.18.21-.28.31-.57.6-1.08,1.26-1.51,1.97-.07.12-.15.22-.22.34-.44.77-.77,1.6-1.03,2.47-.05.19-.1.37-.14.56-.22.89-.37,1.81-.37,2.76v29.43c0,11.36-6.11,21.95-15.95,27.63-9.84,5.68-22.06,5.68-31.91,0l-25.49-14.71c-.82-.48-1.69-.8-2.57-1.06-.19-.06-.37-.11-.56-.16-.88-.21-1.76-.34-2.65-.34-.13,0-.26.02-.4.02-.84.02-1.66.13-2.47.32-.13.03-.27.05-.4.09-.87.24-1.71.6-2.51,1.04-.08.04-.16.06-.24.1l-50.97,29.43c-3.65,2.11-5.9,6.01-5.9,10.22v58.86c0,4.22,2.25,8.11,5.9,10.22l50.97,29.43c.08.04.17.06.24.1.8.44,1.64.79,2.5,1.03.14.04.28.06.42.09.81.19,1.62.3,2.45.32.1,0,.19.04.29.04.04,0,.08-.02.13-.02.89,0,1.77-.13,2.65-.35.19-.04.37-.1.56-.16.88-.26,1.75-.59,2.58-1.06l25.49-14.71c9.84-5.68,22.06-5.68,31.91,0,9.84,5.68,15.95,16.27,15.95,27.63v29.43c0,.95.15,1.87.37,2.76.05.19.09.37.14.56.25.86.59,1.69,1.03,2.47.07.12.15.22.22.34.43.71.94,1.37,1.51,1.97.1.1.18.21.28.31.65.63,1.37,1.18,2.15,1.66.07.04.13.11.2.16l50.97,29.43c1.83,1.05,3.86,1.58,5.9,1.58s4.08-.53,5.9-1.58l50.97-29.43c3.65-2.11,5.9-6.01,5.9-10.22v-58.86c0-4.22-2.25-8.11-5.9-10.22l-50.97-29.43c-.08-.04-.16-.06-.24-.1-.8-.44-1.64-.8-2.51-1.04-.13-.04-.26-.05-.39-.09-.82-.2-1.65-.31-2.49-.33-.13,0-.25-.02-.38-.02-.89,0-1.78.13-2.66.35-.18.04-.36.1-.54.15-.88.26-1.75.59-2.58,1.07l-25.49,14.72c-9.84,5.68-22.07,5.68-31.9,0-9.84-5.68-15.95-16.27-15.95-27.63s6.11-21.95,15.95-27.63Z" fill="currentColor"/>
    <path d="M141.09,317.65l50.97,29.43c1.83,1.05,3.86,1.58,5.9,1.58s4.08-.53,5.9-1.58l50.97-29.43c.08-.04.13-.11.2-.16.78-.48,1.51-1.02,2.15-1.66.1-.1.18-.21.28-.31.57-.6,1.08-1.26,1.51-1.97.07-.12.15-.22.22-.34.44-.77.77-1.6,1.03-2.47.05-.19.1-.37.14-.56.22-.89.37-1.81.37-2.76v-29.43c0-11.36,6.11-21.95,15.96-27.63s22.06-5.68,31.91,0l25.49,14.71c.82.48,1.69.8,2.57,1.06.19.06.37.11.56.16.87.21,1.76.34,2.64.35.04,0,.09.02.13.02.1,0,.19-.04.29-.04.83-.02,1.65-.13,2.45-.32.14-.03.28-.05.41-.09.87-.24,1.71-.6,2.51-1.04.08-.04.16-.06.24-.1l50.97-29.43c3.65-2.11,5.9-6.01,5.9-10.22v-58.86c0-4.22-2.25-8.11-5.9-10.22l-50.97-29.43c-3.65-2.11-8.15-2.11-11.81,0l-50.97,29.43c-.08.04-.13.11-.2.16-.78.48-1.51,1.02-2.15,1.66-.1.1-.18.21-.28.31-.57.6-1.08,1.26-1.51,1.97-.07.12-.15.22-.22.34-.44.77-.77,1.6-1.03,2.47-.05.19-.1.37-.14.56-.22.89-.37,1.81-.37,2.76v29.43c0,11.36-6.11,21.95-15.95,27.63-9.84,5.68-22.07,5.68-31.91,0l-25.49-14.71c-.82-.48-1.69-.8-2.58-1.06-.19-.06-.37-.11-.55-.16-.88-.21-1.76-.34-2.65-.35-.13,0-.26.02-.4.02-.83.02-1.66.13-2.47.32-.13.03-.27.05-.4.09-.87.24-1.71.6-2.51,1.04-.08.04-.16.06-.24.1l-50.97,29.43c-3.65,2.11-5.9,6.01-5.9,10.22v58.86c0,4.22,2.25,8.11,5.9,10.22Z" fill="currentColor"/>
    <path d="M396.88,484.35l-50.97-29.43c-.08-.04-.17-.06-.24-.1-.8-.44-1.64-.79-2.51-1.03-.14-.04-.27-.06-.41-.09-.81-.19-1.64-.3-2.47-.32-.13,0-.26-.02-.39-.02-.89,0-1.78.13-2.66.35-.18.04-.36.1-.54.15-.88.26-1.76.59-2.58,1.07l-25.49,14.72c-9.84,5.68-22.06,5.68-31.9,0-9.84-5.68-15.96-16.27-15.96-27.63v-29.43c0-.95-.15-1.87-.37-2.76-.05-.19-.09-.37-.14-.56-.25-.86-.59-1.69-1.03-2.47-.07-.12-.15-.22-.22-.34-.43-.71-.94-1.37-1.51-1.97-.1-.1-.18-.21-.28-.31-.65-.63-1.37-1.18-2.15-1.66-.07-.04-.13-.11-.2-.16l-50.97-29.43c-3.65-2.11-8.15-2.11-11.81,0l-50.97,29.43c-3.65,2.11-5.9,6.01-5.9,10.22v58.86c0,4.22,2.25,8.11,5.9,10.22l50.97,29.43c.08.04.17.06.25.1.8.44,1.63.79,2.5,1.03.14.04.29.06.43.09.8.19,1.61.3,2.43.32.1,0,.2.04.3.04.04,0,.09-.02.13-.02.88,0,1.77-.13,2.64-.34.19-.04.37-.1.56-.16.88-.26,1.75-.59,2.57-1.06l25.49-14.71c9.84-5.68,22.06-5.68,31.91,0,9.84,5.68,15.95,16.27,15.95,27.63v29.43c0,.95.15,1.87.37,2.76.05.19.09.37.14.56.25.86.59,1.69,1.03,2.47.07.12.15.22.22.34.43.71.94,1.37,1.51,1.97.1.1.18.21.28.31.65.63,1.37,1.18,2.15,1.66.07.04.13.11.2.16l50.97,29.43c1.83,1.05,3.86,1.58,5.9,1.58s4.08-.53,5.9-1.58l50.97-29.43c3.65-2.11,5.9-6.01,5.9-10.22v-58.86c0-4.22-2.25-8.11-5.9-10.22Z" fill="currentColor"/>
  </svg>
)

const sweAgents: SWEAgent[] = [
  {
    id: 'github-copilot',
    name: 'GitHub Copilot Coding Agent',
    description: 'AI pair programmer integrated with GitHub via MCP',
    icon: <ExternalLink className="w-6 h-6 text-white" />,
    requiresApiKey: true,
    configType: 'pat',
    instructions: 'Generate a Personal Access Token (PAT) from GitHub Settings > Developer settings > Personal access tokens. The agent is invoked via Model Context Protocol (MCP) for seamless integration.'
  },
  {
    id: 'codex-cli',
    name: 'Azure OpenAI Codex w/ GitHub Actions',
    description: 'Azure OpenAI Codex model with GitHub Actions workflow automation',
    icon: <SiOpenai className="w-6 h-6 text-white" />,
    requiresApiKey: true,
    configType: 'azure-openai',
    instructions: 'Deploy Azure OpenAI Codex model at ai.azure.com. Go to Azure AI Studio > Deployments > Create new deployment > Select Codex model. You need the API Key and Endpoint. GitHub Actions workflows will be automatically created for your tasks.'
  },
  {
    id: 'devin',
    name: 'Devin',
    description: 'Advanced AI software engineer for complex coding tasks',
    icon: <CognitionLogo className="w-6 h-6 text-white" />,
    requiresApiKey: true,
    configType: 'azure-marketplace',
    instructions: 'First provision Devin from Azure Marketplace, then get your API key from https://app.devin.ai/settings/api-keys. The API key is required to authenticate with the Devin service for advanced coding tasks.'
  },
  {
    id: 'replit',
    name: 'Replit Agent',
    description: 'Coming Soon on Azure Marketplace',
    icon: <SiReplit className="w-6 h-6 text-white" />,
    requiresApiKey: false,
    comingSoon: true
  }
]

export function SWEAgentSelection({
  selectedAgent,
  setSelectedAgent,
  apiKey,
  setApiKey,
  customization,
  workflowMode,
  selectedTasks,
  isAssigningTasks,
  onAssignToSWEAgent,
  validationField
}: SWEAgentSelectionProps) {
  const [endpoint, setEndpoint] = useState<string>('')

  const isFormValid = customization[validationField] && apiKey

  return (
    <Card className="bg-figma-medium-gray border-figma-light-gray">
      <CardHeader>
        <CardTitle className="text-figma-text-primary">SWE Agent Selection</CardTitle>
        <CardDescription className="text-figma-text-secondary">
          Choose an AI agent to handle the implementation
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 gap-3">
          {sweAgents.map((agent) => (
            <div
              key={agent.id}
              className={`p-3 rounded border cursor-pointer transition-colors ${
                selectedAgent === agent.id
                  ? 'border-figma-light-gray bg-figma-dark-gray'
                  : 'border-figma-light-gray hover:border-figma-light-gray'
              }`}
              onClick={() => setSelectedAgent(agent.id)}
            >
              <div className="flex items-center space-x-3">
                <span className="text-2xl">{agent.icon}</span>
                <div className="flex-1">
                  <h4 className="text-figma-text-primary font-medium">{agent.name}</h4>
                  <p className="text-figma-text-secondary text-sm">{agent.description}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {selectedAgent && (() => {
          const agent = sweAgents.find(a => a.id === selectedAgent)
          if (!agent) return null
          
          if (agent.comingSoon) {
            return (
              <div className="p-4 bg-yellow-900/20 border border-yellow-600 rounded-lg">
                <p className="text-yellow-400 text-sm font-medium">Coming Soon on Azure Marketplace</p>
                <p className="text-figma-text-secondary text-xs mt-1">This agent will be available soon through Azure Marketplace integration.</p>
              </div>
            )
          }
          
          if (agent.configType === 'azure-marketplace') {
            return (
              <div className="space-y-3">
                <div className="p-3 bg-blue-900/20 border border-blue-600 rounded-lg">
                  <p className="text-blue-400 text-sm font-medium mb-2">Azure Marketplace Setup Required:</p>
                  <ol className="text-figma-text-primary text-xs space-y-1 list-decimal list-inside">
                    <li>Provision Devin from Azure Marketplace</li>
                    <li>Get your API key from <a href="https://app.devin.ai/settings/api-keys" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 underline">app.devin.ai/settings/api-keys</a></li>
                  </ol>
                </div>
                <div>
                  <Label htmlFor="apiKey" className="text-figma-text-primary">Devin API Key</Label>
                  <Input
                    id="apiKey"
                    type="password"
                    placeholder="Enter your Devin API key..."
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="bg-figma-input-gray border-figma-light-gray text-figma-text-primary placeholder-figma-text-secondary"
                  />
                </div>
                {/* Assignment Button */}
                <Button
                  onClick={() => onAssignToSWEAgent()}
                  disabled={!isFormValid || (workflowMode === 'breakdown' && selectedTasks.size === 0) || isAssigningTasks}
                  className="w-full bg-white text-black hover:bg-gray-200 border border-gray-300"
                >
                  {isAssigningTasks ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Assigning...
                    </>
                  ) : (
                    workflowMode === 'breakdown' 
                      ? `Assign Selected Tasks (${selectedTasks.size})` 
                      : 'Assign One-Shot Implementation'
                  )}
                </Button>
              </div>
            )
          }
          
          if (agent.requiresApiKey) {
            return (
              <div className="space-y-3">
                <div>
                  <Label htmlFor="apiKey" className="text-figma-text-primary">
                    {agent.configType === 'pat' ? 'Personal Access Token (PAT)' : 
                     agent.configType === 'azure-openai' ? 'API Key & Endpoint' : 'API Key'}
                  </Label>
                  <Input
                    id="apiKey"
                    type="password"
                    placeholder={
                      agent.configType === 'pat' ? 'Enter your GitHub PAT...' :
                      agent.configType === 'azure-openai' ? 'Enter your Azure OpenAI API Key...' :
                      'Enter your API key...'
                    }
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="bg-figma-input-gray border-figma-light-gray text-figma-text-primary placeholder-figma-text-secondary"
                  />
                </div>
                
                {agent.configType === 'azure-openai' && (
                  <div>
                    <Label htmlFor="endpoint" className="text-figma-text-primary">Azure OpenAI Endpoint</Label>
                    <Input
                      id="endpoint"
                      type="text"
                      placeholder="https://your-resource.openai.azure.com/"
                      value={endpoint}
                      onChange={(e) => setEndpoint(e.target.value)}
                      className="bg-figma-input-gray border-figma-light-gray text-figma-text-primary placeholder-figma-text-secondary"
                    />
                  </div>
                )}
                
                {agent.instructions && (
                  <div className="p-3 bg-blue-900/20 border border-blue-600 rounded-lg">
                    <p className="text-blue-400 text-sm font-medium mb-1">Setup Instructions:</p>
                    <p className="text-figma-text-primary text-xs">{agent.instructions}</p>
                  </div>
                )}

                {/* Assignment Button */}
                <Button
                  onClick={() => onAssignToSWEAgent()}
                  disabled={!isFormValid || (workflowMode === 'breakdown' && selectedTasks.size === 0) || isAssigningTasks}
                  className="w-full bg-white text-black hover:bg-gray-200 border border-gray-300"
                >
                  {isAssigningTasks ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Assigning...
                    </>
                  ) : (
                    workflowMode === 'breakdown' 
                      ? `Assign Selected Tasks (${selectedTasks.size})` 
                      : 'Assign One-Shot Implementation'
                  )}
                </Button>
              </div>
            )
          }
          
          return null
        })()}
      </CardContent>
    </Card>
  )
} 