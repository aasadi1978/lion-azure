set -e

# Load secrets
source ./secret_variables.sh

# Define variables
AZURE_SUBSCRIPTION="AzureSubscription-V1.0"
RESOURCE_GROUP="rg-lion-app"
LOCATION="westeurope"
CONTAINER_ENV_NAME="lion-container-env"
APP_NAME="lion"
PORT=8000

# Login to Azure and set subscription
# az account set --subscription "$AZURE_SUBSCRIPTION"

# Create Resource Group
# az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Container Apps environment (only once per region)
az containerapp env create \
  --name $CONTAINER_ENV_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Deploy the Container App
az containerapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_ENV_NAME \
  --image $DOCKER_IMAGE \
  --target-port $PORT \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 1 \
  --cpu 2.0 \
  --memory 8Gi \
  --env-vars \
    AZURE_SQL_USER=$AZURE_SQL_USER \
    AZURE_SQL_PASS=$AZURE_SQL_PASS \
    AZURE_SQL_SERVER=$AZURE_SQL_SERVER \
    AZURE_SQL_DB=$AZURE_SQL_DB \
    AZURE_SUBSCRIPTION_ID=$AZURE_SUBSCRIPTION_ID \
    AZURE_RESOURCE_GROUP=$AZURE_RESOURCE_GROUP \
    AZURE_SUBSCRIPTION=$AZURE_SUBSCRIPTION \
    AZURE_LION_APP_TENANT_ID=$AZURE_LION_APP_TENANT_ID \
    AZURE_LION_APP_CLIENT_ID=$AZURE_LION_APP_CLIENT_ID \
    AZURE_LION_APP_OBJECT_ID=$AZURE_LION_APP_OBJECT_ID \
    AZURE_LION_APP_CLIENT_SECRET=$AZURE_LION_APP_CLIENT_SECRET \
    FLASK_ENV=$FLASK_ENV \
    FLASK_SECRET_KEY=$FLASK_SECRET_KEY \
    AZURE_STORAGE_CONNECTION_STRING=$AZURE_STORAGE_CONNECTION_STRING \
    PORT=$PORT

echo "✅ Container App '$APP_NAME' deployed to Azure Container Apps."
