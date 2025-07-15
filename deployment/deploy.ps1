# Set variables
$ResourceGroup = "se-agent-factory-rg"
$Location = "eastus2"
$EnvironmentName = "se-agent-factory-env"
$RegistryName = "seagentfactoryacr$(Get-Date -Format 'yyyyMMddHHmmss')"
$BackendAppName = "se-agent-factory-backend"
$FrontendAppName = "se-agent-factory-frontend"

Write-Host "🚀 Deploying SE Agent Factory to Azure Container Apps" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Create resource group
Write-Host "Creating resource group..." -ForegroundColor Green
az group create --name $ResourceGroup --location $Location

# Create Azure Container Registry
Write-Host "Creating Azure Container Registry..." -ForegroundColor Green
az acr create --resource-group $ResourceGroup --name $RegistryName --sku Basic --admin-enabled true

# Create Container Apps Environment
Write-Host "Creating Container Apps Environment..." -ForegroundColor Green
az containerapp env create --name $EnvironmentName --resource-group $ResourceGroup --location $Location

# Build and push backend image
Write-Host "Building and pushing backend image..." -ForegroundColor Green
Set-Location ../src/backend
az acr build --registry $RegistryName --image backend:latest .

# Build and push frontend image  
Write-Host "Building and pushing frontend image..." -ForegroundColor Green
Set-Location ../frontend
az acr build --registry $RegistryName --image frontend:latest .

# Return to deployment directory
Set-Location ../../deployment

# Get ACR login server
$AcrLoginServer = (az acr show --name $RegistryName --resource-group $ResourceGroup --query loginServer --output tsv)

# Deploy backend container app
Write-Host "Deploying backend container app..." -ForegroundColor Green
az containerapp create `
  --name $BackendAppName `
  --resource-group $ResourceGroup `
  --environment $EnvironmentName `
  --image "$AcrLoginServer/backend:latest" `
  --target-port 8000 `
  --ingress external `
  --registry-server $AcrLoginServer `
  --registry-identity system `
  --cpu 0.5 `
  --memory 1.0Gi `
  --min-replicas 1 `
  --max-replicas 10 `
  --env-vars PYTHONPATH=/app

# Get backend URL
$BackendUrl = (az containerapp show --name $BackendAppName --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn --output tsv)

# Deploy frontend container app
Write-Host "Deploying frontend container app..." -ForegroundColor Green
az containerapp create `
  --name $FrontendAppName `
  --resource-group $ResourceGroup `
  --environment $EnvironmentName `
  --image "$AcrLoginServer/frontend:latest" `
  --target-port 80 `
  --ingress external `
  --registry-server $AcrLoginServer `
  --registry-identity system `
  --cpu 0.5 `
  --memory 1.0Gi `
  --min-replicas 1 `
  --max-replicas 10 `
  --env-vars VITE_API_URL=https://$BackendUrl

# Get frontend URL
$FrontendUrl = (az containerapp show --name $FrontendAppName --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn --output tsv)

Write-Host ""
Write-Host "🎉 Deployment complete!" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green
Write-Host "Backend URL: https://$BackendUrl" -ForegroundColor Cyan
Write-Host "Frontend URL: https://$FrontendUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Test the deployment using: ./test-deployment.ps1 https://$BackendUrl https://$FrontendUrl"
Write-Host "2. Open the frontend URL in your browser"
Write-Host "3. Monitor logs with: az containerapp logs show --name $BackendAppName --resource-group $ResourceGroup" 