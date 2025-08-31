from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .api.routes import auth, templates, specs, users, agents
from .data.static_data import learning_resources_data, patterns_data
from .models.schemas import LearningResource
from .api.dependencies import get_template_service

logger = logging.getLogger(__name__)

app = FastAPI(title="AIFoundry.app API", description="API for AI App Templates")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(templates.router, prefix="/api/templates", tags=["templates"])
app.include_router(specs.router, prefix="/api/specs", tags=["specs"])
app.include_router(users.router, prefix="/api/user", tags=["users"])
app.include_router(agents.router, prefix="/api", tags=["agents"])

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
    endpoint: Optional[str] = None
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

try:
    github_app_client = GitHubAppClient()
except ValueError as e:
    logger.warning(f"GitHub App client initialization failed: {e}. GitHub App features will be disabled.")
    github_app_client = None

cosmos_service = CosmosService()

@app.get("/api/auth/github")
async def github_oauth_login():
    """Initiate GitHub OAuth flow"""
    client_id = os.getenv("GITHUB_CLIENT_ID")
    redirect_uri = os.getenv("GITHUB_REDIRECT_URI")
    
    if not client_id:
        raise HTTPException(status_code=500, detail="GITHUB_CLIENT_ID environment variable is required")
    if not redirect_uri:
        raise HTTPException(status_code=500, detail="GITHUB_REDIRECT_URI environment variable is required")
    
    scope = "repo,workflow,admin:repo_hook,public_repo"
    
    auth_url = f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}"
    return {"auth_url": auth_url}

@app.post("/api/auth/github/callback")
async def github_oauth_callback(request: Dict[str, str]):
    """Handle GitHub OAuth callback"""
    code = request.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")
    
    client_id = os.getenv("GITHUB_CLIENT_ID")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    
    if not client_id:
        raise HTTPException(status_code=500, detail="GITHUB_CLIENT_ID environment variable is required")
    if not client_secret:
        raise HTTPException(status_code=500, detail="GITHUB_CLIENT_SECRET environment variable is required")
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code
            },
            headers={"Accept": "application/json"}
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token received")
        
        user_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {access_token}"}
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user information")
        
        user_data = user_response.json()
        
        return {
            "access_token": access_token,
            "user": {
                "login": user_data["login"],
                "name": user_data.get("name"),
                "avatar_url": user_data["avatar_url"]
            }
        }

