# Azure Deployment Guide

## Prerequisites

- Azure subscription
- Azure CLI installed
- Docker installed
- Azure Container Registry (ACR)

## Architecture

```
┌──────────────────────────────────────┐
│  Azure Container Registry (ACR)      │
│  (Stores Docker images)              │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  Azure Container Apps                │
│  (Serverless container runtime)      │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  Azure Key Vault                     │
│  (Secrets: LLM_API_KEY, etc)         │
└──────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  Azure Log Analytics                 │
│  (Logs, metrics, alerts)             │
└──────────────────────────────────────┘
```

## Step 1: Create Azure Resources

### Set environment variables
```bash
export RESOURCE_GROUP=ticketai-rg
export REGISTRY_NAME=ticketairegistry
export LOCATION=eastus
export CONTAINER_APP_NAME=ticketai-api
export KEYVAULT_NAME=ticketai-kv
```

### Create resource group
```bash
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION
```

### Create Container Registry
```bash
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $REGISTRY_NAME \
  --sku Basic
```

### Create Key Vault
```bash
az keyvault create \
  --name $KEYVAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Add LLM API key (securely)
az keyvault secret set \
  --vault-name $KEYVAULT_NAME \
  --name "llm-api-key" \
  --value "sk-your-api-key-here"
```

### Create Container Apps Environment
```bash
az containerapp env create \
  --name ticketai-env \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

## Step 2: Build and Push Docker Image

```bash
# Build image
docker build -t $REGISTRY_NAME.azurecr.io/ticketai:latest .

# Login to ACR
az acr login --name $REGISTRY_NAME

# Push image
docker push $REGISTRY_NAME.azurecr.io/ticketai:latest
```

## Step 3: Deploy to Container Apps

```bash
# Get Key Vault secret
LLM_API_KEY=$(az keyvault secret show \
  --vault-name $KEYVAULT_NAME \
  --name "llm-api-key" \
  --query value -o tsv)

# Deploy Container App
az containerapp create \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment ticketai-env \
  --image $REGISTRY_NAME.azurecr.io/ticketai:latest \
  --target-port 8000 \
  --ingress 'external' \
  --registry-server $REGISTRY_NAME.azurecr.io \
  --registry-username $REGISTRY_USERNAME \
  --registry-password $REGISTRY_PASSWORD \
  --env-vars \
    MODEL_NAME=gpt-4 \
    LLM_ENDPOINT=https://api.openai.com/v1/chat/completions \
    LLM_API_KEY="$LLM_API_KEY" \
    MAX_INPUT_LENGTH=5000 \
    MAX_OUTPUT_TOKENS=500 \
    TIMEOUT_SECONDS=30 \
    RATE_LIMIT_PER_MINUTE=60 \
    LOG_LEVEL=INFO \
    ENVIRONMENT=production
```

## Step 4: Setup Monitoring

### Enable Azure Log Analytics
```bash
az containerapp logs show \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --follow
```

### Create Alerts
```bash
# Alert on high error rate
az monitor metrics alert create \
  --name "ticketai-error-rate-alert" \
  --resource-group $RESOURCE_GROUP \
  --scopes /subscriptions/{subscription-id}/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.App/containerApps/$CONTAINER_APP_NAME \
  --condition "total ErrorRate > 5" \
  --window-size 5m \
  --evaluation-frequency 1m
```

## Step 5: Test Deployment

```bash
# Get container app URL
APP_URL=$(az containerapp show \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn \
  -o tsv)

# Send test request
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"ticket": "I cannot log in"}' \
  https://$APP_URL/triage
```

## Step 6: Setup CI/CD

Update GitHub Actions secrets:
```bash
# Add to GitHub repo settings
AZURE_REGISTRY_LOGIN
AZURE_REGISTRY_PASSWORD
AZURE_REGISTRY_URL
```

## Monitoring & Troubleshooting

### View logs
```bash
az containerapp logs show \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP
```

### Check container status
```bash
az containerapp show \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.provisioningState
```

### Restart container
```bash
az containerapp update \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP
```

## Scaling

### Auto-scale configuration
```bash
az containerapp update \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --scale-rule-type cpu \
  --scale-rule-auth "Azure Monitor" \
  --min-replicas 1 \
  --max-replicas 10
```

## Cost Management

- **Container Apps**: Billed per vCPU-second and memory
- **Key Vault**: Small monthly cost + per-operation charges
- **Log Analytics**: Per-GB ingestion + retention
- **ACR**: Basic tier is cost-effective for small teams

## Security Best Practices

1. **Never commit API keys** — use Key Vault only
2. **Enable private endpoints** for Key Vault if needed
3. **Use managed identity** for container to access Key Vault
4. **Enable audit logging** in Key Vault
5. **Rotate secrets regularly**
6. **Use RBAC** for Azure resource access control
