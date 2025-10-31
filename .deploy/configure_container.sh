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
DEPLOY_APPROACH="Docker" # or Github CI/CD
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

# Create app with Docker container
az webapp create \
--name $APP_NAME \
--resource-group $RESOURCE_GROUP \
--plan $APP_PLAN \
--deployment-container-image-name https://index.docker.io/$DOCKER_IMAGE

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