@app.get("/api/user/repositories")
async def get_user_repositories(
    authorization: str = Header(...),
    limit: int = Query(10, ge=1, le=100, description="Number of most recent repositories to return"),
    sort: str = Query("updated", description="Sort field: created, updated, pushed, full_name"),
    direction: str = Query("desc", description="Sort direction: asc or desc"),
    page: int = Query(1, ge=1, description="Page number for pagination")
):
    """Get user's most recent repositories.

    Defaults to the 10 most recently updated repositories. You can adjust the
    number returned using the `limit` query parameter (max 100).
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ")[1]

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user/repos",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
            },
            params={
                "sort": sort,
                "direction": direction,
                "per_page": limit,
                "page": page,
            },
        )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch repositories")

        return response.json()

@app.get("/api/user/repositories/search")
async def search_user_repositories(
    q: str = Query(..., min_length=1, description="Search text for repository name/description"),
    authorization: str = Header(...),
    limit: int = Query(10, ge=1, le=100, description="Max number of results to return"),
    sort: str = Query("updated", description="Sort: stars, forks, help-wanted-issues, updated"),
    order: str = Query("desc", description="Order: asc or desc"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
):
    """Search within the authenticated user's repositories by name/description.

    Uses GitHub's search API constrained to the user's login.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ")[1]

    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
            },
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=user_resp.status_code, detail="Failed to fetch user info")

        login = user_resp.json().get("login")
        if not login:
            raise HTTPException(status_code=400, detail="Could not determine user login")

        # Search name, description, and README. GitHub search supports in:name,description,readme
        query = f"{q} user:{login} in:name,description,readme"

        search_resp = await client.get(
            "https://api.github.com/search/repositories",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
            },
            params={
                "q": query,
                "per_page": limit,
                "sort": sort,
                "order": order,
                "page": page,
            },
        )

        if search_resp.status_code != 200:
            raise HTTPException(status_code=search_resp.status_code, detail="Failed to search repositories")

        data = search_resp.json()
        # GitHub returns { total_count, incomplete_results, items: [...] }
        return data.get("items", [])

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
    """Generate task breakdown for a specification using Azure OpenAI"""
    try:
        spec = spec_by_id.get(spec_id)
        if not spec:
            raise HTTPException(status_code=404, detail="Specification not found")
        
        try:
            client = get_azure_openai_client()
            
            prompt = f"""You are a task breakdown specialist for software development projects based on specifications. 
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
              {{
                "id": "task-1",
                "title": "Task title",
                "description": "Detailed description",
                "estimatedTime": "X-Y hours",
                "estimatedTokens": "X-Y tokens",
                "priority": "high|medium|low",
                "status": "pending"
              }}
            ]

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
            
            response = client.responses.create(
                model=os.getenv("MODEL_NAME", "gpt-5-nano"),
                input=prompt
            )
            
            response_content = response.output_text if hasattr(response, 'output_text') else str(response.output[0].content[0].text)
            
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
                    
        except Exception as e:
            logger.error(f"Azure OpenAI error: {e}")
            return []
            
    except Exception as e:
        logger.error(f"Error in generate_spec_task_breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/specs/{spec_id}/enhance")
async def enhance_spec(spec_id: str):
    """Enhance specification content to be tailored for coding agents using Azure OpenAI"""
    try:
        spec = spec_by_id.get(spec_id)
        if not spec:
            raise HTTPException(status_code=404, detail="Specification not found")
        
        try:
            client = get_azure_openai_client()
            
            prompt = f"""You are a specification enhancement specialist for coding agents. Your task is to take an existing specification and enhance it to be more suitable and actionable for AI coding agents.

            Please enhance the following specification by:
            1. Adding technical implementation details where missing
            2. Breaking down high-level requirements into specific, actionable items
            3. Adding clear acceptance criteria for each feature
            4. Including technical constraints and considerations
            5. Specifying API endpoints, data models, and integration points where relevant
            6. Adding testing requirements and validation criteria
            7. Making the language more precise and technical
            8. Ensuring the specification is comprehensive enough for an AI agent to implement

            **Original Specification:**
            Title: {spec.title}
            Description: {spec.description}
            Content:
            {spec.content}

            Please return an enhanced version of this specification that maintains the original intent but provides much more technical detail and actionable guidance for a coding agent. Format the response in markdown.
            """
            
            try:
                response = client.chat.completions.create(
                    model="gpt-5-nano",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000
                )
                enhanced_content = response.choices[0].message.content
            except Exception as chat_error:
                logger.error(f"Chat completions failed: {chat_error}")
                for model_name in ["gpt-4", "gpt-35-turbo", "gpt-4-turbo"]:
                    try:
                        response = client.chat.completions.create(
                            model=model_name,
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=2000
                        )
                        enhanced_content = response.choices[0].message.content
                        logger.info(f"Successfully used model: {model_name}")
                        break
                    except Exception as model_error:
                        logger.error(f"Model {model_name} failed: {model_error}")
                        continue
                else:
                    raise Exception("No available models found")
            
            return {
                "enhanced_content": enhanced_content,
                "original_content": spec.content,
                "title": spec.title,
                "description": spec.description
            }
                    
        except Exception as e:
            logger.error(f"Azure OpenAI error: {e}")
            enhanced_content = f"""# Enhanced Specification: {spec.title}

{spec.description}


- **Frontend Interface**: React-based user interface with real-time chat capabilities
- **Backend API**: RESTful API service with WebSocket support for real-time communication
- **AI Processing Engine**: Natural language processing and machine learning models
- **Database Layer**: Persistent storage for user sessions, conversation history, and analytics
- **Authentication Service**: Secure user authentication and authorization system

- **Frontend**: React.js, TypeScript, WebSocket client
- **Backend**: Python FastAPI, WebSocket server, async/await patterns
- **AI/ML**: Azure OpenAI, custom NLP models, sentiment analysis
- **Database**: PostgreSQL for structured data, Redis for caching
- **Infrastructure**: Docker containers, Azure Container Apps, Azure Application Gateway

## Detailed Requirements


**Acceptance Criteria:**
- System must analyze incoming tickets using NLP to extract intent, urgency, and category
- Route tickets to appropriate support agents based on expertise and availability
- Achieve 95% accuracy in ticket categorization
- Response time under 30 seconds for initial routing

**Technical Implementation:**
- Implement text classification model using Azure OpenAI
- Create agent skill matrix and availability tracking
- Design priority queue system with SLA-based routing
- Add fallback to human oversight for edge cases

**Acceptance Criteria:**
- Generate contextually appropriate responses for common queries
- Maintain conversation history and context across interactions
- Support multi-turn conversations with state management
- Provide confidence scores for generated responses

**Technical Implementation:**
- Integrate Azure OpenAI GPT models for response generation
- Implement conversation state management with Redis
- Create response templates for common scenarios
- Add human handoff triggers for low-confidence responses

**Acceptance Criteria:**
- Real-time sentiment analysis of customer communications
- Automatic escalation for negative sentiment or frustrated customers
- Sentiment trend tracking and reporting
- Integration with existing CRM systems

