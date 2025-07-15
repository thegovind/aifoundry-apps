# SE Agent Factory - Deployment Guide

## Overview
This guide covers testing and deploying the SE Agent Factory application to Azure Container Apps.

## Prerequisites

### Required Tools
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- [Azure Developer CLI (azd)](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd)
- [Docker](https://docs.docker.com/get-docker/)
- [Node.js 18+](https://nodejs.org/)
- [Python 3.12+](https://www.python.org/)

### Azure Subscription
- Active Azure subscription with Container Apps enabled
- Sufficient permissions to create resources

## Dockerfile Validation Summary

### ✅ Frontend Dockerfile
- **Multi-stage build** for optimal image size
- **Node.js 18 Alpine** for security and efficiency
- **Nginx** for production serving
- **Health checks** with wget
- **Security headers** configured

### ✅ Backend Dockerfile
- **Python 3.12 slim** for optimal performance
- **Poetry** for dependency management
- **Health checks** with curl
- **Proper port exposure** (8000)

## Local Testing

### 1. Test Individual Services

#### Backend Testing
```bash
cd ../src/backend
docker build -t se-agent-factory-backend .
docker run -p 8000:8000 se-agent-factory-backend

# Test endpoints
curl http://localhost:8000/healthz
curl http://localhost:8000/api/templates
```

#### Frontend Testing
```bash
cd ../src/frontend
docker build -t se-agent-factory-frontend .
docker run -p 3000:80 se-agent-factory-frontend

# Test in browser
open http://localhost:3000
```

### 2. Full Stack Testing with Docker Compose

```bash
# From deployment directory
docker-compose up --build

# Test full application
open http://localhost:3000
```

## Azure Container Apps Deployment

### Method 1: Azure Developer CLI (Recommended)

```bash
# From project root (not deployment directory)
azd init
azd up

# Follow prompts to select subscription and region
```

### Method 2: Manual Deployment

#### Using Bash (Linux/macOS)
```bash
# From deployment directory
chmod +x deploy.sh
./deploy.sh
```

#### Using PowerShell (Windows)
```powershell
# From deployment directory
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
./deploy.ps1
```

## Testing Your Deployment

After deployment, test your application:

```bash
# Linux/macOS
chmod +x test-deployment.sh
./test-deployment.sh <backend-url> <frontend-url>

# Windows
./test-deployment.ps1 <backend-url> <frontend-url>
```

## Monitoring and Troubleshooting

### Health Check Endpoints
- Backend: `https://your-backend-url/healthz`
- Frontend: `https://your-frontend-url/` (returns 200 for healthy)

### Common Issues and Solutions

#### 1. Build Failures
- **Problem**: Docker build fails
- **Solution**: Check Docker daemon is running and you have sufficient disk space

#### 2. Health Check Failures
- **Problem**: Container apps fail health checks
- **Solution**: Verify endpoints are responding within timeout period

#### 3. CORS Issues
- **Problem**: Frontend cannot connect to backend
- **Solution**: Ensure `VITE_API_URL` environment variable is set correctly

### Viewing Logs
```bash
# View container app logs
az containerapp logs show --name se-agent-factory-backend --resource-group se-agent-factory-rg
az containerapp logs show --name se-agent-factory-frontend --resource-group se-agent-factory-rg
```

## Scaling and Configuration

### Scaling Container Apps
```bash
# Scale backend
az containerapp update --name se-agent-factory-backend --resource-group se-agent-factory-rg --min-replicas 2 --max-replicas 20

# Scale frontend
az containerapp update --name se-agent-factory-frontend --resource-group se-agent-factory-rg --min-replicas 2 --max-replicas 20
```

### Environment Variables
- Backend: `PYTHONPATH=/app`
- Frontend: `VITE_API_URL=https://your-backend-url`

## Security Considerations

### Network Security
- Container apps use HTTPS by default
- Internal communication between services is encrypted
- CORS is configured for frontend-backend communication

### Identity and Access
- Container apps use system-assigned managed identity
- Container registry access is granted automatically
- No credentials stored in environment variables

## Cost Optimization

### Resource Allocation
- **Development**: 0.5 CPU, 1Gi memory
- **Production**: Scale based on usage patterns
- **Idle scaling**: Minimum 1 replica to avoid cold starts

### Monitoring Costs
```bash
# Check resource usage
az containerapp show --name se-agent-factory-backend --resource-group se-agent-factory-rg --query properties.template.containers[0].resources
```

## Cleanup

### Remove Resources
```bash
# Using Azure CLI
az group delete --name se-agent-factory-rg --yes --no-wait

# Using Azure Developer CLI (from project root)
azd down
```

## File Structure

```
deployment/
├── README.md              # This file
├── docker-compose.yml     # Local testing with Docker Compose
├── deploy.sh              # Bash deployment script
├── deploy.ps1             # PowerShell deployment script
├── test-deployment.sh     # Bash testing script
└── test-deployment.ps1    # PowerShell testing script
```

## Support and Troubleshooting

### Useful Commands
```bash
# Check container app status
az containerapp show --name se-agent-factory-backend --resource-group se-agent-factory-rg --query properties.provisioningState

# View configuration
az containerapp show --name se-agent-factory-backend --resource-group se-agent-factory-rg --query properties.configuration

# Check ingress configuration
az containerapp show --name se-agent-factory-backend --resource-group se-agent-factory-rg --query properties.configuration.ingress
```

### Getting Help
- [Azure Container Apps Documentation](https://docs.microsoft.com/en-us/azure/container-apps/)
- [Azure Developer CLI Documentation](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/)
- [Docker Documentation](https://docs.docker.com/) 