import { useState, useEffect, useCallback } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Settings, GitBranch, Loader2, Save, FileText } from 'lucide-react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Textarea } from './ui/textarea'
import { Badge } from './ui/badge'
import { Checkbox } from './ui/checkbox'
import { SWEAgentSelection } from './SWEAgentSelection'
import MDEditor from '@uiw/react-md-editor'

interface Spec {
  id: string
  title: string
  description: string
  content: string
  created_at: string
  updated_at: string
  tags: string[]
}

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
  priority: string
  status: string
}

export function SpecWorkbench() {
  const { specId } = useParams()
  const navigate = useNavigate()
  const isNewSpec = specId === 'new'

  const [spec, setSpec] = useState<Spec | null>(null)
  const [loading, setLoading] = useState(!isNewSpec)
  const [saving, setSaving] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [content, setContent] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [tagInput, setTagInput] = useState('')

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
  const [workflowMode, setWorkflowMode] = useState<'breakdown' | 'oneshot'>('breakdown')
  const [assignmentResponse, setAssignmentResponse] = useState<{ status: string; message: string; agent?: string } | null>(null)
  
  const apiUrl = import.meta.env.VITE_API_URL

  const fetchSpec = useCallback(async () => {
    try {
      const response = await fetch(`${apiUrl}/api/specs/${specId}`)
      if (response.ok) {
        const data = await response.json()
        setSpec(data)
        setTitle(data.title)
        setDescription(data.description)
        setContent(data.content)
        setTags(data.tags || [])
      }
    } catch (error) {
      console.error('Error fetching spec:', error)
    } finally {
      setLoading(false)
    }
  }, [specId, apiUrl])

  useEffect(() => {
    if (!isNewSpec && specId) {
      fetchSpec()
    }
  }, [specId, isNewSpec, fetchSpec])

  const saveSpec = async () => {
    setSaving(true)
    try {
      const specData = {
        title,
        description,
        content,
        tags
      }

      const url = isNewSpec ? `${apiUrl}/api/specs` : `${apiUrl}/api/specs/${specId}`
      const method = isNewSpec ? 'POST' : 'PUT'

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(specData)
      })

      if (response.ok) {
        const savedSpec = await response.json()
        if (isNewSpec) {
          navigate(`/spec/${savedSpec.id}`)
        } else {
          setSpec(savedSpec)
        }
      }
    } catch (error) {
      console.error('Error saving spec:', error)
    } finally {
      setSaving(false)
    }
  }

  const addTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()])
      setTagInput('')
    }
  }

  const removeTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove))
  }

  const generateTaskBreakdown = async () => {
    if (!spec && isNewSpec) {
      await saveSpec()
      return
    }

    setIsGeneratingTasks(true)
    try {
      const mappedCustomization = {
        ...customization,
        customer_scenario: customization.customer_scenario || `Implement specification: ${title}`,
        use_case: customization.use_case || 'Specification Implementation',
        additional_requirements: `${customization.additional_requirements}\n\nSpecification Content:\n${content}`
      }

      const response = await fetch(`${apiUrl}/api/specs/${spec?.id || specId}/breakdown`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(mappedCustomization)
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
      const mappedCustomization = {
        ...customization,
        customer_scenario: customization.customer_scenario || `Implement specification: ${title}`,
        use_case: customization.use_case || 'Specification Implementation',
        additional_requirements: `${customization.additional_requirements}\n\nSpecification Content:\n${content}`
      }

      const payload = {
        agent_id: selectedAgent,
        api_key: apiKey,
        template_id: spec?.id || specId,
        customization: mappedCustomization,
        ...(taskId ? { task_id: taskId } : { 
          mode: workflowMode === 'oneshot' ? 'oneshot' : 'breakdown'
        })
      }

      const response = await fetch(`${apiUrl}/api/specs/${spec?.id || specId}/assign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      if (response.ok) {
        const result = await response.json()
        console.log('Assignment successful:', result)
        setAssignmentResponse(result)
        
        if (!taskId && workflowMode === 'breakdown') {
          setSelectedTasks(new Set())
        }
      } else {
        const error = await response.json()
        console.error('Assignment failed:', error)
        setAssignmentResponse({
          status: 'error',
          message: error.detail || 'Unknown error occurred',
          agent: selectedAgent
        })
      }
    } catch (error) {
      console.error('Error assigning to SWE agent:', error)
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

  return (
    <div className="min-h-screen bg-figma-black">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-8">
        <div className="mb-6">
          <Link to="/specs" className="inline-flex items-center text-figma-text-secondary hover:text-figma-text-primary mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Specifications
          </Link>
          
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              <div className="text-4xl">📝</div>
              <div>
                <h1 className="text-3xl font-bold text-white">
                  {isNewSpec ? 'New Specification' : title || 'Specification'}
                </h1>
                <p className="text-gray-400 mt-2">
                  {isNewSpec ? 'Create a new specification with markdown editor' : description}
                </p>
              </div>
            </div>
            <Button 
              onClick={saveSpec} 
              disabled={saving || !title.trim()}
              className="bg-white text-black hover:bg-gray-200"
            >
              {saving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Save Specification
                </>
              )}
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="space-y-6">
            <Card className="bg-figma-medium-gray border-figma-light-gray">
              <CardHeader>
                <CardTitle className="text-figma-text-primary flex items-center">
                  <FileText className="h-5 w-5 mr-2" />
                  Specification Details
                </CardTitle>
                <CardDescription className="text-figma-text-secondary">
                  Define your specification with title, description, and content
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="title" className="text-white">Title</Label>
                  <Input
                    id="title"
                    placeholder="Enter specification title..."
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="bg-figma-input-gray border-figma-light-gray text-figma-text-primary placeholder-figma-text-secondary"
                  />
                </div>

                <div>
                  <Label htmlFor="description" className="text-white">Description</Label>
                  <Textarea
                    id="description"
                    placeholder="Brief description of the specification..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="bg-figma-input-gray border-figma-light-gray text-figma-text-primary placeholder-figma-text-secondary"
                  />
                </div>

                <div>
                  <Label className="text-white">Tags</Label>
                  <div className="flex items-center space-x-2 mb-2">
                    <Input
                      placeholder="Add tag..."
                      value={tagInput}
                      onChange={(e) => setTagInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && addTag()}
                      className="bg-figma-input-gray border-figma-light-gray text-figma-text-primary placeholder-figma-text-secondary"
                    />
                    <Button onClick={addTag} size="sm" variant="outline">
                      Add
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {tags.map((tag) => (
                      <Badge key={tag} variant="outline" className="bg-figma-dark-gray text-figma-text-secondary border-figma-light-gray">
                        {tag}
                        <button
                          onClick={() => removeTag(tag)}
                          className="ml-2 text-figma-text-secondary hover:text-white"
                        >
                          ×
                        </button>
                      </Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <Label className="text-white">Content (Markdown)</Label>
                  <div className="mt-2" data-color-mode="dark">
                    <MDEditor
                      value={content}
                      onChange={(val: string | undefined) => setContent(val || '')}
                      preview="edit"
                      hideToolbar={false}
                      textareaProps={{
                        placeholder: 'Write your specification in markdown...',
                        style: {
                          fontSize: 14,
                          backgroundColor: '#374151',
                          color: '#F9FAFB'
                        }
                      }}
                      height={300}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-figma-medium-gray border-figma-light-gray">
              <CardHeader>
                <CardTitle className="text-figma-text-primary flex items-center">
                  <Settings className="h-5 w-5 mr-2" />
                  Customization Details
                </CardTitle>
                <CardDescription className="text-figma-text-secondary">
                  Configure implementation requirements and preferences
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="customerScenario" className="text-white">Implementation Scenario</Label>
                  <Textarea
                    id="customerScenario"
                    placeholder="Describe the implementation context, requirements, and specific needs..."
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
                    <Input
                      id="industry"
                      placeholder="Technology, Healthcare, etc."
                      value={customization.industry}
                      onChange={(e) => setCustomization(prev => ({ ...prev, industry: e.target.value }))}
                      className="bg-figma-input-gray border-figma-light-gray text-figma-text-primary placeholder-figma-text-secondary"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="useMCPTools"
                      checked={customization.use_mcp_tools}
                      onCheckedChange={(checked) => setCustomization(prev => ({ ...prev, use_mcp_tools: !!checked }))}
                    />
                    <Label htmlFor="useMCPTools" className="text-white text-sm">
                      Use MCP Tools
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="useA2A"
                      checked={customization.use_a2a}
                      onCheckedChange={(checked) => setCustomization(prev => ({ ...prev, use_a2a: !!checked }))}
                    />
                    <Label htmlFor="useA2A" className="text-white text-sm">
                      Use A2A Communication
                    </Label>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-figma-medium-gray border-figma-light-gray">
              <CardHeader>
                <CardTitle className="text-figma-text-primary flex items-center">
                  <GitBranch className="h-5 w-5 mr-2" />
                  Workflow Configuration
                </CardTitle>
                <CardDescription className="text-figma-text-secondary">
                  Choose how to approach the implementation task
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
                      disabled={!title.trim() || isGeneratingTasks}
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
                              <span className="text-figma-text-secondary text-xs">{task.estimatedTokens} tokens</span>
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
                  <CardTitle className="text-figma-text-primary">Assignment Result</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="text-sm text-figma-text-secondary whitespace-pre-wrap bg-figma-dark-gray p-4 rounded border border-figma-light-gray overflow-x-auto">
                    {JSON.stringify(assignmentResponse, null, 2)}
                  </pre>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