**Technical Implementation:**
- Deploy sentiment analysis model with real-time processing
- Create escalation rules engine with configurable thresholds
- Implement webhook integrations for CRM updates
- Add sentiment dashboard with historical analytics


```
POST /api/auth/login
POST /api/auth/logout
GET /api/auth/profile
```

```
POST /api/tickets - Create new support ticket
GET /api/tickets/:id - Retrieve ticket details
PUT /api/tickets/:id - Update ticket status
GET /api/tickets - List tickets with filtering
```

```
POST /api/ai/analyze - Analyze ticket content
POST /api/ai/generate-response - Generate automated response
GET /api/ai/sentiment/:ticketId - Get sentiment analysis
```

```
GET /api/agents - List available agents
PUT /api/agents/:id/status - Update agent availability
GET /api/agents/:id/workload - Get agent current workload
```


```json
{{
  "id": "uuid",
  "customer_id": "uuid",
  "subject": "string",
  "description": "text",
  "category": "enum",
  "priority": "enum",
  "status": "enum",
  "assigned_agent_id": "uuid",
  "sentiment_score": "float",
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "conversation_history": "array"
}}
```

```json
{{
  "id": "uuid",
  "name": "string",
  "email": "string",
  "skills": "array",
  "availability_status": "enum",
  "current_workload": "integer",
  "performance_metrics": "object"
}}
```

### Performance Requirements
- **Response Time**: API responses under 200ms for 95% of requests
- **Throughput**: Support 1000 concurrent users
- **Availability**: 99.9% uptime SLA
- **Scalability**: Auto-scaling based on load metrics

### Security Requirements
- **Authentication**: OAuth 2.0 with JWT tokens
- **Authorization**: Role-based access control (RBAC)
- **Data Encryption**: TLS 1.3 for data in transit, AES-256 for data at rest
- **Audit Logging**: Comprehensive audit trail for all system actions


- Test all API endpoints with comprehensive test cases
- Mock external dependencies (Azure OpenAI, database)
- Achieve 90% code coverage minimum

- End-to-end workflow testing
- Database integration testing
- External API integration testing

- Load testing with simulated user traffic
- Stress testing for peak load scenarios
- Database performance optimization


- Automated testing on pull requests
- Staging environment deployment
- Production deployment with blue-green strategy

- Application performance monitoring (APM)
- Custom metrics for business KPIs
- Alert rules for system health and performance

- Automated database backups
- Disaster recovery procedures
- Data retention policies

- GDPR compliance for customer data
- SOC 2 Type II certification requirements
- Data privacy and protection measures

- **Phase 1** (Weeks 1-2): Core API development and database setup
- **Phase 2** (Weeks 3-4): AI integration and ticket routing
- **Phase 3** (Weeks 5-6): Frontend development and user interface
- **Phase 4** (Weeks 7-8): Testing, optimization, and deployment

- Ticket resolution time reduction by 40%
- Customer satisfaction score improvement to 4.5/5
- Agent productivity increase by 30%
- System uptime of 99.9%

This enhanced specification provides comprehensive technical details and actionable guidance for implementing the AI-powered customer support system using modern software engineering practices and Azure cloud services."""

            return {
                "enhanced_content": enhanced_content,
                "original_content": spec.content,
                "title": spec.title,
                "description": spec.description
            }
            
    except Exception as e:
        logger.error(f"Error in enhance_spec: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/specs/{spec_id}/assign")
async def assign_spec_to_swe_agent(spec_id: str, request: SWEAgentRequest):
    """Assign specification implementation to SWE agent"""
    try:
        spec = spec_by_id.get(spec_id)
        if not spec:
            raise HTTPException(status_code=404, detail="Specification not found")
        
        if request.agent_id == "devin":
            # Build an instruction with spec context and optional task focus
            import re
            def slugify(s: str) -> str:
                return re.sub(r"[^a-zA-Z0-9-]+", "-", s.lower()).strip("-")

            task_block = ""
            repo_hint = ""
            if request.task_details:
                t = request.task_details
                t_title = t.get("title") or "Selected Task"
                t_desc = t.get("description") or ""
                task_block = f"\n\nFocus Task:\n- Title: {t_title}\n- Description: {t_desc}\n"
                spec_slug = slugify(spec.title)
                task_slug = slugify(t_title)
                repo_hint = f"\nCreate a NEW GitHub repository for this task named: {spec_slug}-{task_slug}. Initialize it and push all work there."
            else:
                # One-shot/full spec implementation – still suggest a repo name derived from spec
                spec_slug = slugify(spec.title)
                repo_hint = f"\nCreate a NEW GitHub repository for this specification named: {spec_slug}-implementation. Initialize it and push all work there."

            prompt = f"""
