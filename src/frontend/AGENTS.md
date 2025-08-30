# AIFoundry Apps - Frontend Application

React-based frontend application for the AIFoundry Apps platform, providing an intuitive interface for managing AI agent templates and multi-agent patterns.

## Application Overview

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite for fast development and optimized builds
- **Styling**: Tailwind CSS with custom design system
- **UI Components**: Radix UI primitives with custom styling
- **State Management**: React hooks and context API
- **Routing**: React Router DOM v7

## Key Features

### Agent Template Management
- **Template Gallery**: Browse and filter AI agent templates from Azure AI Foundry catalog
- **Template Customization**: Interactive forms for customizing agent behaviors and configurations
- **Pattern Workbench**: Visual interface for designing multi-agent workflows
- **Spec Editor**: Markdown-based specification editor with live preview

### SWE Agent Integration
- **Agent Selection**: Choose between GitHub Copilot, Devin, and Azure OpenAI Codex agents
- **Task Assignment**: Assign templates and patterns to specific SWE agents
- **Workflow Management**: Support for both breakdown and one-shot implementation modes
- **Authentication**: GitHub OAuth integration for agent access

### User Interface
- **Modern Design**: Clean, professional interface inspired by Azure AI Labs
- **Responsive Layout**: Mobile-first design with desktop optimization
- **Interactive Components**: Rich form controls, modals, and navigation
- **Real-time Updates**: Live feedback and status updates during agent operations

## Technical Stack

### Core Dependencies
- **React**: ^18.3.1 - Component framework
- **TypeScript**: ~5.6.2 - Type safety and developer experience
- **Vite**: ^6.0.1 - Build tool and development server
- **React Router DOM**: ^7.6.3 - Client-side routing

### UI Framework
- **Tailwind CSS**: ^3.4.16 - Utility-first CSS framework
- **Radix UI**: Complete set of accessible UI primitives
- **Lucide React**: ^0.364.0 - Icon library
- **Class Variance Authority**: ^0.7.1 - Component variant management

### Specialized Components
- **Mermaid**: ^11.8.1 - Diagram rendering for workflow visualization
- **React MD Editor**: ^4.0.8 - Markdown editing with preview
- **React Hook Form**: ^7.60.0 - Form state management and validation
- **Recharts**: ^2.12.4 - Data visualization and analytics

### Development Tools
- **ESLint**: ^9.15.0 - Code linting and quality
- **TypeScript ESLint**: ^8.15.0 - TypeScript-specific linting rules
- **Autoprefixer**: ^10.4.20 - CSS vendor prefixing

## Component Architecture

### Core Components
- **TemplateWorkbench**: Main interface for template customization
- **PatternWorkbench**: Multi-agent pattern design interface  
- **SpecWorkbench**: Specification editing and management
- **SWEAgentSelection**: Agent selection and configuration interface

### UI Components
- **Custom Button, Card, Dialog**: Styled Radix UI primitives
- **Form Controls**: Input, Select, Checkbox, Radio components
- **Layout Components**: Navigation, Sidebar, Content areas
- **Data Display**: Tables, Charts, Progress indicators

## Configuration

### Environment Variables
- **VITE_API_BASE_URL**: Backend API endpoint
- **VITE_GITHUB_CLIENT_ID**: GitHub OAuth client ID
- **VITE_AZURE_MAPS_KEY**: Azure Maps integration key

### Build Configuration
- **TypeScript**: Strict mode enabled with path mapping
- **Vite**: Optimized for React with TypeScript support
- **Tailwind**: Custom design tokens and component classes
- **ESLint**: React hooks and TypeScript rules enabled

## Development Workflow

### Local Development
```bash
cd src/frontend
pnpm install
pnpm run dev
```

### Build Process
```bash
pnpm run build    # TypeScript compilation + Vite build
pnpm run preview  # Preview production build
pnpm run lint     # Code quality checks
```

### Integration Points
- **Backend API**: RESTful API communication with FastAPI backend
- **GitHub OAuth**: User authentication and repository access
- **Azure Services**: Maps integration and AI service connectivity
- **MCP Servers**: Model Context Protocol for agent communication

## Deployment

- **Development**: Vite dev server on localhost:5173
- **Production**: Static build deployed to Azure Container Apps
- **CDN**: Optimized assets with Azure CDN integration
- **Monitoring**: Application insights and error tracking

## Authentication & Security

- **GitHub OAuth**: Secure user authentication flow
- **Token Management**: Secure storage and refresh of access tokens
- **API Security**: CORS configuration and request validation
- **Environment Isolation**: Separate configs for dev/staging/production