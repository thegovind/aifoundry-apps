param name string
param location string = resourceGroup().location
param tags object = {}

param logAnalyticsWorkspaceName string = ''
param applicationInsightsName string = ''

module logAnalyticsWorkspace 'container-apps-logs.bicep' = if (empty(logAnalyticsWorkspaceName)) {
  name: 'container-apps-logs'
  params: {
    name: '${name}-logs'
    location: location
    tags: tags
  }
}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: empty(logAnalyticsWorkspaceName) ? logAnalyticsWorkspace.outputs.customerId : reference(resourceId('Microsoft.OperationalInsights/workspaces', logAnalyticsWorkspaceName), '2021-12-01-preview').customerId
        sharedKey: empty(logAnalyticsWorkspaceName) ? logAnalyticsWorkspace.outputs.primarySharedKey : listKeys(resourceId('Microsoft.OperationalInsights/workspaces', logAnalyticsWorkspaceName), '2021-12-01-preview').primarySharedKey
      }
    }
  }
}

output defaultDomain string = containerAppsEnvironment.properties.defaultDomain
output name string = containerAppsEnvironment.name