Implement the "{spec.title}" specification.

Context:
- Title: {spec.title}
- Description: {spec.description}

Full Specification Content:
{spec.content}

Customer Customization:
- Customer: {request.customization.company_name}
- Industry: {request.customization.industry}
- Use Case: {request.customization.use_case}
- Scenario: {request.customization.customer_scenario}
- Brand Theme: {request.customization.brand_theme}
- Primary Color: {request.customization.primary_color}
- Additional Requirements: {request.customization.additional_requirements}
- Use MCP Tools: {request.customization.use_mcp_tools}
- Use A2A: {request.customization.use_a2a}

Mode: {request.mode}{task_block}

Instructions:
- {"Leverage MCP tools when helpful." if request.customization.use_mcp_tools else "Use best-practice tools and testing."}
- {"Apply agent-to-agent (A2A) patterns when applicable." if request.customization.use_a2a else "Use clean interfaces and modularity."}
- {repo_hint}
""".strip()

            devin_payload = {
                "prompt": prompt,
                # idempotent lets Devin coalesce retries instead of duplicating work
                "idempotent": True
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
    """Generate task breakdown using Azure OpenAI"""
    print(f"DEBUG: Received request for template_id: {template_id}")
    print(f"DEBUG: Request data: {request}")
    print(f"DEBUG: Request dict: {request.dict()}")
    try:
        template = next((t for t in templates_data if t.id == template_id), None)
        pattern = None
        
        if not template:
            pattern = next((p for p in patterns_data if p["id"] == template_id), None)
            if not pattern:
                raise HTTPException(status_code=404, detail="Template or pattern not found")
        
        try:
            client = get_azure_openai_client()
            
            if template:
                prompt = f"""You are a task breakdown specialist for software development projects. 
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
                  {{
                    "id": "task-1",
                    "title": "Task title",
                    "description": "Detailed description",
                    "estimatedTime": "X-Y hours",
                    "estimatedTokens": "X-Y tokens",
                    "priority": "high|medium|low",
                    "status": "pending"
                  }}
                ]

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
                
                prompt = f"""You are a task breakdown specialist for software development projects. 
                Given an AI agent pattern and implementation requirements, break down the work into specific, actionable tasks.
                
                For each task, provide:
                - A clear, specific title
                - Detailed description of what needs to be done
                - Estimated time to complete
                - Priority level (high, medium, low)
                - Status (always 'pending' for new tasks)
                
                Return your response as a JSON array of task objects with the following structure:
                [
                  {{
                    "id": "task-1",
                    "title": "Task title",
                    "description": "Detailed description",
                    "estimatedTime": "X-Y hours",
                    "estimatedTokens": "X-Y tokens",
                    "priority": "high|medium|low",
                    "status": "pending"
                  }}
                ]

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
            
            response = client.responses.create(
                model=os.getenv("MODEL_NAME", "gpt-5-nano"),
                input=prompt
            )
            
            response_content = response.output_text if hasattr(response, 'output_text') else str(response.output[0].content[0].text)
            
            try:
                import re
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
        
        except Exception as azure_error:
            print(f"Azure OpenAI authentication failed: {azure_error}. Using mock response for local testing.")
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating task breakdown: {str(e)}")

@app.post("/api/templates/{template_id}/assign")
async def assign_to_swe_agent(template_id: str, request: SWEAgentRequest, authorization: Optional[str] = Header(None)):
    """Assign customization task to SWE agent"""
    try:
        logger.debug(f"Looking for template_id: {template_id}")
        logger.debug(f"templates_data type: {type(templates_data)}")
        logger.debug(f"First template type: {type(templates_data[0]) if templates_data else 'No templates'}")
        template = next((t for t in templates_data if t.id == template_id), None)
        logger.debug(f"Found template: {template}")
        pattern = None
        if not template:
            pattern = next((p for p in patterns_data if p["id"] == template_id), None)
            logger.debug(f"Found pattern: {pattern}")
            if not pattern:
                raise HTTPException(status_code=404, detail="Template or pattern not found")
        
        if request.agent_id == "devin":
            # Use template or pattern data
            item = template if template else pattern
            item_type = "template" if template else "pattern"
            
            # Require GitHub auth to fork/copy the template repository into user's account
            if not authorization or not authorization.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="GitHub authentication required to deploy to your repository")

            gh_token = authorization.split(" ")[1]

            # Extract owner/repo from the source template URL
            repo_url = getattr(item, 'github_url', item.get('github_url', '') if isinstance(item, dict) else '')
            match = re.search(r'github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$', repo_url)
            if not match:
                raise HTTPException(status_code=400, detail=f"Could not extract owner/repo from URL: {repo_url}")
            src_owner, src_repo = match.groups()

            # Derive target repo name based on title + company
            title = getattr(item, 'title', item.get('title', 'template') if isinstance(item, dict) else 'template')
            safe_name = re.sub(r'[^a-zA-Z0-9-]', '-', title.lower())
            company = request.customization.company_name or "customer"
            company_safe = re.sub(r'[^a-zA-Z0-9-]', '-', company.lower()).strip('-') or 'customer'
            target_repo = f"{safe_name}-{company_safe}"

            async with httpx.AsyncClient() as client:
                # Identify the authenticated user
                user_resp = await client.get(
                    "https://api.github.com/user",
                    headers={"Authorization": f"token {gh_token}"}
                )
                if user_resp.status_code != 200:
                    raise HTTPException(status_code=user_resp.status_code, detail="Failed to identify GitHub user")
                user_login = user_resp.json().get("login")

                # Fork the repo into user's account (optionally using a new name)
                fork_resp = await client.post(
                    f"https://api.github.com/repos/{src_owner}/{src_repo}/forks",
                    headers={
                        "Authorization": f"token {gh_token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                    json={"name": target_repo}
                )
                if fork_resp.status_code not in (201, 202):
                    raise HTTPException(status_code=fork_resp.status_code, detail=f"Failed to fork repository: {fork_resp.text}")

            # Wait briefly for fork to be ready, then create agents.md using PyGithub service
            from .github_service import GitHubService
            import asyncio
            await asyncio.sleep(2)

            github_service = GitHubService(github_token=gh_token)
            agents_content = github_service.generate_agents_md_content(
                content_type=item_type,
                item=item.__dict__ if hasattr(item, '__dict__') else item,
                customization=request.customization.__dict__
            )
            file_result = github_service.create_file(
                repo_name=f"{user_login}/{target_repo}",
                file_path="agents.md",
                content=agents_content,
                commit_message="Add agents.md with customization details"
            )
            if not file_result.get("success"):
                # Don't fail the whole flow; include warning but proceed to Devin
                logger.warning(f"Failed to create agents.md: {file_result.get('error')}")

            # Prepare Devin session prompt
            fork_repo_url = f"https://github.com/{user_login}/{target_repo}"
            prompt = f"""
