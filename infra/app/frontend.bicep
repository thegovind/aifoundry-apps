param name string
param location string = resourceGroup().location
param tags object = {}

param containerAppsEnvironmentName string
param containerRegistryName string
param backendUri string
param exists bool = false

param containerCpuCoreCount string = '0.5'
param containerMemory string = '1.0Gi'
param containerMinReplicas int = 1
param containerMaxReplicas int = 10

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' existing = {
  name: containerAppsEnvironmentName
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' existing = {
  name: containerRegistryName
}

resource app 'Microsoft.App/containerApps@2023-05-01' = {
  name: name
  location: location
  tags: union(tags, {'azd-service-name': 'frontend'})
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 80
        transport: 'http'
        allowInsecure: false
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: 'system'
        }
      ]
    }
    template: {
      containers: [
        {
          image: exists ? 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' : 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          name: 'frontend'
          env: [
            {
              name: 'VITE_API_URL'
              value: backendUri
            }
          ]
          resources: {
            cpu: json(containerCpuCoreCount)
            memory: containerMemory
          }
          probes: [
            {
              type: 'Readiness'
              httpGet: {
                path: '/'
                port: 80
                scheme: 'HTTP'
              }
              initialDelaySeconds: 10
              periodSeconds: 5
              timeoutSeconds: 3
              successThreshold: 1
              failureThreshold: 3
            }
            {
              type: 'Liveness'
              httpGet: {
                path: '/'
                port: 80
                scheme: 'HTTP'
              }
              initialDelaySeconds: 30
              periodSeconds: 30
              timeoutSeconds: 3
              successThreshold: 1
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: containerMinReplicas
        maxReplicas: containerMaxReplicas
      }
    }
  }
}

// Give the app access to Container Registry
resource containerRegistryAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: containerRegistry
  name: guid(subscription().id, resourceGroup().id, app.id, 'b24988ac-6180-42a0-ab88-20f7382dd24c')
  properties: {
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: app.identity.principalId
  }
}

output defaultDomain string = containerAppsEnvironment.properties.defaultDomain
output name string = app.name
output uri string = 'https://${app.properties.configuration.ingress.fqdn}'
