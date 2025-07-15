targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Id of the user or app to assign application roles')
param principalId string = ''

// Optional parameters to override the default azd resource naming conventions. Update the main.parameters.json file to set the desired naming convention.
@description('A token to inject into the name of each resource.')
param resourceToken string = ''

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken_ = !empty(resourceToken) ? resourceToken : toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }

// Organize resources in a resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

var resourceGroupName = ''

// Container registry
module containerRegistry './core/host/container-registry.bicep' = {
  name: 'container-registry'
  scope: rg
  params: {
    name: '${abbrs.containerRegistryRegistries}${resourceToken_}'
    location: location
    tags: tags
  }
}

// Container apps environment
module containerAppsEnvironment './core/host/container-apps-environment.bicep' = {
  name: 'container-apps-env'
  scope: rg
  params: {
    name: '${abbrs.appManagedEnvironments}${resourceToken_}'
    location: location
    tags: tags
  }
}

// Backend container app
module backend './app/backend.bicep' = {
  name: 'backend'
  scope: rg
  params: {
    name: !empty(backendServiceName) ? backendServiceName : '${abbrs.appContainerApps}backend-${resourceToken_}'
    location: location
    tags: tags
    containerAppsEnvironmentName: containerAppsEnvironment.outputs.name
    containerRegistryName: containerRegistry.outputs.name
    exists: backendExists
  }
}

// Frontend container app
module frontend './app/frontend.bicep' = {
  name: 'frontend'
  scope: rg
  params: {
    name: !empty(frontendServiceName) ? frontendServiceName : '${abbrs.appContainerApps}frontend-${resourceToken_}'
    location: location
    tags: tags
    containerAppsEnvironmentName: containerAppsEnvironment.outputs.name
    containerRegistryName: containerRegistry.outputs.name
    backendUri: backend.outputs.uri
    exists: frontendExists
  }
}

var backendServiceName = ''
var frontendServiceName = ''
var backendExists = false
var frontendExists = false

// App outputs
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP string = rg.name

output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.outputs.loginServer
output AZURE_CONTAINER_REGISTRY_NAME string = containerRegistry.outputs.name

output BACKEND_URI string = backend.outputs.uri
output FRONTEND_URI string = frontend.outputs.uri
