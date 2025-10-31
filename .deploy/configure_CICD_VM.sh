# Copy and paste the content of the secret_variables.sh file here
source ./secret_variables.sh

# Define your variables
AZURE_SUBSCRIPTION="AzureSubscription-V1.0"
AZURE_RESOURCE_GROUP="rg-lion-app"
RESOURCE_GROUP="rg-lion-app"
APP_PLAN="lion-app-plan"
APP_NAME="lion"
LOCATION="westeurope"
RUNTIME="PYTHON|3.12"
DEPLOY_APPROACH="CI/CD"
FLASK_ENV="production"
WEBSITES_CONTAINER_START_TIME_LIMIT=188
WEBSITES_ENABLE_APP_SERVICE_STORAGE=false
WEBSITES_PORT=8000

SCM_DO_BUILD_DURING_DEPLOYMENT=$DEPLOY_APPROACH == "CI/CD"
WEBSITES_DISABLE_ORYX=$DEPLOY_APPROACH == "Docker"

# Create the Resource Group if required
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create an App Service Plan
# This defines the pricing tier (e.g., B1 = Basic, S1 = Standard):
az appservice plan create \
  --name $APP_PLAN \
  --resource-group $RESOURCE_GROUP \
  --sku B1 \ 
  --is-linux

Create the Web App (Python runtime example)
az webapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_PLAN \
  --runtime $RUNTIME


SCM_DO_BUILD_DURING_DEPLOYMENT=false
WEBSITES_DISABLE_ORYX=true


# Verify
echo "Configuring app settings for deployment approach: $DEPLOY_APPROACH"
echo "→ SCM_DO_BUILD_DURING_DEPLOYMENT=$SCM_DO_BUILD_DURING_DEPLOYMENT"
echo "→ WEBSITES_DISABLE_ORYX=$WEBSITES_DISABLE_ORYX"

# Update system settings
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings AZURE_SQL_USER=$AZURE_SQL_USER AZURE_SQL_PASS=$AZURE_SQL_PASS AZURE_SQL_SERVER=$AZURE_SQL_SERVER AZURE_SQL_DB=$AZURE_SQL_DB \
  AZURE_SUBSCRIPTION_ID=$AZURE_SUBSCRIPTION_ID AZURE_RESOURCE_GROUP=$AZURE_RESOURCE_GROUP AZURE_SUBSCRIPTION=$AZURE_SUBSCRIPTION \
  AZURE_LION_APP_TENANT_ID=$AZURE_LION_APP_TENANT_ID AZURE_LION_APP_CLIENT_ID=$AZURE_LION_APP_CLIENT_ID \
  AZURE_LION_APP_OBJECT_ID=$AZURE_LION_APP_OBJECT_ID AZURE_LION_APP_CLIENT_SECRET=$AZURE_LION_APP_CLIENT_SECRET FLASK_ENV=$FLASK_ENV \
  FLASK_SECRET_KEY=$FLASK_SECRET_KEY WEBSITES_CONTAINER_START_TIME_LIMIT=$WEBSITES_CONTAINER_START_TIME_LIMIT \
  AZURE_STORAGE_CONNECTION_STRING=$AZURE_STORAGE_CONNECTION_STRING WEBSITES_ENABLE_APP_SERVICE_STORAGE=$WEBSITES_ENABLE_APP_SERVICE_STORAGE \
  WEBSITES_PORT=$WEBSITES_PORT PORT=$WEBSITES_PORT \
  SCM_DO_BUILD_DURING_DEPLOYMENT=$SCM_DO_BUILD_DURING_DEPLOYMENT WEBSITES_DISABLE_ORYX=$WEBSITES_DISABLE_ORYX

# Verify app settings
az webapp config appsettings list \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output table


# Enable logging
az webapp log config \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --application-logging true \
  --docker-container-logging filesystem
