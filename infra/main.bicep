@description('The location for all resources. Defaults to the resource group location.')
param location string = resourceGroup().location

@description('A unique suffix to append to resource names to ensure global uniqueness.')
param resourceSuffix string = uniqueString(resourceGroup().id)

@description('The administrator username for PostgreSQL.')
param pgSqlUsername string = 'postgresAdmin'

@description('The administrator password for PostgreSQL.')
@secure()
param pgSqlPassword string

// --- 1. Azure Container Registry (ACR) ---
// This will hold your Docker images for the frontend, backend, and chroma.
resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: 'acr${resourceSuffix}'
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// --- 2. Azure Database for PostgreSQL (Flexible Server) ---
// This replaces your local postgres container.
resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-03-01-preview' = {
  name: 'psql-${resourceSuffix}'
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    administratorLogin: pgSqlUsername
    administratorLoginPassword: pgSqlPassword
    version: '15'
    storage: {
      storageSizeGB: 32
    }
  }
}

// Allow Azure Services to access the database
resource postgresFirewall 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-03-01-preview' = {
  parent: postgres
  name: 'AllowAllAzureServicesAndResourcesWithinIG'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// Create the default database
resource authDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-03-01-preview' = {
  parent: postgres
  name: 'auth_db'
  properties: {
    charset: 'utf8'
    collation: 'en_US.utf8'
  }
}

// --- 3. Azure Container Apps Environment ---
// The secure boundary that holds your container apps.
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'law-${resourceSuffix}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
  }
}

resource acaEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'cae-${resourceSuffix}'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// --- 4. Container Apps ---

// ChromaDB Vector Store
resource chromaApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'ca-chroma'
  location: location
  properties: {
    managedEnvironmentId: acaEnvironment.id
    configuration: {
      ingress: {
        external: false // Internal only - not accessible from the internet
        targetPort: 8000
      }
    }
    template: {
      containers: [
        {
          name: 'chroma'
          image: 'chromadb/chroma:1.5.5'
          env: [
            { name: 'IS_PERSISTENT', value: 'FALSE' } // For ephemeral testing. Real deployment needs Azure Files volume.
            { name: 'ANONYMIZED_TELEMETRY', value: 'FALSE' }
          ]
          resources: {
            cpu: json('1.0')
            memory: '2.0Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}

// Backend API
resource backendApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'ca-backend'
  location: location
  properties: {
    managedEnvironmentId: acaEnvironment.id
    configuration: {
      ingress: {
        external: true // Accessible from the internet (for the frontend to call)
        targetPort: 8000
      }
      secrets: [
        { name: 'db-password', value: pgSqlPassword }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          // Using a placeholder image until ACR image is built and pushed
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          env: [
            { name: 'ENVIRONMENT', value: 'production' }
            { name: 'CHROMA_HOST', value: chromaApp.name }
            { name: 'CHROMA_PORT', value: '8000' }
            { name: 'CHROMA_SSL', value: 'false' }
            { name: 'DATABASE_URL', value: 'postgresql+asyncpg://${pgSqlUsername}:${pgSqlPassword}@${postgres.properties.fullyQualifiedDomainName}:5432/auth_db' }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

// Frontend
resource frontendApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'ca-frontend'
  location: location
  properties: {
    managedEnvironmentId: acaEnvironment.id
    configuration: {
      ingress: {
        external: true // Accessible from the internet
        targetPort: 5173 
      }
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          env: [
            { name: 'VITE_API_URL', value: 'https://${backendApp.properties.configuration.ingress.fqdn}' }
          ]
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

output acrLoginServer string = acr.properties.loginServer
output frontendUrl string = 'https://${frontendApp.properties.configuration.ingress.fqdn}'
output backendUrl string = 'https://${backendApp.properties.configuration.ingress.fqdn}'
output dbFqdn string = postgres.properties.fullyQualifiedDomainName
