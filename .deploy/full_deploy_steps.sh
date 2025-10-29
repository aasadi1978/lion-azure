# Define your variables
RESOURCE_GROUP="rg-lion-app"
APP_PLAN="lion-app-plan"
APP_NAME="lion"
LOCATION="westeurope"
RUNTIME="PYTHON|3.12"
# NOTE: az webapp list-runtimes --os linux --output table
DEPLOY_APPROACH="Docker"
# or Github CI/CD

# Create the Resource Group if required
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create an App Service Plan
# This defines the pricing tier (e.g., B1 = Basic, S1 = Standard):
az appservice plan create \
  --name $APP_PLAN \
  --resource-group $RESOURCE_GROUP \
  --sku B1 \ 
  --is-linux

# Create the Web App (Python runtime example)
az webapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_PLAN \
  --runtime $RUNTIME


# The following app settings have to be set based on deployment approach
if [ "$DEPLOY_APPROACH" = "Docker" ]; then

    SCM_DO_BUILD_DURING_DEPLOYMENT=false
    WEBSITES_DISABLE_ORYX=true

    az webapp create \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --plan $APP_PLAN \
    --deployment-container-image-name https://index.docker.io/$DOCKER_IMAGE

else
  SCM_DO_BUILD_DURING_DEPLOYMENT=true
  WEBSITES_DISABLE_ORYX=false
fi

# Verify
echo "Configuring app settings for deployment approach: $DEPLOY_APPROACH"
echo "→ SCM_DO_BUILD_DURING_DEPLOYMENT=$SCM_DO_BUILD_DURING_DEPLOYMENT"
echo "→ WEBSITES_DISABLE_ORYX=$WEBSITES_DISABLE_ORYX"

# Secrets: Env Variables
# =======================================
# Copy secret keys from secrets.sh or github repo secrets
AZURE_LION_APP_TENANT_ID="0f1f6ccxxxxxxxxxxxxxxxxx2b4c1d"
AZURE_LION_APP_CLIENT_ID="d72880exxxxxxxxxxxxxxxxxx168e3397c0"
AZURE_LION_APP_OBJECT_ID="e25dd9abxxxxxxxxxxxxxxxxxc220cf1b"
AZURE_LION_APP_CLIENT_SECRET="Z~A8QxxxxxxxxxxxxxxxxxxxxxddnHRWh~bjZ"
FLASK_SECRET_KEY="tAig8gl-n7xxxxxxxxxxxxxxxxxxxxx-z2BMo5JPN0"
AZURE_SUBSCRIPTION_ID="96c96b4xxxxxxxxxxxxxxxx10e6bd3"
DOCKER_IMAGE=asadi197xxxxxxxxxxxxxxxxp:latest
AZURE_SQL_USER="SECRET"
AZURE_SQL_PASS="SECRET"
AZURE_SQL_SERVER="lixxxxxxxxxxxxxxxxxxxxxdows.net"
AZURE_SQL_DB="lion-sql-db"
AZURE_STORAGE_CONNECTION_STRING="DefaultEndpoxxxxxxxxxxxxxxxxxxxxxxxxxMk987plulZCvn+ASt1vCiTA==;EndpointSuffix=core.windows.net"

# =======================================

# Env variables
AZURE_RESOURCE_GROUP="rg-lion-app"
AZURE_SUBSCRIPTION="AzureSubscription-V1.0"
FLASK_ENV="produnction"
WEBSITES_CONTAINER_START_TIME_LIMIT=188
WEBSITES_ENABLE_APP_SERVICE_STORAGE=false
WEBSITES_PORT=8000

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


if [ "$DEPLOY_APPROACH" = "Docker" ]; then
    az webapp create \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --plan $APP_PLAN \
    --deployment-container-image-name https://index.docker.io/$DOCKER_IMAGE

# Enable logging
az webapp log config \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --application-logging true \
  --docker-container-logging filesystem
