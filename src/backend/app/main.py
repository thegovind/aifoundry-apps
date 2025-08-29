from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import os
import re
import logging
import httpx
from pathlib import Path
from datetime import datetime
from azure.ai.projects import AIProjectClient
from azure.core.credentials import AzureKeyCredential
from .mcp_client import create_github_mcp_client

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(title="AIFoundry.app  API", description="API for AI App Templates")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Template(BaseModel):
    id: str
    title: str
    description: str
    tags: List[str]
    languages: List[str]
    models: List[str]
    databases: List[str]
    collection: str
    task: str
    pattern: Optional[str] = None
    github_url: str
    fork_count: int
    star_count: int
    is_featured: bool
    icon: str
    created_at: str

class FilterOptions(BaseModel):
    tasks: List[str]
    languages: List[str]
    collections: List[str]
    models: List[str]
    databases: List[str]
    patterns: List[str]

class LearningResource(BaseModel):
    id: str
    title: str
    description: str
    url: str
    type: str
    icon: str

class CustomizationRequest(BaseModel):
    customer_scenario: str
    brand_theme: str
    primary_color: str
    company_name: str
    industry: str
    use_case: str
    additional_requirements: str
    use_mcp_tools: bool = False
    use_a2a: bool = False
    owner: str = ""
    repo: str = ""

class TaskBreakdownRequest(BaseModel):
    template_id: str
    customization: CustomizationRequest

class TaskBreakdownResponse(BaseModel):
    tasks: List[Dict[str, str]]

class SWEAgentRequest(BaseModel):
    agent_id: str
    api_key: str
    template_id: str
    customization: CustomizationRequest
    task_id: Optional[str] = None
    mode: str = "breakdown"

class Spec(BaseModel):
    id: str
    title: str
    description: str
    content: str
    created_at: str
    updated_at: str
    tags: List[str]

class SpecCreateRequest(BaseModel):
    title: str
    description: str
    content: str
    tags: List[str] = []

CATALOG_PATH = Path(__file__).parent / "catalog.json"
FEATURED_PATH = Path(__file__).parent / "featured.json"
SPECS_PATH = Path(__file__).parent / "specs.json"

def load_catalog() -> List[Template]:
    items: List[Template] = []
    raw: List[Dict] = []
    if CATALOG_PATH.exists():
        with CATALOG_PATH.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    else:
        logger.warning("catalog.json not found; returning empty catalog")
    try:
        with FEATURED_PATH.open("r", encoding="utf-8") as f:
            featured_urls = set(json.load(f))
    except FileNotFoundError:
        featured_urls = set()
    for obj in raw:
        try:
            is_featured = obj.get("github_url") in featured_urls or obj.get("is_featured", False)
            obj["is_featured"] = bool(is_featured)
            items.append(Template(**obj))
        except Exception as e:
            logger.warning(f"Skipping invalid template: {e}")
    return items

templates_data: List[Template] = load_catalog()
template_by_id: Dict[str, Template] = {t.id: t for t in templates_data}

def load_specs() -> List[Spec]:
    specs: List[Spec] = []
    if SPECS_PATH.exists():
        with SPECS_PATH.open("r", encoding="utf-8") as f:
            raw_specs = json.load(f)
            for spec_data in raw_specs:
                try:
                    specs.append(Spec(**spec_data))
                except Exception as e:
                    logger.warning(f"Skipping invalid spec: {e}")
    return specs

def save_specs(specs: List[Spec]):
    with SPECS_PATH.open("w", encoding="utf-8") as f:
        json.dump([spec.model_dump() for spec in specs], f, indent=2)

specs_data: List[Spec] = load_specs()
spec_by_id: Dict[str, Spec] = {s.id: s for s in specs_data}

@app.get("/api/specs")
async def get_specs():
    """Get all specifications"""
    return specs_data

