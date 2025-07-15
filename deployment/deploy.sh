#!/bin/bash

# Set variables
RESOURCE_GROUP="se-agent-factory-rg"
LOCATION="eastus2"
ENVIRONMENT_NAME="se-agent-factory-env"
REGISTRY_NAME="seagentfactoryacr$(date +%s)"
BACKEND_APP_NAME="se-agent-factory-backend"
FRONTEND_APP_NAME="se-agent-factory-frontend"

echo "🚀 Deploying SE Agent Factory to Azure Container Apps"
echo "=================================================="

# Create resource group
echo "Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure Container Registry
echo "Creating Azure Container Registry..."
az acr create --resource-group $RESOURCE_GROUP --name $REGISTRY_NAME --sku Basic --admin-enabled true

# Create Container Apps Environment
echo "Creating Container Apps Environment..."
az containerapp env create --name $ENVIRONMENT_NAME --resource-group $RESOURCE_GROUP --location $LOCATION

# Build and push backend image
echo "Building and pushing backend image..."
cd ../src/backend
az acr build --registry $REGISTRY_NAME --image backend:latest .

# Build and push frontend image  
echo "Building and pushing frontend image..."
cd ../frontend
az acr build --registry $REGISTRY_NAME --image frontend:latest .

# Return to deployment directory
cd ../../deployment

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query loginServer --output tsv)

# Deploy backend container app
echo "Deploying backend container app..."
az containerapp create \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT_NAME \
  --image $ACR_LOGIN_SERVER/backend:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-identity system \
  --cpu 0.5 \
  --memory 1.0Gi \
  --min-replicas 1 \
  --max-replicas 10 \
  --env-vars PYTHONPATH=/app

# Get backend URL
BACKEND_URL=$(az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn --output tsv)

# Deploy frontend container app
echo "Deploying frontend container app..."
az containerapp create \
  --name $FRONTEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT_NAME \
  --image $ACR_LOGIN_SERVER/frontend:latest \
  --target-port 80 \
  --ingress external \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-identity system \
  --cpu 0.5 \
  --memory 1.0Gi \
  --min-replicas 1 \
  --max-replicas 10 \
  --env-vars VITE_API_URL=https://$BACKEND_URL

# Get frontend URL
FRONTEND_URL=$(az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn --output tsv)

echo ""
echo "🎉 Deployment complete!"
echo "======================"
echo "Backend URL: https://$BACKEND_URL"
echo "Frontend URL: https://$FRONTEND_URL"
echo ""
echo "📋 Next steps:"
echo "1. Test the deployment using: ./test-deployment.sh https://$BACKEND_URL https://$FRONTEND_URL"
echo "2. Open the frontend URL in your browser"
echo "3. Monitor logs with: az containerapp logs show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP" 