You are Devin. Implement the following customization for the {title} {item_type}.

Customer: {request.customization.company_name}
Industry: {request.customization.industry}
Use Case: {request.customization.use_case}
Brand Theme: {request.customization.brand_theme}
Primary Color: {request.customization.primary_color}

Scenario:
{request.customization.customer_scenario}

Additional Requirements:
{request.customization.additional_requirements}

Repository to work in (forked from template):
{fork_repo_url}

Tasks:
- Review repository and agents.md for context.
- Apply customizations and open a pull request.
- Document changes in the PR description.
""".strip()

            devin_payload = {"prompt": prompt, "idempotent": True}
            headers = {"Authorization": f"Bearer {request.api_key}", "Content-Type": "application/json"}

            async with httpx.AsyncClient() as client:
                devin_api_url = os.getenv("DEVIN_API_BASE_URL", "https://api.devin.ai")
                try:
                    response = await client.post(
                        f"{devin_api_url}/v1/sessions",
                        json=devin_payload,
                        headers=headers,
                        timeout=30.0,
                    )
                    
                    if response.status_code == 200:
                        devin_response = response.json()
                        
                        result = {
                            "status": "success",
                            "agent": "devin",
                            "session_id": devin_response.get("session_id"),
                            "session_url": devin_response.get("session_url"),
                            "session_status": devin_response.get("status", "created"),
                            "repository_url": fork_repo_url,
                            "message": "Forked template, created agents.md, and started Devin session"
                        }
                        
                        try:
                            async with httpx.AsyncClient() as client:
                                user_resp = await client.get(
                                    "https://api.github.com/user",
                                    headers={"Authorization": f"token {gh_token}"}
                                )
                                if user_resp.status_code == 200:
                                    user_data = user_resp.json()
                                    await cosmos_service.store_agent_assignment(
                                        user_id=str(user_data["id"]),
                                        user_login=user_data["login"],
                                        template_id=template_id,
                                        template_title=getattr(item, 'title', item.get('title', 'Unknown Template') if isinstance(item, dict) else 'Unknown Template'),
                                        agent_id="devin",
                                        customization=request.customization.model_dump(),
                                        assignment_response=result
                                    )
                                else:
                                    logger.warning(f"Failed to get user info for assignment storage: {user_resp.status_code}")
                        except Exception as e:
                            logger.error(f"Failed to store Devin assignment: {e}")
                        
                        return result
                    elif response.status_code == 401:
                        raise HTTPException(status_code=401, detail="Invalid Devin API key. Please check your credentials.")
                    elif response.status_code == 429:
                        raise HTTPException(status_code=429, detail="Devin API rate limit exceeded. Please try again later.")
                    else:
                        logger.error(f"Devin API error: {response.status_code} - {response.text}")
                        raise HTTPException(status_code=response.status_code, detail=f"Devin API error: {response.text}")
                except httpx.TimeoutException:
                    raise HTTPException(status_code=504, detail="Devin API request timed out. Please try again.")
                except httpx.RequestError as e:
                    logger.error(f"Devin API request failed: {e}")
                    raise HTTPException(status_code=503, detail="Failed to connect to Devin API. Please try again later.")
                    
        elif request.agent_id == "github-copilot":
            from .github_service import GitHubService
            
            try:
                # Use template or pattern data
                item = template if template else pattern
                item_type = "template" if template else "pattern"
                
                if not item:
                    raise HTTPException(status_code=404, detail="Template or pattern not found")
                
                # Extract repository information from github_url
                repo_url = getattr(item, 'github_url', item.get('github_url', '') if isinstance(item, dict) else '')
                if not repo_url:
                    raise HTTPException(status_code=400, detail="No GitHub URL found for this template")
                
                match = re.search(r'github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$', repo_url)
                if not match:
                    raise HTTPException(status_code=400, detail=f"Could not extract owner/repo from URL: {repo_url}")
                
                template_owner, template_repo = match.groups()
                
                if not authorization or not authorization.startswith("Bearer "):
                    raise HTTPException(status_code=401, detail="GitHub authentication required")
                
                gh_token = authorization.split(" ")[1]
                
                # Fork the repository to user's account
                github_service = GitHubService(github_token=gh_token)
                
                if github_service.mock_mode:
                    logger.warning("GitHub token not provided, using mock mode")
                    return {
                        "status": "error",
                        "agent": "github-copilot",
                        "message": "GitHub token is required for GitHub Copilot integration. Please provide a valid GitHub Personal Access Token."
                    }
                
                user = github_service.github.get_user()
                
                try:
                    source_repo = github_service.github.get_repo(f"{template_owner}/{template_repo}")
                    
                    try:
                        forked_repo = user.create_fork(source_repo)
                        logger.info(f"Successfully forked {template_owner}/{template_repo} to {forked_repo.full_name}")
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            # Repository already forked, get existing fork
                            forked_repo = github_service.github.get_repo(f"{user.login}/{template_repo}")
                            logger.info(f"Using existing fork: {forked_repo.full_name}")
                        else:
                            raise e
                            
                except Exception as e:
                    if "saml enforcement" in str(e).lower() or "403" in str(e):
                        logger.info(f"Repository access blocked by SAML enforcement, copying repository content instead")
                        copy_result = github_service.copy_repository_content(
                            source_owner=template_owner,
                            source_repo=template_repo,
                            target_repo_name=template_repo,
                            description=f"Copy of {template_owner}/{template_repo} for customization"
                        )
                        if not copy_result["success"]:
                            raise Exception(f"Failed to copy repository: {copy_result['error']}")
                        
                        forked_repo = github_service.github.get_repo(copy_result["repo_name"])
                        logger.info(f"Successfully copied repository to {forked_repo.full_name}")
                    else:
                        raise e
                
                template_title = getattr(item, 'title', item.get('title', 'Unknown Template') if isinstance(item, dict) else 'Unknown Template')
                issue_content = await generate_github_issue_content(template_title, request.customization)
                
                issue_title = f"Customize {template_title} for {request.customization.company_name}"
                issue = forked_repo.create_issue(
                    title=issue_title,
                    body=issue_content,
                    labels=["enhancement", "customization"]
                )
                
                try:
                    copilot_user = github_service.github.get_user("copilot")
                    issue.add_to_assignees(copilot_user)
                    logger.info(f"Successfully assigned issue #{issue.number} to copilot")
                except Exception as e:
                    logger.warning(f"Could not assign issue to copilot user: {e}")
                
                result = {
                    "status": "success",
                    "agent": "github-copilot",
                    "message": f"Successfully forked repository and created issue #{issue.number} for GitHub Copilot. Make sure GitHub Copilot Coding Agent is enabled in your organization.",
                    "repository_url": forked_repo.html_url,
                    "issue_url": issue.html_url,
                    "issue_number": issue.number,
                    "setup_instructions": "https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-organization/add-copilot-coding-agent"
                }
                
                try:
                    await cosmos_service.store_agent_assignment(
                        user_id=str(user.id),
                        user_login=user.login,
                        template_id=template_id,
                        template_title=template_title,
                        agent_id="github-copilot",
                        customization=request.customization.model_dump(),
                        assignment_response=result
                    )
                except Exception as e:
                    logger.error(f"Failed to store GitHub Copilot assignment: {e}")
                
                return result
                
            except Exception as e:
                logger.error(f"GitHub Copilot assignment error: {e}")
                return {
                    "status": "error",
                    "agent": "github-copilot",
                    "message": f"Failed to assign task to GitHub Copilot: {str(e)}. Please ensure you have a valid GitHub token and the repository exists."
                }
            
        elif request.agent_id == "replit":
            return {
                "status": "success",
                "agent": "replit",
                "message": "Task assigned to Replit Agent (placeholder implementation)"
            }
            
        elif request.agent_id == "codex-cli":
            from .github_service import GitHubService
            
            try:
                item = template if template else pattern
                item_type = "template" if template else "pattern"
                
                if not item:
                    spec = next((s for s in specs_data if s["id"] == template_id), None)
                    if spec:
                        item = spec
                        item_type = "spec"
                    else:
                        raise HTTPException(status_code=404, detail="Template, pattern, or spec not found")
                
                if not item:
                    raise HTTPException(status_code=404, detail="No item found for processing")
                
                github_service = GitHubService()
                
                title = getattr(item, 'title', item.get('title', 'Unknown Item') if isinstance(item, dict) else 'Unknown Item')
                
                safe_name = re.sub(r'[^a-zA-Z0-9-]', '-', title.lower())
                repo_name = f"{safe_name}-{request.customization.company_name.lower().replace(' ', '-')}"
                
                repo_result = github_service.create_repository(
                    repo_name=repo_name,
                    description=f"Azure OpenAI Codex implementation for {title}",
                    private=False
                )
                
                if not repo_result["success"]:
                    raise Exception(f"Failed to create repository: {repo_result['error']}")
                
                agents_content = github_service.generate_agents_md_content(
                    content_type=item_type,
                    item=item.__dict__ if hasattr(item, '__dict__') else item,
                    customization=request.customization.__dict__
                )
                
                file_result = github_service.create_file(
                    repo_name=repo_result["repo_name"],
                    file_path="agents.md",
                    content=agents_content,
                    commit_message="Add agents.md with project specification"
                )
                
                if not file_result["success"]:
                    logger.warning(f"Failed to create agents.md: {file_result['error']}")
                
                workflow_content = github_service.generate_github_actions_workflow(
                    agent_type="codex-cli",
                    azure_config={"endpoint": request.endpoint, "api_key": "***"}
                )
                
                workflow_result = github_service.create_file(
                    repo_name=repo_result["repo_name"],
                    file_path=".github/workflows/codex-automation.yml",
                    content=workflow_content,
                    commit_message="Add GitHub Actions workflow for Azure OpenAI Codex automation"
                )
                
                if not workflow_result["success"]:
                    logger.warning(f"Failed to create workflow: {workflow_result['error']}")
                
                secrets_to_create = {
                    "AZURE_OPENAI_API_KEY": request.api_key,
                    "AZURE_OPENAI_ENDPOINT": request.endpoint
                }
                
                secrets_result = github_service.create_repository_secrets(
                    repo_name=repo_result["repo_name"],
                    secrets=secrets_to_create
                )
                
                if not secrets_result["success"]:
                    logger.warning(f"Failed to create repository secrets: {secrets_result.get('error', 'Unknown error')}")
                
                result = {
                    "status": "success",
                    "agent": "codex-cli",
                    "message": f"Repository created successfully with Azure OpenAI Codex automation setup. GitHub secrets configured automatically.",
                    "repository_url": repo_result["repo_url"],
                    "repository_name": repo_result["repo_name"],
                    "secrets_created": secrets_result.get("secrets_created", []) if secrets_result["success"] else []
                }
                
                try:
                    if github_service.github and not github_service.mock_mode:
                        user = github_service.github.get_user()
                        await cosmos_service.store_agent_assignment(
                            user_id=str(user.id),
                            user_login=user.login,
                            template_id=template_id,
                            template_title=title,
                            agent_id="codex-cli",
                            customization=request.customization.model_dump(),
                            assignment_response=result
                        )
                except Exception as e:
                    logger.error(f"Failed to store Codex assignment: {e}")
                
                return result
                
            except Exception as e:
                logger.error(f"Codex-cli assignment error: {e}")
                return {
                    "status": "error",
                    "agent": "codex-cli",
                    "message": f"Failed to create repository and setup Codex automation: {str(e)}"
                }
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported agent: {request.agent_id}")
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error assigning to SWE agent: {str(e)}")

@app.post("/api/templates/{template_id}/deploy")
async def deploy_template_to_github(template_id: str, request: dict):
    """Deploy template to user's GitHub repository with agent configuration"""
    try:
        template = next((t for t in templates_data if t["id"] == template_id), None)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        access_token = request.get("access_token")
        target_repo = request.get("target_repo")
        agent_config = request.get("agent_config", {})
        
        if not access_token or not target_repo:
            raise HTTPException(status_code=400, detail="Missing access_token or target_repo")
        
        import re
        match = re.search(r'github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$', template["github_url"])
        if not match:
            raise HTTPException(status_code=400, detail="Invalid template GitHub URL")
        
        template_owner, template_repo = match.groups()
        
        async with httpx.AsyncClient() as client:
            fork_response = await client.post(
                f"https://api.github.com/repos/{template_owner}/{template_repo}/forks",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                json={"name": target_repo}
            )
            
            if fork_response.status_code not in [202, 201]:
                raise HTTPException(status_code=fork_response.status_code, detail=f"Failed to fork repository: {fork_response.text}")
            
            fork_data = fork_response.json()
            
            user_response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {access_token}"}
            )
            user_data = user_response.json()
            user_login = user_data["login"]
            
            import asyncio
            await asyncio.sleep(2)
            
            from datetime import datetime
            agent_config_content = {
                "template_id": template_id,
                "template_name": template["title"],
                "agent_config": agent_config,
                "deployment_date": datetime.now().isoformat(),
                "source_repo": template["github_url"]
            }
            
            import base64
            import json
            config_response = await client.put(
                f"https://api.github.com/repos/{user_login}/{target_repo}/contents/aifoundry-agents.json",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                json={
                    "message": "Add AIfoundry agent configuration",
                    "content": base64.b64encode(
                        json.dumps(agent_config_content, indent=2).encode()
                    ).decode()
                }
            )
            
            workflow_content = f"""name: AIfoundry Agent Workflow

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  agent-execution:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Agent Environment
      run: |
        echo "Setting up agent environment for {template['title']}"
        echo "Agent config: {agent_config.get('agent_type', 'default')}"
    
    - name: Execute Agent Tasks
      run: |
        echo "Executing agent tasks..."
        
    - name: Report Results
      run: |
        echo "Agent execution completed"
"""
            
            workflow_response = await client.put(
                f"https://api.github.com/repos/{user_login}/{target_repo}/contents/.github/workflows/aifoundry-agent.yml",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                json={
                    "message": "Add AIfoundry agent workflow",
                    "content": base64.b64encode(workflow_content.encode()).decode()
                }
            )
            
            return {
                "status": "success",
                "message": f"Successfully deployed {template['title']} to {user_login}/{target_repo}",
                "repository": {
                    "name": target_repo,
                    "full_name": f"{user_login}/{target_repo}",
                    "url": fork_data["html_url"]
                },
                "agent_config": agent_config_content
            }
            
    except Exception as e:
        logger.error(f"Error deploying template to GitHub: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/assignments")
