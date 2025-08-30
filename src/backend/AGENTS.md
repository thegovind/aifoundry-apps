# AIFoundry Apps - Backend API

FastAPI-based backend service providing REST APIs for AI agent template management, multi-agent pattern orchestration, and SWE agent integration.

## Service Overview

- **Framework**: FastAPI with Python 3.11+
- **Package Management**: UV for fast dependency resolution and virtual environments
- **Database**: PostgreSQL with async support via psycopg
- **Authentication**: GitHub OAuth with JWT token management
- **AI Integration**: Azure AI Foundry, GitHub Copilot, and MCP servers

## Core Functionality

### Template & Pattern Management
- **Template Catalog**: Browse and filter AI agent templates from Azure AI Foundry
- **Pattern Library**: Multi-agent workflow patterns (routing, chaining, parallelization)
- **Customization Engine**: Dynamic template customization based on user requirements
- **Task Breakdown**: AI-powered task decomposition for complex implementations

### SWE Agent Integration
- **Agent Orchestration**: Support for Devin, GitHub Copilot, and Azure OpenAI Codex
- **Repository Management**: Automated GitHub repository creation and management
- **Workflow Automation**: GitHub Actions workflow generation for agent tasks
- **MCP Integration**: Model Context Protocol for seamless agent communication

### GitHub Services
- **OAuth Authentication**: Secure GitHub user authentication and authorization
- **Repository Operations**: Create, clone, and manage GitHub repositories
- **File Management**: Automated creation of agents.md specifications and workflows
- **API Integration**: GitHub REST API and GraphQL integration

## Technical Stack

### Core Dependencies
- **FastAPI**: ^0.115.14 - Modern async web framework
- **Pydantic**: ^2.11.7 - Data validation and serialization
- **psycopg[binary]**: ^3.2.9 - PostgreSQL async database adapter
- **PyGithub**: ^2.1.1 - GitHub API client library
- **PyJWT**: ^2.10.1 - JSON Web Token implementation

### AI & Integration
- **azure-ai-projects**: ^1.0.0b5 - Azure AI Foundry integration
- **azure-core**: ^1.30.0 - Azure SDK core functionality
- **mcp**: ^1.11.0 - Model Context Protocol implementation
- **httpx**: ^0.27.2 - Async HTTP client for external APIs

### Utilities
- **beautifulsoup4**: ^4.12.3 - HTML parsing and web scraping
- **lxml**: ^5.2.2 - XML/HTML processing
- **python-dotenv**: ^1.0.0 - Environment variable management

## API Architecture

### Authentication Endpoints
- **POST /auth/github/login**: Initiate GitHub OAuth flow
- **GET /auth/github/callback**: Handle OAuth callback and token exchange
- **GET /auth/user/repositories**: List user's GitHub repositories

### Template Management
- **GET /templates**: List available agent templates with filtering
- **GET /templates/{id}**: Get specific template details
- **POST /templates/{id}/breakdown**: Generate task breakdown for template
- **POST /templates/{id}/assign**: Assign template to SWE agent

### Pattern & Spec Management
- **GET /patterns**: List multi-agent patterns
- **GET /specs**: List custom specifications
- **POST /specs**: Create new specification
- **PUT /specs/{id}**: Update existing specification

### Agent Operations
- **POST /assign-to-swe-agent**: Assign tasks to specific SWE agents
- **POST /deploy-template-to-github**: Deploy template to GitHub repository

## Service Integrations

### Azure AI Foundry
- **Template Catalog**: Access to pre-built agent templates
- **AI Models**: Integration with Azure OpenAI and other AI services
- **Project Management**: Azure AI project creation and management

### GitHub Integration
- **OAuth Flow**: Secure user authentication via GitHub
- **Repository Management**: Automated repo creation with agents.md files
- **Actions Workflows**: Dynamic GitHub Actions workflow generation
- **API Access**: Full GitHub REST API integration via PyGithub

### MCP Servers
- **GitHub Copilot**: Code generation and suggestions via MCP
- **Agent Communication**: Standardized protocol for agent interactions
- **Tool Integration**: Access to various development tools and services

## Configuration

### Environment Variables
- **GITHUB_CLIENT_ID**: GitHub OAuth application client ID
- **GITHUB_CLIENT_SECRET**: GitHub OAuth application secret
- **GITHUB_TOKEN**: GitHub personal access token for API operations
- **AZURE_AI_***: Azure AI Foundry service credentials
- **DATABASE_URL**: PostgreSQL connection string

### Security Configuration
- **JWT_SECRET_KEY**: Secret key for JWT token signing
- **CORS_ORIGINS**: Allowed origins for cross-origin requests
- **API_RATE_LIMITS**: Rate limiting configuration for API endpoints

## Data Models

### Core Models
- **Template**: Agent template with metadata and configuration
- **Pattern**: Multi-agent workflow pattern definition
- **Spec**: Custom specification with markdown content
- **CustomizationRequest**: User customization parameters

### Request/Response Models
- **SWEAgentRequest**: Agent assignment request with credentials
- **TaskBreakdownResponse**: AI-generated task decomposition
- **FilterOptions**: Template filtering and search parameters

## Development Setup

### Local Development
```bash
cd src/backend
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv sync
uv run fastapi dev app/main.py --port 8000 --host 0.0.0.0
```

### Database Setup
```bash
# PostgreSQL setup required
export DATABASE_URL="postgresql://user:pass@localhost/aifoundry"
```

### Testing
```bash
uv run pytest                    # Run test suite
uv run fastapi dev --reload      # Development with auto-reload
```

## Deployment

### Production Configuration
- **Azure Container Apps**: Containerized deployment
- **Environment Variables**: Secure credential management
- **Health Checks**: `/healthz` endpoint for monitoring
- **Logging**: Structured logging with Azure Application Insights

### CI/CD Pipeline
- **GitHub Actions**: Automated testing and deployment
- **Docker**: Multi-stage builds for optimized containers
- **Azure DevOps**: Infrastructure as code deployment

## Security & Compliance

- **OAuth 2.0**: Secure GitHub authentication flow
- **JWT Tokens**: Stateless authentication with secure token management
- **CORS**: Properly configured cross-origin resource sharing
- **Input Validation**: Pydantic models for request/response validation
- **Rate Limiting**: API endpoint protection against abuse
- **Secret Management**: Environment-based credential storage

## Monitoring & Observability

- **Health Checks**: Application health monitoring
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Error Tracking**: Comprehensive error handling and reporting
- **Performance Metrics**: API response time and throughput monitoring