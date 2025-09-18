import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Wrench, GitBranch, Loader2, Save, CheckCircle, AlertCircle, ChevronLeft, ChevronRight, ChevronDown, ChevronUp, Sparkles, Edit } from 'lucide-react'
import { Badge } from './ui/badge'
import { Button } from './ui/button'
import { toast } from '@/hooks/use-toast'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Textarea } from './ui/textarea'
import AssignmentResult from './AssignmentResult'
import { Checkbox } from './ui/checkbox'
import { SWEAgentSelection } from './SWEAgentSelection'
import { ConstitutionEditor } from './ConstitutionEditor'
import MDEditor from '@uiw/react-md-editor'

interface Spec {
  id: string
  title: string
  description: string
  content: string
  created_at: string
  updated_at: string
  tags: string[]
  phase: string
  specification?: string
  plan?: string
  tasks?: TaskBreakdown[]
  branch_name?: string
  feature_number?: string
  version?: number
  constitutional_compliance?: {
    is_compliant: boolean
    violations: Array<{article: string, violation: string}>
    recommendations: string[]
    gates_passed: Record<string, boolean>
  }
  tech_stack?: string
  architecture?: string
  constraints?: string
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
  acceptanceCriteria?: string[]
}

export function SpecWorkbench() {
  const params = useParams()
  const { specId } = params
  const navigate = useNavigate()
  const isNewSpec = window.location.pathname === '/spec/new' || specId === 'new'
  
  console.log('SpecWorkbench params:', params)
  console.log('SpecWorkbench specId:', specId)
  console.log('SpecWorkbench isNewSpec:', isNewSpec)
  console.log('Current pathname:', window.location.pathname)

  const [spec, setSpec] = useState<Spec | null>(null)
  const [loading, setLoading] = useState(!isNewSpec)
  const [saving, setSaving] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [content, setContent] = useState('')
  const [isEnhancing, setIsEnhancing] = useState(false)
  const [tags, setTags] = useState<string[]>([])
  const [tagInput, setTagInput] = useState('')

  const [customization] = useState<CustomizationRequest>({
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
  const [endpoint, setEndpoint] = useState<string>('')
  const [githubPat, setGithubPat] = useState<string>('')
  const [preferImport, setPreferImport] = useState<boolean>(false)
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false)

  // Agent Configuration (matches CLI --ai flag)
  const [ignoreAgentTools, setIgnoreAgentTools] = useState<boolean>(false)
  const [projectName, setProjectName] = useState<string>('')
  const [agentConfigured, setAgentConfigured] = useState<boolean>(false)

  const [activeTab, setActiveTab] = useState<'agent' | 'specify' | 'plan' | 'tasks'>('agent')

  const [specPhase, setSpecPhase] = useState<'specification' | 'plan' | 'tasks' | 'completed'>('specification')
  const [requirements, setRequirements] = useState('')
  const [planContent, setPlanContent] = useState('')
  const [taskBreakdown, setTaskBreakdown] = useState<TaskBreakdown[]>([])
  const [workflowMode, setWorkflowMode] = useState<'breakdown' | 'oneshot'>('breakdown')
  const [isAssigningTasks, setIsAssigningTasks] = useState(false)
  const [assignmentPhase, setAssignmentPhase] = useState<'idle' | 'starting'>('idle')
  const [assignmentResponses, setAssignmentResponses] = useState<any[]>([])
  const [isAgentPanelExpanded, setIsAgentPanelExpanded] = useState(true)
  const [isBasicDetailsCollapsed, setIsBasicDetailsCollapsed] = useState(false)
  const [isConstitutionEditorOpen, setIsConstitutionEditorOpen] = useState(false)

  useEffect(() => {
    if (title && description && !isBasicDetailsCollapsed) {
      const timer = setTimeout(() => {
        setIsBasicDetailsCollapsed(true)
      }, 2000)
      return () => clearTimeout(timer)
    }
  }, [title, description, isBasicDetailsCollapsed])

  const responseRef = useRef<HTMLDivElement>(null)
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  // Spec Kit wizard configuration fields (align with CLI flags & templates)
  const [aiPreference, setAiPreference] = useState<'claude' | 'gemini' | 'copilot'>('copilot')
  const [useMcpTools, setUseMcpTools] = useState<boolean>(false)
  const [useA2A, setUseA2A] = useState<boolean>(false)
  const [techStack, setTechStack] = useState<string>('')
  const [architectureNotes, setArchitectureNotes] = useState<string>('')
  const [nonFunctional, setNonFunctional] = useState<string>('')
  const [gateSimplicity, setGateSimplicity] = useState<boolean>(false)
  const [gateAntiAbstraction, setGateAntiAbstraction] = useState<boolean>(false)
  const [gateIntegrationFirst, setGateIntegrationFirst] = useState<boolean>(false)

  const fetchSpec = useCallback(async () => {
    if (isNewSpec || !specId) {
      setLoading(false)
      return
    }
    
    try {
      const response = await fetch(`${apiUrl}/api/specs/${specId}`)
      if (response.ok) {
        const specData = await response.json()
        setSpec(specData)
        setTitle(specData.title || '')
        setDescription(specData.description || '')
        setContent(specData.content || '')
        setTags(specData.tags || [])
        setRequirements(specData.specification || '')
        setPlanContent(specData.plan || '')
        setTaskBreakdown(specData.tasks || [])
        setSpecPhase(specData.phase || 'specification')
      }
    } catch (error) {
      console.error('Error fetching spec:', error)
    } finally {
      setLoading(false)
    }
  }, [specId, isNewSpec, apiUrl])

  useEffect(() => {
    fetchSpec()
  }, [fetchSpec])

  const saveSpec = async (): Promise<Spec | null> => {
    setSaving(true)
    try {
      const specData = {
        title,
        description,
        content,
        tags,
        specification: requirements,
        plan: planContent,
        tasks: taskBreakdown,
        phase: specPhase
      }

      console.log('Saving spec with data:', specData)
      console.log('Is new spec:', isNewSpec)
      console.log('Current specId:', specId)
      // Prefer updating if there's a concrete id; otherwise create
      let method: 'POST' | 'PUT' = 'POST'
      let url = `${apiUrl}/api/specs`
      const candidateId = (spec && (spec as any).id) ? (spec as any).id : (specId && specId !== 'new' ? specId : null)
      if (!isNewSpec && candidateId) {
        method = 'PUT'
        url = `${apiUrl}/api/specs/${candidateId}`
      }
      console.log('Saving via', method, url)

      let response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(specData)
      })

      // If attempting PUT but backend doesn't have it, fallback to POST
      if (method === 'PUT' && response.status === 404) {
        console.warn('PUT 404 — falling back to POST create')
        response = await fetch(`${apiUrl}/api/specs`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(specData)
        })
      }

      console.log('Save response status:', response.status)

      if (response.ok) {
        const savedSpec = await response.json()
        console.log('Saved spec response:', savedSpec)
        setSpec(savedSpec)
        if (isNewSpec || !candidateId) {
          console.log('Navigating to:', `/spec/${savedSpec.id}`)
          navigate(`/spec/${savedSpec.id}`)
        }
        toast({
          title: "Success",
          description: "Specification saved successfully"
        })
        return savedSpec
      } else {
        const errorText = await response.text()
        console.error('Save failed with status:', response.status, 'Error:', errorText)
        toast({
          title: "Error",
          description: `Failed to save specification: ${response.status}`,
          variant: "destructive"
        })
        return null
      }
    } catch (error) {
      console.error('Error saving spec:', error)
      toast({
        title: "Error",
        description: "Failed to save specification",
        variant: "destructive"
      })
      return null
    } finally {
      setSaving(false)
    }
  }

  const ensureSpecExists = async (): Promise<string | null> => {
    const saved = await saveSpec()
    return saved?.id || spec?.id || null
  }

  const handleEnhanceContent = async () => {
    const id = await ensureSpecExists()
    if (!id) {
      toast({ title: 'Save required', description: 'Save the spec before enhancing', variant: 'destructive' })
      return
    }
    setIsEnhancing(true)
    try {
      const url = `${apiUrl.replace(/\/$/, '')}/api/specs/${id}/enhance?stream=true`
      
      // Try POST first, then GET as fallback
      let success = false
      let lastError: any = null

      for (const method of ['POST', 'GET'] as const) {
        try {
          const resp = await fetch(url, { method })
          if (!resp.ok || !resp.body) {
            lastError = new Error(`Enhance ${method} ${url} failed: ${resp.status}`)
            continue
          }
          const reader = resp.body.getReader()
          const decoder = new TextDecoder('utf-8')
          // Start with a divider so user sees progress clearly
          setContent((prev) => (prev && prev.trim().length > 0 ? prev + '\n\n' : ''))
          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            const chunk = decoder.decode(value, { stream: true })
            if (chunk) setContent((prev) => (prev ?? '') + chunk)
          }
          success = true
          break
        } catch (e) {
          lastError = e
          continue
        }
      }
      if (!success) throw lastError || new Error('Enhance failed')
    } catch (err) {
      console.error('Enhance error:', err)
      toast({ title: 'Error', description: 'Failed to enhance spec', variant: 'destructive' })
    } finally {
      setIsEnhancing(false)
    }
  }

  const insertSpecTemplate = () => {
    if (content && content.trim().length > 0) return
    const template = `# Feature Specification

## Overview
- What and why in plain language.

## Users & Personas
- Primary users
- Secondary users

## User Stories
- As a [user], I want [goal], so that [reason].

## Functional Requirements
- [ ] Requirement 1
- [ ] Requirement 2

## Non-Functional Requirements
- Performance, security, accessibility, reliability.

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Assumptions
- Assumption 1

## Out-of-Scope
- Not included in this feature

## Clarifications
- [NEEDS CLARIFICATION: list questions here]

## Review & Acceptance Checklist
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable
`
    setContent(template)
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

  const handleSpecifyPhase = async () => {
    if (!requirements.trim()) {
      toast({
        title: "Requirements needed",
        description: "Please provide requirements before proceeding to planning phase",
        variant: "destructive"
      })
      return
    }

    try {
      let currentSpec = spec
      
      if (!currentSpec || isNewSpec || window.location.pathname.includes('/new')) {
        console.log('Saving spec first before specify phase...')
        await saveSpec()
        
        await new Promise(resolve => setTimeout(resolve, 2000))
        
        if (window.location.pathname.includes('/new')) {
          toast({
            title: "Error",
            description: "Failed to save specification. Please try again.",
            variant: "destructive"
          })
          return
        }
        
        const urlParts = window.location.pathname.split('/')
        const specIdFromUrl = urlParts[urlParts.length - 1]
        
        if (specIdFromUrl && specIdFromUrl !== 'new') {
          console.log('Fetching saved spec with ID:', specIdFromUrl)
          try {
            const fetchResponse = await fetch(`${apiUrl}/api/specs/${specIdFromUrl}`)
            if (fetchResponse.ok) {
              currentSpec = await fetchResponse.json()
              console.log('Successfully fetched spec:', currentSpec)
            } else {
              console.error('Failed to fetch spec, using fallback')
              currentSpec = { 
                id: specIdFromUrl, 
                title, 
                description, 
                content, 
                tags,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                phase: 'specification'
              }
            }
          } catch (error) {
            console.error('Error fetching spec:', error)
            toast({
              title: "Error",
              description: "Failed to retrieve saved specification.",
              variant: "destructive"
            })
            return
          }
        } else {
          toast({
            title: "Error",
            description: "Unable to determine specification ID after saving.",
            variant: "destructive"
          })
          return
        }
      }

      if (!currentSpec?.id) {
        toast({
          title: "Error",
          description: "Unable to get specification ID. Please save the spec first.",
          variant: "destructive"
        })
        return
      }

      const response = await fetch(`${apiUrl}/api/specs/${currentSpec.id}/specify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          requirements: requirements
        })
      })

      if (response.ok) {
        const result = await response.json()
        setSpec(result.spec)
        setSpecPhase('plan')
        setActiveTab('plan')
        toast({
          title: "Specification Complete",
          description: result.message || "Ready to proceed to planning phase"
        })
      } else {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to complete specification phase')
      }
    } catch (error) {
      console.error('Error in specify phase:', error)
      toast({
        title: "Error",
        description: (error as Error).message || "Failed to complete specification phase",
        variant: "destructive"
      })
    }
  }

  const handlePlanPhase = async (contentOverride?: string) => {
    if (!spec?.id) {
      toast({
        title: "Error",
        description: "No specification ID found. Please complete the specify phase first.",
        variant: "destructive"
      })
      return
    }

    try {
      const response = await fetch(`${apiUrl}/api/specs/${spec.id}/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plan_content: contentOverride || planContent || "Generate technical implementation plan"
        })
      })

      if (response.ok) {
        const result = await response.json()
        setPlanContent(result.plan || result.message)
        setSpecPhase('tasks')
        setActiveTab('tasks')
        toast({
          title: "Plan Generated",
          description: result.message || "Ready to break down into tasks"
        })
      } else {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to generate plan')
      }
    } catch (error) {
      console.error('Error in plan phase:', error)
      toast({
        title: "Error",
        description: (error as Error).message || "Failed to generate plan",
        variant: "destructive"
      })
    }
  }

  const handleTasksPhase = async () => {
    if (!spec?.id) {
      toast({
        title: "Error",
        description: "No specification ID found. Please complete previous phases first.",
        variant: "destructive"
      })
      return
    }

    try {
      const response = await fetch(`${apiUrl}/api/specs/${spec.id}/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          specification: requirements,
          plan: planContent,
          title,
          description
        })
      })

      if (response.ok) {
        const result = await response.json()
        setTaskBreakdown(result.tasks)
        setSpecPhase('completed')
        toast({
          title: "Tasks Generated",
          description: "Specification workflow complete"
        })
      }
    } catch (error) {
      console.error('Error in tasks phase:', error)
    }
  }

  const assignToSWEAgent = async () => {
    setIsAssigningTasks(true)
    setAssignmentPhase('starting')
    setAssignmentResponses([])

    try {
      const mappedCustomization = {
        ...customization,
        title,
        customer_scenario: customization.customer_scenario || description,
        additional_requirements: customization.additional_requirements || content
      }

      const payload = {
        spec_id: spec?.id || 'new',
        agent_type: selectedAgent,
        api_key: apiKey,
        endpoint: endpoint,
        customization: mappedCustomization,
        github_pat: githubPat,
        prefer_import: preferImport,
        selected_tasks: Array.from(selectedTasks),
        workflow_mode: workflowMode
      }

      const response = await fetch(`${apiUrl}/api/specs/assign-swe-agent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (response.ok) {
        const result = await response.json()
        setAssignmentResponses(prev => [...prev, result])
        
        toast({
          title: "Assignment Complete",
          description: "Specification assigned to SWE Agent successfully"
        })
      }
    } catch (error) {
      console.error('Error assigning to SWE agent:', error)
      toast({
        title: "Assignment Failed",
        description: "Failed to assign specification to SWE Agent",
        variant: "destructive"
      })
    } finally {
      setIsAssigningTasks(false)
      setAssignmentPhase('idle')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-figma-black flex items-center justify-center">
        <div className="flex items-center space-x-2 text-figma-text-primary">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Loading specification...</span>
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
                  {isNewSpec ? 'New Spec-Kit Project' : title || 'Spec-Kit Project'}
                </h1>
                <p className="text-gray-400 mt-2">
                  {isNewSpec ? 'Follow the spec-kit three-phase methodology: Agent Setup → /specify → /plan → /tasks' : 'Manage your spec-driven development workflow'}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <Button
                onClick={saveSpec}
                disabled={saving}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                {saving ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>

        <div className={`grid gap-8 transition-all duration-300 ${isAgentPanelExpanded ? 'grid-cols-1 lg:grid-cols-3' : 'grid-cols-1'}`}>
          <div className={`space-y-6 ${isAgentPanelExpanded ? 'lg:col-span-2' : 'col-span-1'}`}>
            <Card className="bg-figma-medium-gray border-figma-light-gray">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-figma-text-primary">Spec Kit Workflow</CardTitle>
                    <CardDescription className="text-figma-text-secondary">
                      Follow the three-phase methodology with constitutional governance
                    </CardDescription>
                  </div>
                  {spec?.branch_name && (
                    <div className="flex items-center gap-2 text-sm text-figma-text-secondary">
                      <GitBranch className="h-4 w-4" />
                      <span>Feature #{spec.feature_number}: {spec.branch_name}</span>
                    </div>
                  )}
                  
                  <div className="flex items-center justify-end mt-3">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setIsConstitutionEditorOpen(true)}
                      className="bg-figma-input-gray text-figma-text-primary border-figma-light-gray hover:bg-figma-light-gray/20 hover:text-white"
                    >
                      <Edit className="h-3 w-3 mr-1" />
                      Edit Constitution
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setActiveTab('agent')}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                      activeTab === 'agent' ? 'bg-blue-600 text-white' : 
                      agentConfigured ? 'bg-green-600 text-white hover:bg-green-500' :
                      'bg-gray-600 text-gray-300 hover:bg-gray-500'
                    }`}
                  >
                    <span className="mr-2">🤖</span>
                    Agent Setup
                  </button>
                  <button
                    onClick={() => setActiveTab('specify')}
                    disabled={!agentConfigured}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                      activeTab === 'specify' ? 'bg-blue-600 text-white' : 
                      specPhase === 'specification' ? 'bg-blue-500 text-white' :
                      (specPhase === 'plan' || specPhase === 'tasks' || specPhase === 'completed') ? 'bg-green-600 text-white hover:bg-green-500' : 
                      'bg-gray-600 text-gray-300 hover:bg-gray-500'
                    }`}
                  >
                    <span className="mr-2">📝</span>
                    /specify
                  </button>
                  <button
                    onClick={() => setActiveTab('plan')}
                    disabled={!agentConfigured || (specPhase === 'specification' && !spec?.specification)}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                      activeTab === 'plan' ? 'bg-blue-600 text-white' :
                      specPhase === 'plan' ? 'bg-blue-500 text-white' :
                      (specPhase === 'tasks' || specPhase === 'completed') ? 'bg-green-600 text-white hover:bg-green-500' :
                      'bg-gray-600 text-gray-300 hover:bg-gray-500'
                    }`}
                  >
                    <span className="mr-2">🏗️</span>
                    /plan
                  </button>
                  <button
                    onClick={() => setActiveTab('tasks')}
                    disabled={!agentConfigured || specPhase === 'specification' || (specPhase === 'plan' && !planContent)}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                      activeTab === 'tasks' ? 'bg-blue-600 text-white' :
                      (specPhase === 'tasks' || specPhase === 'completed') ? 'bg-green-600 text-white hover:bg-green-500' :
                      'bg-gray-600 text-gray-300 hover:bg-gray-500'
                    }`}
                  >
                    <span className="mr-2">✅</span>
                    /tasks
                  </button>
                </div>
              </CardContent>
            </Card>

            {showAdvanced && (
              <Card className="bg-figma-medium-gray border-figma-light-gray">
                <CardHeader>
                  <CardTitle className="text-figma-text-primary">GitHub Integration</CardTitle>
                  <CardDescription className="text-figma-text-secondary">
                    Configure GitHub Personal Access Token for repository operations
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="githubPat" className="text-white">GitHub Personal Access Token</Label>
                    <Input
                      id="githubPat"
                      type="password"
                      placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                      value={githubPat}
                      onChange={(e) => setGithubPat(e.target.value)}
                      className="bg-figma-input-gray border-figma-light-gray text-figma-text-primary placeholder-figma-text-secondary"
                    />
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={async () => {
                        const token = githubPat.trim()
                        if (!token) {
                          alert('Please enter a GitHub token first')
                          return
                        }
                        try {
                          const r = await fetch(`${apiUrl}/api/github/test-token`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ token })
                          })
                          const data = await r.json()
                          if (data.ok) {
                            alert(`GitHub token OK for ${data.login}\nScopes: ${(data.scopes || []).join(', ') || 'none'}`)
                          } else {
                            alert(`Token check failed: ${data.error || String(data.status)}`)
                          }
                        } catch (e: any) {
                          alert(`Token check error: ${String(e)}`)
                        }
                      }}
                    >
                      Test GitHub Token
                    </Button>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox id="preferImport" checked={preferImport} onCheckedChange={(checked) => setPreferImport(!!checked)} />
                    <Label htmlFor="preferImport" className="text-white text-sm">Prefer Import (copy) instead of Fork</Label>
                  </div>
                </CardContent>
              </Card>
            )}

            <Card className="bg-figma-medium-gray border-figma-light-gray">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-figma-text-primary">Basic Details</CardTitle>
                    <CardDescription className="text-figma-text-secondary">
                      Provide basic information about your specification
                    </CardDescription>
                  </div>
                  <Button 
                    onClick={() => setIsBasicDetailsCollapsed(!isBasicDetailsCollapsed)}
                    variant="ghost"
                    size="sm"
                    className="text-figma-text-secondary hover:text-figma-text-primary p-1"
                  >
                    {isBasicDetailsCollapsed ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />}
                  </Button>
                </div>
              </CardHeader>
              {!isBasicDetailsCollapsed && (
                <CardContent className="space-y-4">
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
                </CardContent>
              )}
            </Card>

            {activeTab === 'specify' && (
              <Card className="bg-figma-medium-gray border-figma-light-gray border-2 border-blue-500">
                <CardHeader>
                  <CardTitle className="text-figma-text-primary flex items-center gap-2">
                    <span>📝</span>
                    /specify - Define WHAT and WHY
                  </CardTitle>
                  <CardDescription className="text-figma-text-secondary">
                    Focus on <strong>what</strong> you want to build and <strong>why</strong> it's needed. 
                    <strong className="text-yellow-400"> Do NOT focus on tech stack</strong> - that comes in the /plan phase.
                  </CardDescription>
                  <div className="mt-3 p-3 bg-blue-900/20 border border-blue-800/30 rounded-lg">
                    <p className="text-xs text-blue-300/80">
                      <strong>CLI equivalent:</strong> <code className="bg-figma-light-gray/20 px-1 rounded">/specify Build an application that...</code>
                    </p>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="requirements" className="text-white">Requirements Specification</Label>
                      <p className="text-xs text-figma-text-secondary mb-2">
                        Be as explicit as possible about <strong>what</strong> you are trying to build and <strong>why</strong>. 
                        Do not focus on tech stack at this point.
                      </p>
                      <Textarea
                        id="requirements"
                        placeholder={`Example: Build an application that can help me organize my photos in separate photo albums. Albums are grouped by date and can be re-organized by dragging and dropping on the main page. Albums never contain other nested albums. Within each album, photos are previewed in a tile-like interface.

Focus on:
• User requirements and scenarios
• Business objectives and constraints  
• Functional requirements
• User experience goals

Avoid:
• Technology choices (React, Node.js, etc.)
• Implementation details
• Architecture decisions`}
                        value={requirements}
                        onChange={(e) => setRequirements(e.target.value)}
                        className="bg-figma-input-gray border-figma-light-gray text-figma-text-primary placeholder-figma-text-secondary min-h-[200px]"
                      />
                      <p className="text-xs text-figma-text-secondary mt-1">
                        💡 <strong>Pro tip:</strong> Use the CLI example format - describe user scenarios and outcomes, not implementation.
                      </p>
                    </div>
                    <div>
                      <Label className="text-white">Wizard Options</Label>
                      <div className="bg-figma-dark-gray rounded-md p-3 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-figma-text-secondary">Preferred AI agent</span>
                          <select
                            value={aiPreference}
                            onChange={(e) => setAiPreference(e.target.value as any)}
                            className="bg-figma-input-gray border-figma-light-gray text-sm rounded px-2 py-1"
                          >
                            <option value="copilot">Copilot</option>
                            <option value="claude">Claude</option>
                            <option value="gemini">Gemini</option>
                          </select>
                        </div>
                        <label className="flex items-center justify-between text-sm text-figma-text-secondary">
                          <span>Ignore agent tools</span>
                          <input type="checkbox" checked={ignoreAgentTools} onChange={(e) => setIgnoreAgentTools(e.target.checked)} />
                        </label>
                        <label className="flex items-center justify-between text-sm text-figma-text-secondary">
                          <span>Use MCP tools</span>
                          <input type="checkbox" checked={useMcpTools} onChange={(e) => setUseMcpTools(e.target.checked)} />
                        </label>
                        <label className="flex items-center justify-between text-sm text-figma-text-secondary">
                          <span>Agent-to-Agent (A2A)</span>
                          <input type="checkbox" checked={useA2A} onChange={(e) => setUseA2A(e.target.checked)} />
                        </label>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <Button variant="outline" onClick={() => setActiveTab('agent')}>← Back to Agent Setup</Button>
                    <Button
                      onClick={handleSpecifyPhase}
                      disabled={!requirements.trim()}
                      className="bg-blue-600 hover:bg-blue-700 text-white"
                    >
                      Complete Specification →
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {activeTab === 'plan' && (
              <Card className="bg-figma-medium-gray border-figma-light-gray border-2 border-blue-500">
                <CardHeader>
                  <CardTitle className="text-figma-text-primary flex items-center gap-2">
                    <span>🏗️</span>
                    /plan - Define HOW to Build It
                  </CardTitle>
                  <CardDescription className="text-figma-text-secondary">
                    Now specify your tech stack and architecture choices. This is where you define the <strong>HOW</strong>.
                  </CardDescription>
                  <div className="mt-3 p-3 bg-blue-900/20 border border-blue-800/30 rounded-lg">
                    <p className="text-xs text-blue-300/80">
                      <strong>CLI equivalent:</strong> <code className="bg-figma-light-gray/20 px-1 rounded">/plan The application uses Vite with minimal libraries. Use vanilla HTML, CSS, and JavaScript...</code>
                    </p>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {planContent ? (
                    <div className="space-y-4">
                      <div className="bg-figma-dark-gray p-4 rounded-lg">
                        <MDEditor.Markdown source={planContent} />
                      </div>
                      <div className="flex items-center justify-between">
                        <Button variant="outline" onClick={() => setActiveTab('specify')}>← Back</Button>
                        <Button
                          onClick={handleTasksPhase}
                          className="bg-blue-600 hover:bg-blue-700 text-white"
                        >
                          Break Down into Tasks →
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <Label className="text-white">Tech stack & architecture</Label>
                          <Textarea
                            placeholder="e.g., Vite + React, .NET Aspire, PostgreSQL"
                            value={techStack}
                            onChange={(e) => setTechStack(e.target.value)}
                            className="bg-figma-input-gray border-figma-light-gray text-figma-text-primary placeholder-figma-text-secondary min-h-[100px]"
                          />
                          <Label className="text-white mt-4 block">Architecture notes</Label>
                          <Textarea
                            placeholder="Key components, boundaries, data flows"
                            value={architectureNotes}
                            onChange={(e) => setArchitectureNotes(e.target.value)}
                            className="bg-figma-input-gray border-figma-light-gray text-figma-text-primary placeholder-figma-text-secondary min-h-[100px]"
                          />
                        </div>
                        <div>
                          <Label className="text-white">Non-functional requirements</Label>
                          <Textarea
                            placeholder="Performance, security, accessibility, SLAs"
                            value={nonFunctional}
                            onChange={(e) => setNonFunctional(e.target.value)}
                            className="bg-figma-input-gray border-figma-light-gray text-figma-text-primary placeholder-figma-text-secondary min-h-[100px]"
                          />
                          <div className="bg-figma-dark-gray rounded-md p-3 mt-3 space-y-2">
                            <div className="text-sm text-figma-text-primary font-medium">Phase -1 Gates</div>
                            <label className="flex items-center justify-between text-sm text-figma-text-secondary">
                              <span>Simplicity Gate (≤3 projects, no future-proofing)</span>
                              <input type="checkbox" checked={gateSimplicity} onChange={(e) => setGateSimplicity(e.target.checked)} />
                            </label>
                            <label className="flex items-center justify-between text-sm text-figma-text-secondary">
                              <span>Anti-Abstraction Gate (use framework directly)</span>
                              <input type="checkbox" checked={gateAntiAbstraction} onChange={(e) => setGateAntiAbstraction(e.target.checked)} />
                            </label>
                            <label className="flex items-center justify-between text-sm text-figma-text-secondary">
                              <span>Integration-First Gate (contracts & tests first)</span>
                              <input type="checkbox" checked={gateIntegrationFirst} onChange={(e) => setGateIntegrationFirst(e.target.checked)} />
                            </label>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center justify-between pt-2">
                        <Button variant="outline" onClick={() => setActiveTab('specify')}>← Back</Button>
                        <Button
                          onClick={() => {
                            const prompt = `Generate a detailed implementation plan based on the specification.\n\n` +
`Preferred AI agent: ${aiPreference}${ignoreAgentTools ? ' (ignore agent tools)' : ''}\n` +
`Use MCP tools: ${useMcpTools ? 'yes' : 'no'}; A2A: ${useA2A ? 'yes' : 'no'}\n\n` +
`Tech stack & architecture:\n${techStack}\n\nArchitecture notes:\n${architectureNotes}\n\nNon-functional requirements:\n${nonFunctional}\n\n` +
`Phase -1 Gates:\n- Simplicity: ${gateSimplicity ? 'pass' : 'pending'}\n- Anti-Abstraction: ${gateAntiAbstraction ? 'pass' : 'pending'}\n- Integration-First: ${gateIntegrationFirst ? 'pass' : 'pending'}\n\n` +
`Please produce:\n- plan.md (high-level)\n- implementation-details/ (data models, API contracts, tests, research)\n`;
                            setPlanContent(prompt)
                            handlePlanPhase(prompt)
                          }}
                          disabled={!requirements.trim()}
                          className="bg-blue-600 hover:bg-blue-700 text-white"
                        >
                          Generate Plan
                        </Button>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>
            )}

            {activeTab === 'tasks' && (
              <Card className="bg-figma-medium-gray border-figma-light-gray border-2 border-blue-500">
                <CardHeader>
                  <CardTitle className="text-figma-text-primary flex items-center gap-2">
                    <span>✅</span>
                    /tasks - Create Actionable Implementation Tasks
                  </CardTitle>
                  <CardDescription className="text-figma-text-secondary">
                    Break down the plan into actionable tasks that can be assigned to your configured agent ({selectedAiAgent || 'selected agent'}).
                  </CardDescription>
                  <div className="mt-3 p-3 bg-blue-900/20 border border-blue-800/30 rounded-lg">
                    <p className="text-xs text-blue-300/80">
                      <strong>CLI equivalent:</strong> <code className="bg-figma-light-gray/20 px-1 rounded">/tasks</code> creates actionable task list for implementation
                    </p>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {taskBreakdown.length > 0 ? (
                    <div className="space-y-4">
                      {taskBreakdown.map((task) => (
                        <div key={task.id} className="bg-figma-dark-gray p-4 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium text-figma-text-primary">{task.title}</h4>
                            <Badge className={`text-xs ${
                              task.priority === 'high' ? 'bg-red-900/30 text-red-400' :
                              task.priority === 'medium' ? 'bg-yellow-900/30 text-yellow-400' :
                              'bg-green-900/30 text-green-400'
                            }`}>
                              {task.priority}
                            </Badge>
                          </div>
                          <p className="text-figma-text-secondary text-sm mb-2">{task.description}</p>
                          <div className="flex items-center gap-4 text-xs text-figma-text-secondary">
                            <span>Time: {task.estimatedTime}</span>
                            <span>Tokens: {task.estimatedTokens}</span>
                            <span>Status: {task.status}</span>
                          </div>
                        </div>
                      ))}
                      <div className="flex items-center justify-between pt-2">
                        <Button variant="outline" onClick={() => setActiveTab('plan')}>← Back</Button>
                        <Button onClick={() => setIsAgentPanelExpanded(true)} className="bg-emerald-600 hover:bg-emerald-700 text-white">Assign to SWE Agent →</Button>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Button
                        onClick={handleTasksPhase}
                        disabled={!planContent.trim()}
                        className="bg-blue-600 hover:bg-blue-700 text-white"
                      >
                        Generate Tasks
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {activeTab === 'agent' && (
              <Card className="bg-figma-medium-gray border-figma-light-gray">
                <CardHeader>
                  <CardTitle className="text-figma-text-primary flex items-center gap-2">
                    <span>🤖</span>
                    Agent Configuration
                  </CardTitle>
                  <CardDescription className="text-figma-text-secondary">
                    Configure your AI agent and project settings (equivalent to <code className="bg-figma-light-gray/20 px-1 rounded">specify init</code>)
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">

                  {/* Project Name */}
                  <div>
                    <Label htmlFor="projectName" className="text-white">Project Name</Label>
                    <p className="text-xs text-figma-text-secondary mb-2">Name for your spec-kit project</p>
                    <Input
                      id="projectName"
                      placeholder="e.g., my-awesome-app"
                      value={projectName}
                      onChange={(e) => setProjectName(e.target.value)}
                      className="bg-figma-input-gray border-figma-light-gray text-figma-text-primary placeholder-figma-text-secondary"
                    />
                  </div>

                  {/* Agent Tools Option */}
                  <div className="flex items-start space-x-3">
                    <Checkbox
                      id="ignoreAgentTools"
                      checked={ignoreAgentTools}
                      onCheckedChange={(checked) => setIgnoreAgentTools(checked as boolean)}
                      className="border-figma-light-gray data-[state=checked]:bg-blue-600"
                    />
                    <div className="grid gap-1.5 leading-none">
                      <Label htmlFor="ignoreAgentTools" className="text-white text-sm font-medium">
                        Ignore Agent Tools
                      </Label>
                      <p className="text-xs text-figma-text-secondary">
                        Equivalent to <code className="bg-figma-light-gray/20 px-1 rounded">--ignore-agent-tools</code> flag
                      </p>
                    </div>
                  </div>

                  {/* Basic Spec Info */}
                  <div className="border-t border-figma-light-gray/20 pt-6">
                    <Label className="text-white text-sm font-medium mb-3 block">Specification Details</Label>
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
                    <Label htmlFor="content" className="text-white">Content (Markdown)</Label>
                    <div data-color-mode="dark" className="bg-figma-dark-gray rounded-md p-1">
                      <MDEditor
                        value={content}
                        onChange={(val) => setContent(val || '')}
                        previewOptions={{ disallowedElements: ['script', 'style'] }}
                        height={260}
                      />
                    </div>
                    <div className="flex items-center gap-3 mt-2">
                      <Button type="button" variant="outline" size="sm" onClick={insertSpecTemplate}>
                        Insert Spec Template
                      </Button>
                      <Button
                        type="button"
                        onClick={handleEnhanceContent}
                        disabled={isEnhancing || !title.trim()}
                        className="px-5 py-2 rounded-full bg-gradient-to-r from-fuchsia-500 via-purple-500 to-indigo-500 text-white shadow hover:opacity-90 disabled:opacity-50"
                      >
                        {isEnhancing ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Enhancing...
                          </>
                        ) : (
                          <>
                            <Sparkles className="h-4 w-4 mr-2" />
                            Enhance
                          </>
                        )}
                      </Button>
                    </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-4">
                    <div className="text-xs text-figma-text-secondary">
                      {projectName && title ? 
                        '✅ Configuration complete - ready to proceed' : 
                        '⚠️ Complete project name and title to continue'
                      }
                    </div>
                    <Button
                      type="button"
                      onClick={() => {
                        if (projectName && title) {
                          setAgentConfigured(true)
                          saveSpec()
                          setActiveTab('specify')
                        }
                      }}
                      disabled={!projectName || !title}
                      className="bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50"
                    >
                      Configure Project & Continue →
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {isAgentPanelExpanded && (
            <div className="lg:col-span-1">
              <Card className="bg-figma-medium-gray border-figma-light-gray sticky top-8">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Wrench className="h-5 w-5 mr-2 text-emerald-400" />
                      <CardTitle className="text-figma-text-primary">Agent Assignment</CardTitle>
                    </div>
                    <Button 
                      onClick={() => setIsAgentPanelExpanded(false)}
                      variant="outline"
                      size="sm"
                      className="bg-figma-input-gray text-figma-text-primary border-figma-light-gray hover:bg-figma-light-gray/20 hover:text-white"
                    >
                      Hide Panel
                      <ChevronRight className="h-4 w-4 ml-2" />
                    </Button>
                  </div>
                  <CardDescription className="text-figma-text-secondary">
                    Assign this specification to a cloud-based coding agent that runs in GitHub Actions
                  </CardDescription>
                </CardHeader>
              <CardContent>
                <SWEAgentSelection
                  selectedAgent={selectedAgent}
                  setSelectedAgent={setSelectedAgent}
                  apiKey={apiKey}
                  setApiKey={setApiKey}
                  endpoint={endpoint}
                  setEndpoint={setEndpoint}
                  customization={{ ...customization, title }}
                  workflowMode={workflowMode}
                  selectedTasks={selectedTasks}
                  isAssigningTasks={isAssigningTasks}
                  onAssignToSWEAgent={assignToSWEAgent}
                  validationField="title"
                />

                {isAssigningTasks && (
                  <Card className="bg-figma-medium-gray border-figma-light-gray mt-4">
                    <CardHeader>
                      <CardTitle className="text-figma-text-primary flex items-center">
                        <Wrench className="h-5 w-5 mr-2 text-emerald-400" />
                        Assignment In Progress
                      </CardTitle>
                      <CardDescription className="text-figma-text-secondary">Starting selected coding agent…</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ul className="text-sm text-figma-text-secondary space-y-2">
                        <li className={`${assignmentPhase !== 'idle' ? 'text-white' : ''}`}>1. Start selected coding agent</li>
                      </ul>
                    </CardContent>
                  </Card>
                )}

                {assignmentResponses.length > 0 && (
                  <div className="space-y-4 mt-4">
                    {assignmentResponses.map((resp, idx) => (
                      <Card key={idx} className="bg-figma-medium-gray border-figma-light-gray">
                        <CardHeader>
                          <CardTitle className="text-figma-text-primary">Assignment Result #{idx + 1}</CardTitle>
                        </CardHeader>
                        <CardContent ref={idx === assignmentResponses.length - 1 ? responseRef : undefined}>
                          <AssignmentResult result={resp} />
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
              </Card>
            </div>
          )}
        </div>
        
        {/* Show Panel Button - appears when agent panel is collapsed */}
        {!isAgentPanelExpanded && (
          <div className="fixed right-0 top-1/2 -translate-y-1/2 z-10">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsAgentPanelExpanded(true)}
              className="relative w-10 h-36 rounded-l-md rounded-r-none border-r-0 bg-figma-medium-gray text-figma-text-primary border-figma-light-gray hover:bg-figma-black hover:text-white shadow-lg"
            >
              <div className="absolute inset-0 flex items-center justify-center -rotate-90">
                <div className="flex items-center gap-1">
                  <ChevronLeft className="h-4 w-4" />
                  <span className="text-xs font-medium">Show Panel</span>
                </div>
              </div>
            </Button>
          </div>
        )}

        {/* Constitution Editor Modal */}
        <ConstitutionEditor
          isOpen={isConstitutionEditorOpen}
          onClose={() => setIsConstitutionEditorOpen(false)}
          specId={spec?.id}
        />
      </div>
    </div>
  )
}

export default SpecWorkbench
