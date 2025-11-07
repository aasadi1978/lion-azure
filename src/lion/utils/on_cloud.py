from os import getenv
ON_CLOUD = getenv('AZURE_SQL_USER', None) is not None

if ON_CLOUD:
    ON_CLOUD = ON_CLOUD and getenv('AZURE_SQL_PASS', None) is not None
    ON_CLOUD = ON_CLOUD and getenv('AZURE_SQL_SERVER', None) is not None
    ON_CLOUD = ON_CLOUD and getenv('AZURE_SQL_DB', None) is not None
    ON_CLOUD = ON_CLOUD and getenv('AZURE_SUBSCRIPTION_ID', None) is not None
    ON_CLOUD = ON_CLOUD and getenv('AZURE_RESOURCE_GROUP', None) is not None
    ON_CLOUD = ON_CLOUD and getenv('AZURE_SUBSCRIPTION', None) is not None
    ON_CLOUD = ON_CLOUD and getenv('AZURE_LION_APP_TENANT_ID', None) is not None
    ON_CLOUD = ON_CLOUD and getenv('AZURE_LION_APP_CLIENT_ID', None) is not None
    ON_CLOUD = ON_CLOUD and getenv('AZURE_LION_APP_OBJECT_ID', None) is not None
    ON_CLOUD = ON_CLOUD and getenv('AZURE_LION_APP_CLIENT_SECRET', None) is not None