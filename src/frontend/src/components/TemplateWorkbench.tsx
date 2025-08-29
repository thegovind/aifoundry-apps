import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Settings, GitBranch, Loader2 } from 'lucide-react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Textarea } from './ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { Badge } from './ui/badge'
import { Checkbox } from './ui/checkbox'
import { Template } from '../App'
import { SWEAgentSelection } from './SWEAgentSelection'

interface CustomizationRequest {
  customer_scenario: string
  brand_theme: string
  primary_color: string
  company_name: string
  industry: string
  use_case: string
  additional_requirements: string
  use_mcp_tools: boolean
  use_a2a: boolean
}

interface TaskBreakdown {
  id: string
  title: string
  description: string
  estimatedTime: string
  estimatedTokens: string
  priority: 'high' | 'medium' | 'low'
  status: 'pending' | 'assigned' | 'completed'
}

export function TemplateWorkbench() {
  const { templateId } = useParams<{ templateId: string }>()
  const [template, setTemplate] = useState<Template | null>(null)
  const [loading, setLoading] = useState(true)
  const [customization, setCustomization] = useState<CustomizationRequest>({
    customer_scenario: '',
    brand_theme: '',
    primary_color: '#3b82f6',
    company_name: '',
    industry: '',
    use_case: '',
    additional_requirements: '',
    use_mcp_tools: false,
    use_a2a: false
  })
  const [selectedTasks, setSelectedTasks] = useState<Set<string>>(new Set())
  const [selectedAgent, setSelectedAgent] = useState<string>('')
  const [apiKey, setApiKey] = useState<string>('')
  const [taskBreakdown, setTaskBreakdown] = useState<TaskBreakdown[]>([])
  const [isGeneratingTasks, setIsGeneratingTasks] = useState(false)
  const [isAssigningTasks, setIsAssigningTasks] = useState(false)
  const [workflowMode, setWorkflowMode] = useState<'breakdown' | 'oneshot'>('oneshot')
  const [assignmentResponse, setAssignmentResponse] = useState<any>(null)

  const apiUrl = import.meta.env.VITE_API_URL

  useEffect(() => {
    if (templateId) {
      fetchTemplate()
    }
  }, [templateId])

  const fetchTemplate = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/templates/${templateId}`)
      if (response.ok) {
        const data = await response.json()
        setTemplate(data)
      }
    } catch (error) {
      console.error('Error fetching template:', error)
    } finally {
      setLoading(false)
    }
  }

  const generateTaskBreakdown = async () => {
    setIsGeneratingTasks(true)
    try {
      const requestPayload = {
        customer_scenario: customization.customer_scenario,
        company_name: customization.company_name,
        industry: customization.industry,
        brand_theme: customization.brand_theme,
        primary_color: customization.primary_color,
        use_case: customization.use_case,
        additional_requirements: customization.additional_requirements,
        use_mcp_tools: customization.use_mcp_tools,
        use_a2a: customization.use_a2a
      }
      
      const response = await fetch(`${apiUrl}/api/templates/${templateId}/breakdown`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestPayload)
      })
      
      if (response.ok) {
        const tasks = await response.json()
        setTaskBreakdown(tasks)
      }
    } catch (error) {
      console.error('Error generating task breakdown:', error)
    } finally {
      setIsGeneratingTasks(false)
    }
  }

  const assignToSWEAgent = async (taskId?: string) => {
    if (!selectedAgent || !apiKey) return

    setIsAssigningTasks(true)
    try {
      const payload = {
        agent_id: selectedAgent,
        api_key: apiKey,
        template_id: templateId,
        customization,
        ...(taskId ? { task_id: taskId } : { 
          mode: workflowMode === 'oneshot' ? 'oneshot' : 'breakdown'
        })
      }

      const response = await fetch(`${apiUrl}/api/templates/${templateId}/assign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      if (response.ok) {
        const result = await response.json()
        console.log('Assignment successful:', result)
        
        // Store the response for display
        setAssignmentResponse(result)
        
        if (!taskId && workflowMode === 'breakdown') {
          setSelectedTasks(new Set())
        }
      } else {
        const error = await response.json()
        console.error('Assignment failed:', error)
        
        // Store the error response for display
        setAssignmentResponse({
          status: 'error',
          message: error.detail || 'Unknown error occurred',
          agent: selectedAgent
        })
      }
    } catch (error) {
      console.error('Error assigning to SWE agent:', error)
      
      // Store the error response for display
      setAssignmentResponse({
        status: 'error',
        message: `Error assigning to SWE agent: ${error}`,
        agent: selectedAgent
      })
    } finally {
      setIsAssigningTasks(false)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <Loader2 className="h-8 w-8 animate-spin text-figma-text-secondary" />
        </div>
      </div>
    )
  }

  if (!template) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white mb-4">Template not found</h1>
          <Link to="/" className="text-figma-text-secondary hover:text-figma-text-primary">
            Return to templates
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-8 py-8">
      <div className="mb-6">
        <Link to="/" className="inline-flex items-center text-figma-text-secondary hover:text-figma-text-primary mb-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Templates
        </Link>
        
        <div className="flex items-center space-x-4 mb-6">
          <div className="text-4xl">{template.icon}</div>
          <div>
            <h1 className="text-3xl font-bold text-white">{template.title}</h1>
            <p className="text-gray-400 mt-2">{template.description}</p>
            <div className="flex items-center space-x-2 mt-3">
              <Badge variant="outline" className="bg-gray-700 text-gray-300 border-gray-600">
                {template.collection}
              </Badge>
              <Badge variant="outline" className="bg-gray-700 text-gray-300 border-gray-600">
                {template.task}
              </Badge>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-6">
                      <Card className="bg-figma-medium-gray border-figma-light-gray">
              <CardHeader>
                <CardTitle className="text-figma-text-primary flex items-center">
                  <Settings className="h-5 w-5 mr-2" />
                  Customization Details
                </CardTitle>
                <CardDescription className="text-figma-text-secondary">
                  Describe your customer scenario and customization requirements
                </CardDescription>
              </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="customerScenario" className="text-white">Customer Scenario</Label>
                <Textarea
                  id="customerScenario"
                  placeholder="Describe the customer use case, business requirements, and specific needs..."
                  value={customization.customer_scenario}
                  onChange={(e) => setCustomization(prev => ({ ...prev, customer_scenario: e.target.value }))}
                  className="bg-figma-input-gray border-figma-light-gray text-figma-text-primary placeholder-figma-text-secondary min-h-[120px]"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="companyName" className="text-white">Company Name</Label>
                  <Input
                    id="companyName"
                    placeholder="Contoso Corp"
                    value={customization.company_name}
                    onChange={(e) => setCustomization(prev => ({ ...prev, company_name: e.target.value }))}
                    className="bg-figma-input-gray border-figma-light-gray text-figma-text-primary placeholder-figma-text-secondary"
                  />
                </div>
                <div>
                  <Label htmlFor="industry" className="text-white">Industry</Label>
                  <Select value={customization.industry} onValueChange={(value) => setCustomization(prev => ({ ...prev, industry: value }))}>
                    <SelectTrigger className="bg-figma-input-gray border-figma-light-gray text-figma-text-primary">
                      <SelectValue placeholder="Select industry" />
                    </SelectTrigger>
                    <SelectContent className="bg-figma-input-gray border-figma-light-gray">
                      <SelectItem value="healthcare">Healthcare</SelectItem>
                      <SelectItem value="finance">Finance</SelectItem>
                      <SelectItem value="retail">Retail</SelectItem>
                      <SelectItem value="manufacturing">Manufacturing</SelectItem>
                      <SelectItem value="technology">Technology</SelectItem>
                      <SelectItem value="education">Education</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <Label htmlFor="brandTheme" className="text-white">Brand Theme & Guidelines</Label>
                <Textarea
                  id="brandTheme"
                  placeholder="Brand colors, fonts, styling preferences, UI/UX guidelines..."
                  value={customization.brand_theme}
                  onChange={(e) => setCustomization(prev => ({ ...prev, brand_theme: e.target.value }))}
                  className="bg-figma-input-gray border-figma-light-gray text-figma-text-primary placeholder-figma-text-secondary"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="primaryColor" className="text-white">Primary Color</Label>
                  <div className="flex items-center space-x-2">
                    <Input
                      id="primaryColor"
                      type="color"
                      value={customization.primary_color}
                      onChange={(e) => setCustomization(prev => ({ ...prev, primary_color: e.target.value }))}
                      className="w-12 h-10 bg-figma-input-gray border-figma-light-gray"
                    />
                    <Input
                      value={customization.primary_color}
                      onChange={(e) => setCustomization(prev => ({ ...prev, primary_color: e.target.value }))}
                      className="bg-figma-input-gray border-figma-light-gray text-figma-text-primary placeholder-figma-text-secondary"
                    />
                  </div>
                </div>
                <div>
                  <Label htmlFor="useCase" className="text-white">Primary Use Case</Label>
                  <Input
                    id="useCase"
                    placeholder="Customer support, data analysis, etc."
                    value={customization.use_case}
                    onChange={(e) => setCustomization(prev => ({ ...prev, use_case: e.target.value }))}
                    className="bg-figma-input-gray border-figma-light-gray text-figma-text-primary placeholder-figma-text-secondary"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="additionalRequirements" className="text-white">Additional Requirements</Label>
                <Textarea
                  id="additionalRequirements"
                  placeholder="Any specific technical requirements, integrations, or constraints..."
                  value={customization.additional_requirements}
                  onChange={(e) => setCustomization(prev => ({ ...prev, additional_requirements: e.target.value }))}
                  className="bg-figma-input-gray border-figma-light-gray text-figma-text-primary placeholder-figma-text-secondary"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="useMCPTools"
                    checked={customization.use_mcp_tools}
                    onCheckedChange={(checked) => setCustomization(prev => ({ ...prev, use_mcp_tools: !!checked }))}
                  />
                  <Label htmlFor="useMCPTools" className="text-white text-sm">
                    Use MCP Tools (Azure AI Foundry Agent Service)
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="useA2A"
                    checked={customization.use_a2a}
                    onCheckedChange={(checked) => setCustomization(prev => ({ ...prev, use_a2a: !!checked }))}
                  />
                  <Label htmlFor="useA2A" className="text-white text-sm">
                    Use A2A (Agent-to-Agent Communication)
                  </Label>
                </div>
              </div>

              {customization.use_mcp_tools && (
                <div className="mt-4 p-4 bg-blue-900/30 border border-blue-700 rounded-md">
                  <p className="text-blue-200 text-sm mb-2">
                    <strong>MCP Tools Integration:</strong> This will create a prompt for the SWE Agent to leverage MCP tools that Azure AI Foundry Agent service supports, enabling enhanced tool integration and workflow automation.
                  </p>
                  <ul className="text-blue-300 text-sm list-disc list-inside mb-3">
                    <li>Enhanced tool integration via Model Context Protocol</li>
                    <li>Azure AI Foundry Agent service compatibility</li>
                    <li>Automated workflow generation with MCP support</li>
                  </ul>
                  <p className="text-blue-300 text-xs">
                    The SWE Agent will be configured to use MCP tools for improved development workflows and Azure service integration.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="bg-figma-medium-gray border-figma-light-gray">
            <CardHeader>
              <CardTitle className="text-figma-text-primary flex items-center">
                <GitBranch className="h-5 w-5 mr-2" />
                Workflow Configuration
              </CardTitle>
              <CardDescription className="text-figma-text-secondary">
                Choose how to approach the customization task
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex space-x-4">
                <Button
                  variant="outline"
                  onClick={() => setWorkflowMode('breakdown')}
                  className={`flex-1 ${workflowMode === 'breakdown' ? 'bg-white text-black hover:bg-gray-100 border-white' : 'bg-figma-dark-gray text-figma-text-primary border-figma-light-gray hover:bg-figma-light-gray'}`}
                >
                  Task Breakdown
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setWorkflowMode('oneshot')}
                  className={`flex-1 ${workflowMode === 'oneshot' ? 'bg-white text-black hover:bg-gray-100 border-white' : 'bg-figma-dark-gray text-figma-text-primary border-figma-light-gray hover:bg-figma-light-gray'}`}
                >
                  One-Shot
                </Button>
              </div>

              {workflowMode === 'breakdown' && (
                <div className="space-y-4">
                  <Button
                    onClick={generateTaskBreakdown}
                    disabled={!customization.customer_scenario || isGeneratingTasks}
                    className="w-full"
                  >
                    {isGeneratingTasks ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Generating Tasks...
                      </>
                    ) : (
                      'Generate Task Breakdown'
                    )}
                  </Button>

                  {taskBreakdown.length > 0 && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <h4 className="text-white font-medium">Generated Tasks:</h4>
                        <div className="flex items-center space-x-2">
                          <Checkbox
                            checked={selectedTasks.size === taskBreakdown.length && taskBreakdown.length > 0}
                            onCheckedChange={(checked) => {
                              if (checked) {
                                setSelectedTasks(new Set(taskBreakdown.map(task => task.id)))
                              } else {
                                setSelectedTasks(new Set())
                              }
                            }}
                          />
                          <span className="text-white text-sm">Select All</span>
                        </div>
                      </div>
                      {taskBreakdown.map((task) => (
                        <div key={task.id} className="bg-figma-dark-gray p-3 rounded border border-figma-light-gray">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center space-x-2">
                              <Checkbox
                                checked={selectedTasks.has(task.id)}
                                onCheckedChange={(checked) => {
                                  const newSelected = new Set(selectedTasks)
                                  if (checked) {
                                    newSelected.add(task.id)
                                  } else {
                                    newSelected.delete(task.id)
                                  }
                                  setSelectedTasks(newSelected)
                                }}
                              />
                              <h5 className="text-figma-text-primary font-medium">{task.title}</h5>
                            </div>
                            <Badge variant={task.priority === 'high' ? 'destructive' : task.priority === 'medium' ? 'default' : 'secondary'}>
                              {task.priority}
                            </Badge>
                          </div>
                          <p className="text-figma-text-secondary text-sm mb-2">{task.description}</p>
                          <div className="flex items-center justify-between">
                            <span className="text-figma-text-secondary text-xs">Est. {task.estimatedTime}</span>
                            <span className="text-figma-text-secondary text-xs">Est. {task.estimatedTokens}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <SWEAgentSelection
            selectedAgent={selectedAgent}
            setSelectedAgent={setSelectedAgent}
            apiKey={apiKey}
            setApiKey={setApiKey}
            customization={customization}
            workflowMode={workflowMode}
            selectedTasks={selectedTasks}
            isAssigningTasks={isAssigningTasks}
            onAssignToSWEAgent={assignToSWEAgent}
            validationField="customer_scenario"
          />

          {assignmentResponse && (
            <Card className="bg-figma-medium-gray border-figma-light-gray">
              <CardHeader>
                <CardTitle className="text-figma-text-primary flex items-center">
                  <GitBranch className="h-5 w-5 mr-2" />
                  Assignment Response
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`p-4 rounded-lg border ${
                  assignmentResponse.status === 'success' 
                    ? 'bg-green-900/20 border-green-600' 
                    : assignmentResponse.status === 'partial_success'
                    ? 'bg-yellow-900/20 border-yellow-600'
                    : 'bg-red-900/20 border-red-600'
                }`}>
                  <div className="flex items-center mb-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      assignmentResponse.status === 'success' 
                        ? 'bg-green-100 text-green-800' 
                        : assignmentResponse.status === 'partial_success'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {assignmentResponse.status === 'success' ? 'Success' : 
                       assignmentResponse.status === 'partial_success' ? 'Partial Success' : 'Error'}
                    </span>
                    {assignmentResponse.agent && (
                      <span className="ml-2 text-figma-text-secondary text-sm">
                        Agent: {assignmentResponse.agent}
                      </span>
                    )}
                  </div>
                  <p className="text-figma-text-primary text-sm leading-relaxed">
                    {assignmentResponse.message}
                  </p>
                  {assignmentResponse.result && (
                    <div className="mt-3 p-3 bg-figma-dark-gray rounded border border-figma-light-gray">
                      <p className="text-figma-text-secondary text-xs mb-1">Response Details:</p>
                      <pre className="text-figma-text-primary text-xs overflow-x-auto">
                        {JSON.stringify(assignmentResponse.result, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
