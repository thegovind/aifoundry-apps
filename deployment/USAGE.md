# Deployment Scripts Usage Guide

This directory contains all the deployment-related scripts and configurations for the AIFoundry.app  application.

## Quick Reference

### 📦 Local Testing
```bash
# Start both services locally
docker-compose up --build

# Access:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8000
```

### 🚀 Deploy to Azure

#### Option 1: Using Azure Developer CLI
```bash
# From project root (recommended)
cd ..
azd init
azd up
```

#### Option 2: Manual deployment scripts
```bash
# Linux/macOS
chmod +x deploy.sh
./deploy.sh

# Windows
./deploy.ps1
```

### 🧪 Test Your Deployment
```bash
# Linux/macOS
chmod +x test-deployment.sh
./test-deployment.sh <backend-url> <frontend-url>

# Windows
./test-deployment.ps1 <backend-url> <frontend-url>
```

## Files in This Directory

| File | Purpose |
|------|---------|
| `README.md` | Comprehensive deployment guide |
| `USAGE.md` | This quick reference guide |
| `docker-compose.yml` | Local development with Docker |
| `deploy.sh` | Bash script for Azure deployment |
| `deploy.ps1` | PowerShell script for Azure deployment |
| `test-deployment.sh` | Bash script to test deployment |
| `test-deployment.ps1` | PowerShell script to test deployment |

## Prerequisites

- Azure CLI installed and logged in
- Docker running locally
- Node.js 18+ and Python 3.12+ for local development

## Common Commands

```bash
# Make scripts executable (Linux/macOS)
chmod +x *.sh

# View deployment logs
az containerapp logs show --name aifoundry-apps-backend --resource-group aifoundry-apps-rg

# Check deployment status
az containerapp show --name aifoundry-apps-backend --resource-group aifoundry-apps-rg --query properties.provisioningState

# Clean up resources
az group delete --name aifoundry-apps-rg --yes --no-wait
```

## Need Help?

- Read the full [deployment guide](./README.md)
- Check the [main project README](../README.md)
- Visit [Azure Container Apps documentation](https://docs.microsoft.com/en-us/azure/container-apps/) 