async def get_user_assignments(authorization: str = Header(...)):
    """Get user's agent assignments for dashboard"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ")[1]

    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}"}
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=user_response.status_code, detail="Failed to get user information")
        
        user_data = user_response.json()
        user_id = str(user_data["id"])
    
    try:
        assignments = await cosmos_service.get_user_assignments(user_id)
        return [assignment.model_dump() for assignment in assignments]
    except Exception as e:
        logger.error(f"Failed to get user assignments: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve assignments")

@app.get("/api/user/assignments/{assignment_id}")
async def get_assignment_details(assignment_id: str, authorization: str = Header(...)):
    """Get detailed assignment information including markdown context"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ")[1]

    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}"}
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=user_response.status_code, detail="Failed to get user information")
        
        user_data = user_response.json()
        user_id = str(user_data["id"])
    
    try:
        assignments = await cosmos_service.get_user_assignments(user_id)
        assignment = next((a for a in assignments if a.id == assignment_id), None)
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        return assignment.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get assignment details: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve assignment details")

@app.get("/api/sessions/{session_id}/status")
async def get_session_status(session_id: str, authorization: str = Header(...)):
    """Get Devin session status"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    api_key = authorization.split(" ")[1] if len(authorization.split(" ")) > 1 else os.getenv("DEVIN_API_KEY")
    
    if not api_key:
        raise HTTPException(status_code=401, detail="Devin API key required")
    
    try:
        async with httpx.AsyncClient() as client:
            devin_api_url = os.getenv("DEVIN_API_BASE_URL", "https://api.devin.ai")
            response = await client.get(
                f"{devin_api_url}/v1/sessions/{session_id}",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30.0,
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=f"Devin API error: {response.text}")
    except Exception as e:
        logger.error(f"Failed to get session status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session status")
