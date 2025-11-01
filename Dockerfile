FROM python:3.12-slim as base

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        curl \
        gnupg \
        unixodbc-dev \
        build-essential \
        libssl-dev \
        libffi-dev \
        libpq-dev \
        g++ \
        python3-dev \
        default-libmysqlclient-dev \
        wget \
        ca-certificates && \
    curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql18 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


WORKDIR /lion
COPY . .

RUN pip install --upgrade pip setuptools
RUN pip install . && pip show lion

# Env variabloes - Docker internal use only
# Azure App Service expects the container to listen on port 8000 or 8080 by default.
# This has to be set app settings, i.e., Environement Variables on the app, WEBSITES_PORT=8000
ENV PORT=8000
ENV FLASK_ENV=production
ENV LION_APP=lion.lion_app:app

# Expose Azure port: 
EXPOSE ${PORT}

ENTRYPOINT ["sh", "-c", "gunicorn -w 4 -k gthread -b 0.0.0.0:${PORT} ${LION_APP}"]

# gunicorn -w 4 -k gthread -b 0.0.0.0:8000 lion.lion_app:app

# ENV PYTHONUNBUFFERED=1
# ENV PYTHONDONTWRITEBYTECODE=1

# Set the following system settings when deploying through docker image
# When deploying through a prebuilt Docker image, the application is already fully built and packaged, so Azure App Service should not attempt 
# to rebuild or modify it during deployment or startup. To ensure this, the settings SCM_DO_BUILD_DURING_DEPLOYMENT=false and WEBSITES_DISABLE_ORYX=true 
# are applied. The first setting disables the Kudu build process that normally runs during source-based deployments, while the second prevents Oryx — Azure’s 
# automatic runtime detection and build tool — from running inside the container at startup. Together, these settings ensure Azure runs the container exactly as 
# built, avoiding unnecessary build steps, startup errors, or runtime conflicts.
# SCM_DO_BUILD_DURING_DEPLOYMENT = false when using Docker
# WEBSITES_DISABLE_ORYX=true

