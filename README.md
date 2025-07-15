# AIfoundry.app

> **⚠️ Experimental - Work in Progress**  
> This is an experimental platform currently under active development. You can test the latest version at [aifoundry.app](https://aifoundry.app)

An agentic pplication that empowers solution engineers to customize multi-agent patterns and leverage the Azure AI Foundry Agent Service Catalog of Agent templates using SWE (Software Engineering) Agents.

## Overview

AIfoundry.app provides a comprehensive platform for solution engineers to:
- Browse and customize multi-agent patterns from the Azure AI Foundry Agent Service Catalog
- Leverage various AI agents and tools for code generation and automation
- Deploy and test agent templates in integrated development environments
- Collaborate on agent-driven software engineering solutions

## Core Technologies & Integrations

### AI Agents & Tools
- **GitHub Copilot Agent**: Integrated via MCP (Model Context Protocol) for intelligent code suggestions
- **Azure AI Foundry Model**: Powered by Codex for advanced code generation and analysis
- **Cognition Devin**: Deployed via MCP on Azure Marketplace for autonomous software engineering
- **Replit Integration**: Available through Azure Marketplace for cloud-based development

### Development Infrastructure
- **GitHub Actions Runner**: Automated CI/CD pipelines and testing
- **MCP (Model Context Protocol)**: Seamless integration between different AI agents
- **Azure Marketplace**: Deployment and distribution platform for agent services

## Features

- **Agent Template Gallery**: Browse and discover pre-built agent templates from Azure AI Foundry
- **Multi-Agent Pattern Customization**: Tailor agent behaviors and workflows to specific use cases
- **Integrated Development Environment**: Test and iterate on agent solutions in real-time
- **SWE Agent Integration**: Leverage Software Engineering Agents for automated code generation
- **Modern UI/UX**: Clean, intuitive interface inspired by Azure AI Labs design language

## Architecture

- **Backend**: FastAPI with Python, integrated with Azure AI Foundry services
- **Frontend**: Vite + React + TypeScript + Tailwind CSS
- **Agent Layer**: MCP-based integration with multiple AI agents (Copilot, Devin, Codex)
- **Deployment**: Azure Container Apps with marketplace integrations
- **Development Tools**: GitHub Actions, Replit, and Azure AI Foundry toolchain

## Development

### Prerequisites
- Azure AI Foundry access
- GitHub Copilot subscription
- Azure Marketplace account for agent services

### Backend Setup
```bash
cd src/backend
poetry install
poetry run fastapi dev app/main.py
```

### Frontend Setup
```bash
cd src/frontend
npm install
npm run dev
```

## Deployment

### Quick Start

For detailed deployment instructions, testing, and troubleshooting, see the [`deployment/` directory](./deployment/README.md).

### Local Development with Docker

Build and run both services using docker-compose:

```bash
# From the deployment directory
cd deployment
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build

# Stop services
docker-compose down
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Backend Health Check: http://localhost:8000/healthz

### Azure Container Apps Deployment

#### Option 1: Azure Developer CLI (Recommended)
```bash
# From project root
azd init
azd up
```

#### Option 2: Manual Deployment
```bash
# From deployment directory
cd deployment

# Linux/macOS
chmod +x deploy.sh
./deploy.sh

# Windows
./deploy.ps1
```

### Testing Your Deployment

After deployment, test your application:

```bash
# From deployment directory
cd deployment

# Linux/macOS
chmod +x test-deployment.sh
./test-deployment.sh <backend-url> <frontend-url>

# Windows
./test-deployment.ps1 <backend-url> <frontend-url>
```

## Project Structure

```
.
├── src/
│   ├── backend/           # FastAPI backend with AI agent integrations
│   └── frontend/          # React frontend for agent template management
├── deployment/            # Deployment scripts and configs
│   ├── README.md         # Detailed deployment guide
│   ├── docker-compose.yml
│   ├── deploy.sh         # Bash deployment script
│   ├── deploy.ps1        # PowerShell deployment script
│   └── test-deployment.* # Testing scripts
├── infra/                # Azure infrastructure templates
└── azure.yaml           # Azure Developer CLI config
```

## Getting Started

1. **Explore Templates**: Visit [aifoundry.app](https://aifoundry.app) to browse available agent templates
2. **Choose Your Agent**: Select from GitHub Copilot, Devin, or Azure AI Foundry models
3. **Customize Patterns**: Modify multi-agent workflows to fit your specific requirements
4. **Deploy & Test**: Use integrated development environments to test your solutions
5. **Collaborate**: Share and iterate on agent-driven software engineering solutions

## Contributing

This project is in active development. Contributions, feedback, and suggestions are welcome as we build the future of agent-driven software engineering.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**🚀 Live Demo**: [aifoundry.app](https://aifoundry.app)  
**🔗 Devin Session**: https://app.devin.ai/sessions/73bc742bdcf84ca7adb544e44eaf542f  
**👤 Requested by**: @thegovind