@app.get("/api/specs/{spec_id}")
async def get_spec(spec_id: str):
    """Get a specific specification"""
    spec = spec_by_id.get(spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Specification not found")
    return spec

@app.post("/api/specs")
async def create_spec(request: SpecCreateRequest):
    """Create a new specification"""
    import uuid
    from datetime import datetime
    
    spec_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    new_spec = Spec(
        id=spec_id,
        title=request.title,
        description=request.description,
        content=request.content,
        created_at=now,
        updated_at=now,
        tags=request.tags
    )
    
    specs_data.append(new_spec)
    spec_by_id[spec_id] = new_spec
    save_specs(specs_data)
    
    return new_spec

@app.put("/api/specs/{spec_id}")
async def update_spec(spec_id: str, request: SpecCreateRequest):
    """Update an existing specification"""
    spec = spec_by_id.get(spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Specification not found")
    
    from datetime import datetime
    now = datetime.now().isoformat()
    
    updated_spec = Spec(
        id=spec_id,
        title=request.title,
        description=request.description,
        content=request.content,
        created_at=spec.created_at,
        updated_at=now,
        tags=request.tags
    )
    
    for i, s in enumerate(specs_data):
        if s.id == spec_id:
            specs_data[i] = updated_spec
            break
    
    spec_by_id[spec_id] = updated_spec
    save_specs(specs_data)
    
    return updated_spec

@app.post("/api/specs/{spec_id}/breakdown")
async def generate_spec_task_breakdown(spec_id: str, request: CustomizationRequest):
    """Generate task breakdown for a specification using Azure AI Agents Service"""
    try:
        spec = spec_by_id.get(spec_id)
        if not spec:
            raise HTTPException(status_code=404, detail="Specification not found")
        
        project_endpoint = os.getenv("AZURE_PROJECT_ENDPOINT")
        api_key = os.getenv("AZURE_API_KEY")
        model_name = os.getenv("AZURE_MODEL_NAME", "gpt-4.1-nano")
        
        if not project_endpoint or not api_key:
            raise HTTPException(
                status_code=500, 
                detail="Azure AI configuration not found. Please set AZURE_PROJECT_ENDPOINT and AZURE_API_KEY environment variables."
            )
        
        try:
            with AIProjectClient(
                endpoint=project_endpoint,
                credential=AzureKeyCredential(api_key)
            ) as project_client:
                agents_client = project_client.agents
                
                agent = agents_client.create_agent(
                    model=model_name,
                    name="spec-breakdown-agent",
                    instructions="""You are a task breakdown specialist for software development projects based on specifications. 
                    Given a specification document and customization requirements, break down the work into specific, actionable tasks.
                    
                    For each task, provide:
                    - A clear, specific title
                    - Detailed description of what needs to be done
                    - Estimated time to complete
                    - Priority level (high, medium, low)
                    - Status (always 'pending' for new tasks)
                    
                    Focus on practical implementation steps like:
                    - Code implementation based on specification requirements
                    - UI/UX development for specified features
                    - Integration of specific requirements from the spec
                    - Testing and validation of implemented features
                    - Documentation updates
                    
                    Return your response as a JSON array of task objects with the following structure:
                    [
                      {
                        "id": "task-1",
                        "title": "Task title",
                        "description": "Detailed description",
                        "estimatedTime": "X-Y hours",
                        "estimatedTokens": "X-Y tokens",
                        "priority": "high|medium|low",
                        "status": "pending"
                      }
                    ]"""
                )
                
                thread = agents_client.threads.create()
                
                prompt = f"""
                Please analyze the following specification and break it down into actionable development tasks:

                **Specification Title:** {spec.title}
                **Description:** {spec.description}
                **Content:**
                {spec.content}

                **Implementation Context:**
                - Customer: {request.company_name}
                - Industry: {request.industry}
                - Use Case: {request.use_case}
                - Scenario: {request.customer_scenario}
                - Additional Requirements: {request.additional_requirements}
                - Brand Theme: {request.brand_theme}
                - Primary Color: {request.primary_color}
                - Use MCP Tools: {request.use_mcp_tools}
                - Use A2A: {request.use_a2a}

                Please provide a comprehensive task breakdown that covers all aspects of implementing this specification.
                """
                
                message = agents_client.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=prompt
                )
                
                run = agents_client.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=agent.id
                )
                
                import time
                while run.status in ["queued", "in_progress"]:
                    time.sleep(1)
                    run = agents_client.threads.runs.retrieve(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                
                if run.status == "completed":
                    messages = agents_client.threads.messages.list(
                        thread_id=thread.id,
                        order="desc",
                        limit=1
                    )
                    
                    if messages.data:
                        response_content = messages.data[0].content[0].text.value
                        
                        try:
                            import re
                            json_match = re.search(r'\[.*\]', response_content, re.DOTALL)
                            if json_match:
                                tasks_json = json_match.group()
                                tasks = json.loads(tasks_json)
                                return tasks
                            else:
                                logger.warning("No JSON array found in response")
                                return []
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse JSON response: {e}")
                            return []
                else:
                    logger.error(f"Run failed with status: {run.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Azure AI error: {e}")
            return []
            
    except Exception as e:
        logger.error(f"Error in generate_spec_task_breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/specs/{spec_id}/assign")
async def assign_spec_to_swe_agent(spec_id: str, request: SWEAgentRequest):
    """Assign specification implementation to SWE agent"""
    try:
        spec = spec_by_id.get(spec_id)
        if not spec:
            raise HTTPException(status_code=404, detail="Specification not found")
        
        if request.agent_id == "devin":
            devin_payload = {
                "prompt": f"""
                Implement the {spec.title} specification for the following scenario:
                
                Customer: {request.customization.company_name}
                Industry: {request.customization.industry}
                Use Case: {request.customization.use_case}
                Scenario: {request.customization.customer_scenario}
                Brand Theme: {request.customization.brand_theme}
                Primary Color: {request.customization.primary_color}
                Additional Requirements: {request.customization.additional_requirements}
                Use MCP Tools: {request.customization.use_mcp_tools}
                Use A2A: {request.customization.use_a2a}
                
                Specification Content:
                {spec.content}
                
                Mode: {request.mode}
                
                {"If MCP Tools is enabled, leverage Model Context Protocol capabilities in your implementation." if request.customization.use_mcp_tools else ""}
                {"If A2A is enabled, utilize Agent-to-Agent communication patterns in your implementation." if request.customization.use_a2a else ""}
                """.strip(),
                "repo_url": "https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview"
            }
            
            headers = {
                "Authorization": f"Bearer {request.api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                devin_api_url = os.getenv("DEVIN_API_BASE_URL", "https://api.devin.ai")
                response = await client.post(
                    f"{devin_api_url}/sessions",
                    json=devin_payload,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "message": f"Successfully assigned specification implementation to Devin",
                        "session_id": result.get("session_id"),
                        "session_url": result.get("session_url"),
                        "agent": "devin",
                        "spec_title": spec.title
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Failed to assign to Devin: {response.text}",
                        "agent": "devin"
                    }
        
        return {
            "status": "error",
            "message": f"Agent {request.agent_id} not supported for specifications",
            "agent": request.agent_id
        }
        
    except Exception as e:
        logger.error(f"Error in assign_spec_to_swe_agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))
legacy_templates_removed = """
    {
        "id": "ai-red-teaming-agent",
        "title": "AI Red Teaming Agent",
        "description": "Facilitates the development of a copilot to accelerate your AI red teaming process: through multi-agent system that automates the generation, transformation, and execution of harmful prompts against target generative AI models or applications for AI red teaming purposes. Useful for streamlining safety testing workflows, surfacing guardrail bypasses, and guiding risk mitigation planning.",
        "tags": ["Multi-agent", "Advanced", "Security"],
        "languages": [".NET/C#", "Python"],
        "models": ["GPT-4", "GPT-4 Turbo"],
        "databases": ["Azure AI Search"],
        "collection": "Microsoft",
        "task": "Multi-agent",
        "pattern": "Evaluator-optimizer",
        "github_url": "https://aka.ms/ai-red-teaming",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": True,
        "icon": "🔒",
        "created_at": "2024-07-01"
    },
    {
        "id": "saifr-communication-compliance-agent",
        "title": "Saifr Communication Compliance Agent",
        "description": "The Saifr Communication Compliance Agent identifies potentially noncompliant text and generates a more compliant, fair, and balanced version, helping end users better adhere to relevant regulatory guidelines",
        "tags": ["Single-agent", "Intermediate", "OpenAPI Specified Tool"],
        "languages": ["Python", "JavaScript"],
        "models": ["GPT-4", "GPT-4 Omni mini"],
        "databases": ["Azure AI Search"],
        "collection": "Saifr from Fidelity Labs",
        "task": "Single-agent",
        "github_url": "https://aka.ms/saifr-communication-agent",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": False,
        "icon": "🔒",
        "created_at": "2024-07-01"
    },
    {
        "id": "auquan-due-diligence-risk-analyst",
        "title": "Auquan Due Diligence Risk Analyst",
        "description": "Helps create agents that assess risks across financial, operational, regulatory, and ESG domains",
        "tags": ["Single-agent", "Intermediate", "OpenAPI Specified Tool"],
        "languages": ["Python", "JavaScript"],
        "models": ["GPT-4", "GPT-4 Omni mini"],
        "databases": ["Azure AI Search"],
        "collection": "Auquan",
        "task": "Single-agent",
        "github_url": "https://aka.ms/due-diligence-risk-analyst-agent",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": False,
        "icon": "💼",
        "created_at": "2024-07-01"
    },
    {
        "id": "healthcare-agent-orchestrator",
        "title": "Healthcare Agent Orchestrator",
        "description": "Facilitates the development and testing of modular specialized agents that coordinate across diverse data types and tools like M365 and Teams to assist multi-disciplinary healthcare workflows—such as cancer care.",
        "tags": ["Multi-agent", "Advanced", "Healthcare"],
        "languages": [".NET/C#", "Python"],
        "models": ["GPT-4", "GPT-4 Turbo"],
        "databases": ["Azure AI Search"],
        "collection": "Microsoft",
        "task": "Multi-agent",
        "pattern": "Orchestrator",
        "github_url": "https://aka.ms/healthcare-multi-agent",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": False,
        "icon": "🏥",
        "created_at": "2024-07-01"
    },
    {
        "id": "researchflow-agent",
        "title": "ResearchFlow Agent",
        "description": "Helps create agents that execute complex, multi-step research workflows and solve open-ended tasks",
        "tags": ["Multi-agent", "Advanced", "Research"],
        "languages": ["Python", "JavaScript"],
        "models": ["GPT-4", "GPT-4 Turbo"],
        "databases": ["Azure AI Search"],
        "collection": "Microsoft",
        "task": "Multi-agent",
        "github_url": "https://aka.ms/research-flow",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": True,
        "icon": "🔧",
        "created_at": "2024-07-01"
    },
    {
        "id": "magentic-one-agent",
        "title": "Magentic-One Agent",
        "description": "A generalist, autonomous multi-agent system that performs deep research and problem-solving by orchestrating web search, code generation, and code execution agents. Helpful for tackling open-ended analytical or technical tasks.",
        "tags": ["Multi-agent", "Advanced", "Code Generation"],
        "languages": ["Python", "JavaScript"],
        "models": ["GPT-4", "GPT-4 Turbo"],
        "databases": ["Azure AI Search"],
        "collection": "Microsoft",
        "task": "Multi-agent",
        "github_url": "https://aka.ms/magnetic-one",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": True,
        "icon": "🤖",
        "created_at": "2024-07-01"
    },
    {
        "id": "sightmachine-filler-optimization-agent",
        "title": "SightMachine Filler Optimization Agent",
        "description": "The SightMachine Filler Optimization Agent supports building agents that analyze manufacturing data to reduce bottlenecks and improve throughput via predictive insights",
        "tags": ["Single-agent", "Intermediate", "Azure Functions"],
        "languages": ["Python", "JavaScript"],
        "models": ["GPT-4", "GPT-4 Omni mini"],
        "databases": ["Azure Functions"],
        "collection": "SightMachine",
        "task": "Single-agent",
        "github_url": "https://aka.ms/sight-machine-filler-optimization",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": False,
        "icon": "📊",
        "created_at": "2024-07-01"
    },
    {
        "id": "marquee-insights-ai-news-agent",
        "title": "Marquee Insights AI News Agent",
        "description": "Enables creating an agent that retrieves and summarize news focused on Microsoft, healthcare, and legal sectors",
        "tags": ["Single-agent", "Intermediate", "News"],
        "languages": ["Python", "JavaScript"],
        "models": ["GPT-4", "GPT-4 Omni mini"],
        "databases": ["Azure AI Search"],
        "collection": "Marquee Insights",
        "task": "Single-agent",
        "github_url": "https://aka.ms/ai-news-agent",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": False,
        "icon": "📰",
        "created_at": "2024-07-01"
    },
    {
        "id": "mihcm-hr-assist-agent",
        "title": "MiHCM HR Assist Agent",
        "description": "Supports agent development for HR scenarios by enabling employees to navigate HR-related records like leave balances, HR requests and work activities using MiHCM's HR APIs",
        "tags": ["Single-agent", "Intermediate", "OpenAPI Specified Tool"],
        "languages": ["Python", "JavaScript"],
        "models": ["GPT-4", "GPT-4 Omni mini"],
        "databases": ["Azure AI Search"],
        "collection": "MiHCM",
        "task": "Single-agent",
        "github_url": "https://aka.ms/hr-agent",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": False,
        "icon": "💼",
        "created_at": "2024-07-01"
    },
    {
        "id": "portfolio-navigator",
        "title": "Portfolio Navigator",
        "description": "Supports agent creation for exploring financial topics from Morningstar data and Grounding with Bing",
        "tags": ["Single-agent", "Beginner", "Morningstar", "Grounding with Bing"],
        "languages": ["Python", "JavaScript"],
        "models": ["GPT-4", "GPT-4 Omni mini"],
        "databases": ["Azure AI Search"],
        "collection": "Microsoft",
        "task": "Single-agent",
        "github_url": "https://aka.ms/trusty-link",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": False,
        "icon": "💼",
        "created_at": "2024-07-01"
    },
    {
        "id": "travel-planner",
        "title": "Travel Planner",
        "description": "Enables agent creation for travel scenarios",
        "tags": ["Single-agent", "Beginner", "File Search", "Code Interpreter"],
        "languages": ["Python", "JavaScript"],
        "models": ["GPT-4", "GPT-4 Omni mini"],
        "databases": ["File Search", "Code Interpreter"],
        "collection": "Microsoft",
        "task": "Single-agent",
        "github_url": "https://aka.ms/travel-planner",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": False,
        "icon": "✈️",
        "created_at": "2024-07-01"
    },
    {
        "id": "home-loan-guide",
        "title": "Home Loan Guide",
        "description": "Enables agent creation to provide users with helpful information about mortgage applications at a fictitious company, Contoso Bank.",
        "tags": ["Single-agent", "Beginner", "Connected Agents", "File Search"],
        "languages": ["Python", "JavaScript"],
        "models": ["GPT-4", "GPT-4 Omni mini"],
        "databases": ["File Search", "Code Interpreter"],
        "collection": "Microsoft",
        "task": "Single-agent",
        "github_url": "https://aka.ms/home-loan-guide",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": False,
        "icon": "🏠",
        "created_at": "2024-07-01"
    },
    {
        "id": "sales-analyst-agent",
        "title": "Sales Analyst Agent",
        "description": "Supports building agents that analyze sales data",
        "tags": ["Single-agent", "Beginner", "File Search", "Code Interpreter"],
        "languages": ["Python", "JavaScript"],
        "models": ["GPT-4", "GPT-4 Omni mini"],
        "databases": ["File Search", "Code Interpreter"],
        "collection": "Microsoft",
        "task": "Single-agent",
        "github_url": "https://aka.ms/sales-analyst",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": False,
        "icon": "📊",
        "created_at": "2024-07-01"
    },
    {
        "id": "customer-service-agent",
        "title": "Customer Service Agent",
        "description": "Helps create a multi-agent system that manages full-cycle support resolution —from authentication to escalation to resolution",
        "tags": ["Multi-agent", "Advanced", "Customer Service"],
        "languages": ["Python", "JavaScript"],
        "models": ["GPT-4", "GPT-4 Turbo"],
        "databases": ["Azure AI Search"],
        "collection": "Microsoft",
        "task": "Multi-agent",
        "github_url": "https://aka.ms/customer-service",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": False,
        "icon": "🎯",
        "created_at": "2024-07-01"
    },
    {
        "id": "warranty-claim-processing-agent",
        "title": "Warranty Claim Processing Agent",
        "description": "Facilitates the development of agents for processing warranty claims",
        "tags": ["Single-agent", "Intermediate", "OpenAPI Specified Tool"],
        "languages": [".NET/C#", "Python"],
        "models": ["GPT-4", "GPT-4 Omni mini"],
        "databases": ["Azure AI Search"],
        "collection": "Microsoft",
        "task": "Single-agent",
        "github_url": "https://aka.ms/warranty-claim-processing",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": False,
        "icon": "🔧",
        "created_at": "2024-07-01"
    },
    {
        "id": "voice-live-agent",
        "title": "Voice Live Agent",
        "description": "Enables agent development for real-time, voice-based interactions using Azure AI Voice Live API.",
        "tags": ["Single-agent", "Intermediate", "Voice"],
        "languages": ["Python", "JavaScript"],
        "models": ["GPT-4", "GPT-4 Omni mini"],
        "databases": ["Azure AI Search"],
        "collection": "Microsoft",
        "task": "Single-agent",
        "github_url": "https://aka.ms/voice-live-agent",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": False,
        "icon": "🎤",
        "created_at": "2024-07-01"
    },
    {
        "id": "text-translation-agent",
        "title": "Text Translation Agent",
        "description": "Helps create agents that handle multilingual text processing, including dynamic language detection and bidirectional translation using Azure AI Translator service",
        "tags": ["Single-agent", "Beginner", "OpenAPI Specified Tool"],
        "languages": ["Python", "JavaScript"],
        "models": ["GPT-4", "GPT-4 Omni mini"],
        "databases": ["Azure AI Search"],
        "collection": "Microsoft",
        "task": "Single-agent",
        "github_url": "https://aka.ms/translation-agent",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": False,
        "icon": "🌍",
        "created_at": "2024-07-01"
    },
    {
        "id": "video-translation-agent",
        "title": "Video Translation Agent",
        "description": "Supports building agents for multilingual video localization with translation, subtitles, and speech generation",
        "tags": ["Single-agent", "Beginner", "Video"],
        "languages": [".NET/C#", "Python"],
        "models": ["GPT-4", "GPT-4 Omni mini"],
        "databases": ["Azure AI Search"],
        "collection": "Microsoft",
        "task": "Single-agent",
        "github_url": "https://aka.ms/video-translation-agent",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": False,
        "icon": "🎬",
        "created_at": "2024-07-01"
    },
    {
        "id": "intent-routing-agent",
        "title": "Intent Routing Agent",
        "description": "Helps create agents that detect user intent and provide exact answering. Perfect for deterministically intent routing and exact question answering with human controls.",
        "tags": ["Single-agent", "Beginner", "OpenAPI Specified Tool"],
        "languages": ["Python", "JavaScript"],
        "models": ["GPT-4", "GPT-4 Omni mini"],
        "databases": ["Azure AI Search"],
        "collection": "Microsoft",
        "task": "Single-agent",
        "github_url": "https://aka.ms/intent-routing",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": False,
        "icon": "🎯",
        "created_at": "2024-07-01"
    },
    {
        "id": "exact-question-answering-agent",
        "title": "Exact Question Answering Agent",
        "description": "Supports building agents that answer predefined, high-value questions to ensure consistent and accurate responses.",
        "tags": ["Single-agent", "Beginner", "OpenAPI Specified Tool"],
        "languages": ["Python", "JavaScript"],
        "models": ["GPT-4", "GPT-4 Omni mini"],
        "databases": ["Azure AI Search"],
        "collection": "Microsoft",
        "task": "Single-agent",
        "github_url": "https://aka.ms/exact-question-answering",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": False,
        "icon": "❓",
        "created_at": "2024-07-01"
    },
    {
        "id": "contract-analysis-agent",
        "title": "Contract Analysis Agent",
        "description": "Enables creating agents that compare contract versions, extract key clauses, highlight differences, and generate review-ready reports.",
        "tags": ["Single-agent", "Intermediate", "File Search", "OpenAPI Specified Tool"],
        "languages": [".NET/C#", "Python"],
        "models": ["GPT-4", "GPT-4 Omni mini"],
        "databases": ["File Search"],
        "collection": "Microsoft",
        "task": "Single-agent",
        "github_url": "https://aka.ms/contract-analysis-agent",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": True,
        "icon": "📄",
        "created_at": "2024-07-01"
    },
    {
        "id": "sop-forge-agent",
        "title": "SOP Forge Agent",
        "description": "Helps create an agent that converts instructional videos into a fully formatted Standard Operating Procedure (SOP).",
        "tags": ["Single-agent", "Intermediate", "File Search", "OpenAPI Specified Tool"],
        "languages": [".NET/C#", "Python"],
        "models": ["GPT-4", "GPT-4 Omni mini"],
        "databases": ["File Search"],
        "collection": "Microsoft",
        "task": "Single-agent",
        "github_url": "https://aka.ms/sop-forge-agent",
        "fork_count": 0,
        "star_count": 0,
        "is_featured": True,
        "icon": "📋",
        "created_at": "2024-07-01"
    }
]

"""
patterns_data = [
    {
        "id": "prompt-chaining",
        "title": "Prompt Chaining Pattern",
        "description": "Sequential processing where the output of one agent becomes the input for the next, with conditional gates and error handling for complex multi-step workflows.",
        "type": "Sequential Processing",
        "use_cases": ["Multi-step workflows", "Data transformation pipelines", "Complex reasoning chains"],
        "github_url": "https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview"
    },
    {
        "id": "routing", 
        "title": "Routing Pattern",
        "description": "Intelligent request routing where a central router agent directs tasks to specialized agents based on content analysis and agent capabilities.",
        "type": "Request Routing",
        "use_cases": ["Content classification", "Task delegation", "Load balancing"],
        "github_url": "https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview"
    },
    {
        "id": "parallelization",
        "title": "Parallelization Pattern", 
        "description": "Concurrent processing where multiple agents work simultaneously on different aspects of a task, with results aggregated for comprehensive output.",
        "type": "Concurrent Processing",
        "use_cases": ["Parallel analysis", "Multi-perspective evaluation", "Distributed processing"],
        "github_url": "https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview"
    },
    {
        "id": "orchestrator",
        "title": "Orchestrator Pattern",
        "description": "Complex workflow management where an orchestrator coordinates multiple specialized agents and synthesizes their outputs into cohesive results.",
        "type": "Workflow Management", 
        "use_cases": ["Complex workflows", "Multi-agent coordination", "Result synthesis"],
        "github_url": "https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview"
    },
    {
        "id": "evaluator-optimizer",
        "title": "Evaluator-Optimizer Pattern",
        "description": "Iterative improvement system where a generator creates solutions and an evaluator provides feedback, creating a continuous optimization loop.",
        "type": "Iterative Improvement",
        "use_cases": ["Solution optimization", "Quality improvement", "Iterative refinement"],
        "github_url": "https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview"
    }
]

filter_options_data = {
    "tasks": ["Single-agent", "Multi-agent"],
    "languages": [".NET/C#", "JavaScript", "Python"],
    "collections": ["Microsoft", "Auquan", "Saifr from Fidelity Labs", "SightMachine", "Marquee Insights", "MiHCM"],
    "models": ["GPT-4", "GPT-4 Omni mini", "GPT-4 Turbo"],
    "databases": ["Azure AI Search", "File Search", "Code Interpreter", "Azure Functions"],
    "patterns": ["Prompt Chaining", "Routing", "Parallelization", "Orchestrator", "Evaluator-optimizer"]
}

learning_resources_data = [
    {
        "id": "azure-ai-fundamentals",
        "title": "Azure AI Fundamentals",
        "description": "Learn the fundamentals of artificial intelligence (AI) and how to implement AI solutions on Azure.",
        "url": "https://docs.microsoft.com/learn/paths/get-started-with-artificial-intelligence-on-azure/",
        "type": "Learning Path",
        "icon": "📚"
    },
    {
        "id": "openai-service",
        "title": "Azure OpenAI Service",
        "description": "Explore Azure OpenAI Service and learn how to integrate powerful AI models into your applications.",
        "url": "https://docs.microsoft.com/azure/cognitive-services/openai/",
        "type": "Documentation",
        "icon": "🔧"
    }
]

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/api/templates", response_model=List[Template])
async def get_templates(
    search: Optional[str] = Query(None, description="Search templates by title or description"),
    task: Optional[str] = Query(None, description="Filter by task type"),
    language: Optional[str] = Query(None, description="Filter by programming language"),
    collection: Optional[str] = Query(None, description="Filter by collection"),
    model: Optional[str] = Query(None, description="Filter by AI model"),
    database: Optional[str] = Query(None, description="Filter by database"),
    sort: Optional[str] = Query("Most Popular", description="Sort order")
):
    filtered = list(templates_data)

    if search:
        s = search.lower()
        filtered = [t for t in filtered if s in t.title.lower() or s in t.description.lower()]

    if task:
        filtered = [t for t in filtered if task == t.task or task in t.tags]

    if language:
        filtered = [t for t in filtered if language in t.languages]

    if collection:
        filtered = [t for t in filtered if t.collection == collection]

    if model:
        filtered = [t for t in filtered if model in t.models]

    if database:
        filtered = [t for t in filtered if database in t.databases]

    if sort == "Most Popular":
        filtered.sort(key=lambda t: t.star_count, reverse=True)
    elif sort == "Most Recent":
        filtered.sort(key=lambda t: t.created_at or "", reverse=True)
    elif sort == "Most Forked":
        filtered.sort(key=lambda t: t.fork_count, reverse=True)

    return [t.model_dump() for t in filtered]

@app.get("/api/templates/featured", response_model=List[Template])
async def get_featured_templates():
    featured = [t for t in templates_data if t.is_featured]
    return [t.model_dump() for t in featured]

@app.get("/api/templates/{template_id}", response_model=Template)
async def get_template(template_id: str):
    t = template_by_id.get(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return t.model_dump()

@app.get("/api/filters", response_model=FilterOptions)
async def get_filters():
    tasks = sorted({t.task for t in templates_data if t.task})
    languages = sorted({lang for t in templates_data for lang in t.languages})
    collections = sorted({t.collection for t in templates_data if t.collection})
    models = sorted({m for t in templates_data for m in t.models})
    databases = sorted({d for t in templates_data for d in t.databases})
    patterns = sorted({t.pattern for t in templates_data if t.pattern})
    return FilterOptions(tasks=tasks, languages=languages, collections=collections, models=models, databases=databases, patterns=patterns).model_dump()

@app.get("/api/learning-resources", response_model=List[LearningResource])
async def get_learning_resources():
    """Get learning resources"""
    return [LearningResource(**resource) for resource in learning_resources_data]

@app.post("/api/templates/{template_id}/breakdown")
async def generate_task_breakdown(template_id: str, request: CustomizationRequest):
    """Generate task breakdown using Azure AI Agents Service"""
    print(f"DEBUG: Received request for template_id: {template_id}")
    print(f"DEBUG: Request data: {request}")
    print(f"DEBUG: Request dict: {request.dict()}")
    try:
        template = next((t for t in templates_data if t["id"] == template_id), None)
        pattern = None
        
        if not template:
            pattern = next((p for p in patterns_data if p["id"] == template_id), None)
            if not pattern:
                raise HTTPException(status_code=404, detail="Template or pattern not found")
        
        project_endpoint = os.getenv("AZURE_PROJECT_ENDPOINT")
        api_key = os.getenv("AZURE_API_KEY")
        model_name = os.getenv("AZURE_MODEL_NAME", "gpt-4.1-nano")
        
        if not project_endpoint or not api_key:
            raise HTTPException(
                status_code=500, 
                detail="Azure AI configuration not found. Please set AZURE_PROJECT_ENDPOINT and AZURE_API_KEY environment variables."
            )
        
        try:
            with AIProjectClient(
                endpoint=project_endpoint,
                credential=AzureKeyCredential(api_key)
            ) as project_client:
                agents_client = project_client.agents
                
                agent = agents_client.create_agent(
                    model=model_name,
                    name="task-breakdown-agent",
                    instructions="""You are a task breakdown specialist for software development projects. 
                    Given a solution template and customization requirements, break down the work into specific, actionable tasks.
                    
                    For each task, provide:
                    - A clear, specific title
                    - Detailed description of what needs to be done
                    - Estimated time to complete
                    - Priority level (high, medium, low)
                    - Status (always 'pending' for new tasks)
                    
                    Focus on practical implementation steps like:
                    - Code customization and configuration
                    - UI/UX modifications for branding
                    - Integration of specific requirements
                    - Testing and validation
                    - Documentation updates
                    
                    Return your response as a JSON array of task objects with the following structure:
                    [
                      {
                        "id": "task-1",
                        "title": "Task title",
                        "description": "Detailed description",
                        "estimatedTime": "X-Y hours",
                        "estimatedTokens": "X-Y tokens",
                        "priority": "high|medium|low",
                        "status": "pending"
                      }
                    ]"""
                )
                
                thread = agents_client.threads.create()
                
                if template:
                    prompt = f"""
                    Please break down the following software customization project into specific tasks:
                    
                    **Template Information:**
                    - Name: {template['title']}
                    - Description: {template['description']}
                    - Technology Stack: {template.get('languages', ['N/A'])[0] if template.get('languages') else 'N/A'}, {template.get('databases', ['N/A'])[0] if template.get('databases') else 'N/A'}
                    - Repository: {template['github_url']}
                    
                    **Customization Requirements:**
                    - Company: {request.company_name}
                    - Industry: {request.industry}
                    - Use Case: {request.use_case}
                    - Brand Theme: {request.brand_theme}
                    - Primary Color: {request.primary_color}
                    - Customer Scenario: {request.customer_scenario}
                    - Additional Requirements: {request.additional_requirements}
                    - Use MCP Tools: {request.use_mcp_tools}
                    - Use A2A: {request.use_a2a}
                    
                    Please provide a detailed task breakdown for implementing these customizations. If MCP Tools is enabled, include tasks that leverage Model Context Protocol capabilities. If A2A is enabled, include tasks that utilize Agent-to-Agent communication patterns.
                    """
                else:  # pattern
                    pattern_title = pattern['title'] if pattern else "AI Agent Pattern"
                    pattern_description = pattern['description'] if pattern else "Custom AI agent pattern implementation"
                    pattern_type = pattern['type'] if pattern else "multi-agent"
                    pattern_use_cases = ', '.join(pattern['use_cases']) if pattern and pattern.get('use_cases') else "General purpose AI agent tasks"
                    
                    prompt = f"""
                    Please break down the following AI agent pattern implementation into specific tasks:
                    
                    **Pattern Information:**
                    - Pattern: {pattern_title}
                    - Description: {pattern_description}
                    - Type: {pattern_type}
                    - Use Cases: {pattern_use_cases}
                    
                    **Implementation Requirements:**
                    - Scenario: {request.customer_scenario}
                    - Input Format: {request.brand_theme.split(' → ')[0] if ' → ' in request.brand_theme else 'Not specified'}
                    - Output Format: {request.brand_theme.split(' → ')[1] if ' → ' in request.brand_theme else 'Not specified'}
                    - Agent Configuration: {request.additional_requirements}
                    - Company/Project: {request.company_name}
                    - Industry Context: {request.industry}
                    - Use MCP Tools: {request.use_mcp_tools}
                    - Use A2A: {request.use_a2a}
                    
                    Please provide a detailed task breakdown for implementing this AI agent pattern. If MCP Tools is enabled, include tasks that leverage Model Context Protocol capabilities. If A2A is enabled, include tasks that utilize Agent-to-Agent communication patterns.
                    """
                
                message = agents_client.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=prompt
                )
                
                run = agents_client.runs.create_and_process(
                    thread_id=thread.id, 
                    agent_id=agent.id
                )
                
                if run.status == "failed":
                    raise HTTPException(status_code=500, detail=f"Agent run failed: {run.last_error}")
                
                messages = agents_client.messages.list(thread_id=thread.id)
                response_content = ""
                for msg in messages:
                    if msg.text_messages:
                        response_content = msg.text_messages[-1].text.value
                        break
                
                agents_client.delete_agent(agent.id)
        except Exception as azure_error:
            print(f"Azure AI authentication failed: {azure_error}. Using mock response for local testing.")
            if template:
                return [
                    {
                        "id": "task-1",
                        "title": f"Customize {template['title']} for {request.company_name}",
                        "description": f"Adapt the {template['title']} template to match {request.industry} industry requirements and {request.use_case} use case. Implement core functionality and integrate with existing systems.",
                        "estimatedTime": "4-6 hours",
                        "estimatedTokens": "15000-25000 tokens",
                        "priority": "high",
                        "status": "pending"
                    },
                    {
                        "id": "task-2", 
                        "title": "Apply brand theme and styling",
                        "description": f"Implement {request.brand_theme} brand theme with primary color {request.primary_color}. Update UI components, logos, and visual elements to match company branding.",
                        "estimatedTime": "2-3 hours",
                        "estimatedTokens": "8000-12000 tokens",
                        "priority": "medium",
                        "status": "pending"
                    },
                    {
                        "id": "task-3",
                        "title": "Integrate additional requirements",
                        "description": f"Implement specific requirements: {request.additional_requirements}. Ensure compatibility with {request.customer_scenario} scenario.",
                        "estimatedTime": "3-4 hours", 
                        "estimatedTokens": "12000-18000 tokens",
                        "priority": "medium",
                        "status": "pending"
                    },
                    {
                        "id": "task-4",
                        "title": "Testing and validation",
                        "description": f"Perform comprehensive testing of the customized {template['title']} solution. Validate functionality, performance, and user experience for {request.use_case} use case.",
                        "estimatedTime": "2-3 hours",
                        "estimatedTokens": "6000-10000 tokens",
                        "priority": "high",
                        "status": "pending"
                    },
                    {
                        "id": "task-5",
                        "title": "Documentation and deployment",
                        "description": f"Create deployment documentation and user guides for the customized solution. Prepare for production deployment in {request.industry} environment.",
                        "estimatedTime": "1-2 hours",
                        "estimatedTokens": "4000-6000 tokens",
                        "priority": "low",
                        "status": "pending"
                    }
                ]
            else:  # pattern
                pattern_title = pattern['title'] if pattern else "AI Agent Pattern"
                pattern_type = pattern['type'] if pattern else "multi-agent"
                return [
                    {
                        "id": "task-1",
                        "title": f"Implement {pattern_title} for {request.company_name}",
                        "description": f"Design and implement the {pattern_title} using {request.customer_scenario}. Set up the core pattern structure and agent coordination.",
                        "estimatedTime": "4-6 hours",
                        "estimatedTokens": "18000-28000 tokens",
                        "priority": "high",
                        "status": "pending"
                    },
                    {
                        "id": "task-2", 
                        "title": "Configure agent interactions",
                        "description": f"Set up agent communication and data flow according to {pattern_type} pattern. Configure input format: {request.brand_theme.split(' → ')[0] if ' → ' in request.brand_theme else 'Not specified'}.",
                        "estimatedTime": "3-4 hours",
                        "estimatedTokens": "12000-18000 tokens",
                        "priority": "high",
                        "status": "pending"
                    },
                    {
                        "id": "task-3",
                        "title": "Implement output formatting",
                        "description": f"Configure output generation to match required format: {request.brand_theme.split(' → ')[1] if ' → ' in request.brand_theme else 'Not specified'}. Ensure proper data transformation.",
                        "estimatedTime": "2-3 hours", 
                        "estimatedTokens": "8000-12000 tokens",
                        "priority": "medium",
                        "status": "pending"
                    },
                    {
                        "id": "task-4",
                        "title": "Apply agent configuration",
                        "description": f"Implement specific agent settings: {request.additional_requirements}. Fine-tune agent behavior and performance.",
                        "estimatedTime": "2-3 hours",
                        "estimatedTokens": "8000-12000 tokens",
                        "priority": "medium",
                        "status": "pending"
                    },
                    {
                        "id": "task-5",
                        "title": "Testing and validation",
                        "description": f"Test the {pattern_title} implementation with sample data. Validate pattern behavior and performance for {request.use_case} use case.",
                        "estimatedTime": "2-3 hours",
                        "estimatedTokens": "6000-10000 tokens",
                        "priority": "high",
                        "status": "pending"
                    }
                ]
        
        try:
            json_match = re.search(r'\[.*\]', response_content, re.DOTALL)
            if json_match:
                tasks_json = json_match.group(0)
                tasks = json.loads(tasks_json)
            else:
                if template:
                    tasks = [
                        {
                            "id": "task-1",
                            "title": f"Customize {template['title']} for {request.company_name}",
                            "description": f"Adapt the template to match {request.industry} industry requirements and {request.use_case} use case",
                            "estimatedTime": "2-3 hours",
                            "estimatedTokens": "10000-15000 tokens",
                            "priority": "high",
                            "status": "pending"
                        },
                        {
                            "id": "task-2", 
                            "title": "Apply brand theme and styling",
                            "description": f"Implement {request.brand_theme} with primary color {request.primary_color}",
                            "estimatedTime": "1-2 hours",
                            "estimatedTokens": "5000-8000 tokens",
                            "priority": "medium",
                            "status": "pending"
                        },
                        {
                            "id": "task-3",
                            "title": "Integrate additional requirements",
                            "description": f"Implement: {request.additional_requirements}",
                            "estimatedTime": "1-2 hours", 
                            "estimatedTokens": "5000-8000 tokens",
                            "priority": "low",
                            "status": "pending"
                        }
                    ]
                else:  # pattern
                    pattern_title = pattern['title'] if pattern else "AI Agent Pattern"
                    pattern_type = pattern['type'] if pattern else "multi-agent"
                    tasks = [
                        {
                            "id": "task-1",
                            "title": f"Implement {pattern_title} for {request.company_name}",
                            "description": f"Set up the {pattern_title} pattern structure and agent coordination",
                            "estimatedTime": "3-4 hours",
                            "estimatedTokens": "15000-20000 tokens",
                            "priority": "high",
                            "status": "pending"
                        },
                        {
                            "id": "task-2", 
                            "title": "Configure agent interactions",
                            "description": f"Set up agent communication according to {pattern_type} pattern",
                            "estimatedTime": "2-3 hours",
                            "estimatedTokens": "10000-15000 tokens",
                            "priority": "medium",
                            "status": "pending"
                        },
                        {
                            "id": "task-3",
                            "title": "Apply configuration",
                            "description": f"Implement: {request.additional_requirements}",
                            "estimatedTime": "1-2 hours", 
                            "estimatedTokens": "5000-8000 tokens",
                            "priority": "low",
                            "status": "pending"
                        }
                    ]
            
            return tasks
            
        except json.JSONDecodeError:
            if template:
                return [
                                    {
                    "id": "task-1",
                    "title": f"Customize {template['title']} for {request.company_name}",
                    "description": f"Adapt the template to match {request.industry} industry requirements and {request.use_case} use case",
                    "estimatedTime": "2-3 hours",
                    "estimatedTokens": "10000-15000 tokens",
                    "priority": "high",
                    "status": "pending"
                },
                {
                    "id": "task-2", 
                    "title": "Apply brand theme and styling",
                    "description": f"Implement {request.brand_theme} with primary color {request.primary_color}",
                    "estimatedTime": "1-2 hours",
                    "estimatedTokens": "5000-8000 tokens",
                    "priority": "medium",
                    "status": "pending"
                },
                {
                    "id": "task-3",
                    "title": "Integrate additional requirements",
                    "description": f"Implement: {request.additional_requirements}",
                    "estimatedTime": "1-2 hours", 
                    "estimatedTokens": "5000-8000 tokens",
                    "priority": "low",
                    "status": "pending"
                }
                ]
            else:  # pattern
                pattern_title = pattern['title'] if pattern else "AI Agent Pattern"
                pattern_type = pattern['type'] if pattern else "multi-agent"
                return [
                                    {
                    "id": "task-1",
                    "title": f"Implement {pattern_title} for {request.company_name}",
                    "description": f"Set up the {pattern_title} pattern structure and agent coordination",
                    "estimatedTime": "3-4 hours",
                    "estimatedTokens": "15000-20000 tokens",
                    "priority": "high",
                    "status": "pending"
                },
                {
                    "id": "task-2", 
                    "title": "Configure agent interactions",
                    "description": f"Set up agent communication according to {pattern_type} pattern",
                    "estimatedTime": "2-3 hours",
                    "estimatedTokens": "10000-15000 tokens",
                    "priority": "medium",
                    "status": "pending"
                },
                {
                    "id": "task-3",
                    "title": "Apply configuration",
                    "description": f"Implement: {request.additional_requirements}",
                    "estimatedTime": "1-2 hours", 
                    "estimatedTokens": "5000-8000 tokens",
                    "priority": "low",
                    "status": "pending"
                }
                ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating task breakdown: {str(e)}")

@app.post("/api/templates/{template_id}/assign")
async def assign_to_swe_agent(template_id: str, request: SWEAgentRequest):
    """Assign customization task to SWE agent"""
    try:
        template = next((t for t in templates_data if t["id"] == template_id), None)
        pattern = None
        if not template:
            pattern = next((p for p in patterns_data if p["id"] == template_id), None)
            if not pattern:
                raise HTTPException(status_code=404, detail="Template or pattern not found")
        
        if request.agent_id == "devin":
            # Use template or pattern data
            item = template if template else pattern
            item_type = "template" if template else "pattern"
            
            devin_payload = {
                "prompt": f"""
                Customize the {item['title']} {item_type} for the following scenario:
                
                Customer: {request.customization.company_name}
                Industry: {request.customization.industry}
                Use Case: {request.customization.use_case}
                Brand Theme: {request.customization.brand_theme}
                Primary Color: {request.customization.primary_color}
                
                Customer Scenario: {request.customization.customer_scenario}
                Additional Requirements: {request.customization.additional_requirements}
                
                Use MCP Tools: {request.customization.use_mcp_tools}
                Use A2A: {request.customization.use_a2a}
                
                Repository: {item.get('github_url', 'https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview')}
                Mode: {request.mode}
                
                {"If MCP Tools is enabled, leverage Model Context Protocol capabilities in your implementation." if request.customization.use_mcp_tools else ""}
                {"If A2A is enabled, utilize Agent-to-Agent communication patterns in your implementation." if request.customization.use_a2a else ""}
                """.strip(),
                "repo_url": item['github_url']
            }
            
            headers = {
                "Authorization": f"Bearer {request.api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                devin_api_url = os.getenv("DEVIN_API_BASE_URL", "https://api.devin.ai")
                response = await client.post(
                    f"{devin_api_url}/v1/sessions",
                    json=devin_payload,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    devin_response = response.json()
                    return {
                        "status": "success",
                        "agent": "devin",
                        "session_id": devin_response.get("session_id"),
                        "message": "Task assigned to Devin successfully"
                    }
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Devin API error: {response.text}"
                    )
                    
        elif request.agent_id == "github-copilot":
            # Use template or pattern data
            item = template if template else pattern
            item_type = "template" if template else "pattern"
            
            if request.customization.use_mcp_tools:
                try:
                    repo_url = item.get('github_url', 'https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview')
                    match = re.search(r'github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$', repo_url)
                    if not match:
                        raise ValueError(f"Could not extract owner/repo from URL: {repo_url}")
                    
                    owner, repo = match.groups()
                    
                    problem_statement = f"""
Implement customizations for {item['title']} {item_type}:

Customer: {request.customization.company_name}
Industry: {request.customization.industry}
Use Case: {request.customization.use_case}
Brand Theme: {request.customization.brand_theme}
Primary Color: {request.customization.primary_color}

Customer Scenario: {request.customization.customer_scenario}
Additional Requirements: {request.customization.additional_requirements}

Repository: {repo_url}
Mode: {request.mode}

Please implement these customizations following best practices and maintaining code quality.
                    """.strip()
                    
                    pr_title = f"Implement {item['title']} {item_type} customizations for {request.customization.company_name}"
                    
                    mcp_client = create_github_mcp_client()
                    result = await mcp_client.create_pull_request_with_copilot(
                        owner=owner,
                        repo=repo,
                        problem_statement=problem_statement,
                        title=pr_title,
                        base_ref="main"
                    )
                    
                    if "error" in result:
                        raise Exception(result["error"])
                    
                    if "error" not in result and not result.get("isError", False):
                        logger.info(f"Successfully created GitHub Copilot PR for {owner}/{repo}: {result}")
                        return {
                            "status": "success",
                            "agent": "github-copilot",
                            "message": f"GitHub Copilot is working on your request. Check the repository for updates.",
                            "result": result
                        }
                    else:
                        error_msg = result.get("content", [{}])[0].get("text", "Unknown error") if result.get("content") else str(result)
                        logger.warning(f"GitHub Copilot MCP call returned error: {error_msg}")
                        return {
                            "status": "partial_success",
                            "agent": "github-copilot",
                            "message": f"GitHub Copilot MCP integration is working, but encountered an authentication issue. Please ensure your GitHub PAT has the required permissions (repo, workflow scopes) and that GitHub Copilot is enabled for this repository. Error: {error_msg}",
                            "result": result
                        }
                    
                except Exception as e:
                    logger.error(f"MCP GitHub Copilot error: {e}")
                    logger.info("Falling back to placeholder GitHub Copilot implementation")
                    return {
                        "status": "success",
                        "agent": "github-copilot", 
                        "message": f"Task assigned to GitHub Copilot (MCP failed, using placeholder implementation). Error: {str(e)}"
                    }
            else:
                return {
                    "status": "success",
                    "agent": "github-copilot", 
                    "message": "Task assigned to GitHub Copilot (MCP Tools not enabled - using placeholder implementation)"
                }
            
        elif request.agent_id == "replit":
            return {
                "status": "success",
                "agent": "replit",
                "message": "Task assigned to Replit Agent (placeholder implementation)"
            }
            
        elif request.agent_id == "codex-cli":
            return {
                "status": "success", 
                "agent": "codex-cli",
                "message": "Task assigned to Codex-cli (placeholder implementation)"
            }
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported agent: {request.agent_id}")
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error assigning to SWE agent: {str(e)}")
