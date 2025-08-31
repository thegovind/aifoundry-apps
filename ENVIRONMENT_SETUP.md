# Environment Setup

## Required Environment Variables

Create a `.env` file in the `src/backend/` directory with the following variables:

```bash
# Azure AI Configuration
# Replace these with your actual Azure AI project details
AZURE_PROJECT_ENDPOINT=https://your-resource.services.ai.azure.com/api/projects/your-project
AZURE_API_KEY=your-azure-ai-api-key-here
AZURE_MODEL_NAME=gpt-4.1-nano

# Optional: GitHub Configuration for MCP integration
GITHUB_TOKEN=your-github-personal-access-token

# Optional: Devin API Configuration
DEVIN_API_BASE_URL=https://api.devin.ai
DEVIN_API_KEY=your-devin-api-key-here

# Application Configuration
PYTHONPATH=/app

# Dependencies
- PyNaCl: Required for GitHub secrets encryption

# Cosmos DB Configuration
COSMOS_CONNECTION_STRING=AccountEndpoint=https://aifoundryapps-cosmos.documents.azure.com:443/;AccountKey=your-cosmos-key-here;
COSMOS_DATABASE_ID=aifoundry
```

## Setup Instructions

1. Copy the above environment variables into a new file: `src/backend/.env`
2. Replace the placeholder values with your actual credentials
3. Never commit the `.env` file to version control (it's already in `.gitignore`)

## Getting Your Azure AI Credentials

1. Go to [Azure AI Foundry](https://ai.azure.com/)
2. Navigate to your project
3. Go to Settings > Project details
4. Copy the endpoint URL and API key

## Security Notes

- The `.env` file is automatically ignored by git
- Never hardcode credentials in source code
- Use Azure Key Vault or Managed Identity for production deployments
