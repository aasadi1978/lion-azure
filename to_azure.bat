az login

az webapp config appsettings set \
  --name lion-app \
  --resource-group <YOUR_RESOURCE_GROUP_NAME> \
  --settings ENABLE_ORYX_BUILD=false SCM_DO_BUILD_DURING_DEPLOYMENT=false WEBSITES_PORT=8000

az webapp config set \
  --name lion-b4c6bdd6dbhhg0ag \
  --resource-group <YOUR_RESOURCE_GROUP_NAME> \
  --startup-file ""
