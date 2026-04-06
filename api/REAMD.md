# CarClinch Background Removal API

## Overview
CarClinch Background Removal API is a FastAPI service that processes car images by removing or replacing backgrounds and stores the generated results in Azure Blob Storage.

The API supports:
- single-model background replacement
- multi-model background replacement
- private image serving through backend URLs
- local development with Docker
- Azure deployment with Terraform

---

## Main Endpoints

### `GET /`
Basic health check endpoint.

### `POST /replace-background`
Processes one car image with one background image using the default model and returns a backend image URL.

### `POST /replace-background-all-models`
Processes the same input with all supported models and returns one result per model.

### `GET /images/{blob_name}`
Serves a processed image from private Azure Blob Storage through the backend.

---

## Tech Stack
- FastAPI
- Python
- Docker
- Azure Blob Storage
- Azure Container Registry (ACR)
- Azure Container Apps
- Terraform

---

## Project Structure

```text
.
├── api/
│   └── src/
│       ├── main.py
│       ├── blob_storage.py
│       ├── util.py
│       ├── constants.py
│       └── requirements.txt
├── core/
├── infrastructure/
│   ├── main.tf
│   ├── variables.tf
│   ├── providers.tf
│   └── outputs.tf
├── Dockerfile
├── .dockerignore
├── .env
└── .env.example
```

---

## Prerequisites

Before running the project, make sure you have:

- Git installed
- Docker installed and running
- Azure CLI installed
- Terraform installed
- An Azure subscription
- Permission to create Azure resources in your subscription
- Permission to push images to Azure Container Registry
- Python 3.12 available locally if you also want to run the API outside Docker

---

## Azure Login and Subscription Setup

### 1. Log in to Azure

```bash
az login
```

### 2. Check the current subscription

```bash
az account show
```

### 3. If needed, switch to the correct subscription

```bash
az account set --subscription "<subscription-id-or-name>"
```

### 4. Register the required resource provider for Container Apps

```bash
az provider register --namespace Microsoft.App
az provider show --namespace Microsoft.App --query registrationState -o tsv
```

Wait until the registration state is:

```text
Registered
```

### 5. Optional: register related providers

```bash
az provider register --namespace Microsoft.OperationalInsights
az provider register --namespace Microsoft.ContainerRegistry
az provider register --namespace Microsoft.Storage
```

---

## Region Note

This project was deployed in:

```text
southafricanorth
```

If your Azure subscription is region-restricted, make sure the Terraform `location` variable matches an allowed region before applying infrastructure.

---

## Deployment Order

The deployment must happen in this order:

1. Provision the base Azure infrastructure first
2. Get the generated Azure values
3. Create the `.env` file
4. Build and push the Docker image to Azure Container Registry
5. Apply Terraform again to create the Container App
6. Test the deployed application
7. Optionally run the app locally with Docker

This order matters because the Container App references an image tag in ACR.  
If the image does not exist yet, deployment will fail with an error like:

```text
MANIFEST_UNKNOWN: manifest tagged by "latest" is not found
```

---

## Step 1: Provision Base Azure Infrastructure

Terraform provisions:
- Resource Group
- Storage Account
- Blob Container
- Azure Container Registry
- Log Analytics Workspace
- Container Apps Environment

### Go to the Terraform folder

```bash
cd infrastructure
```

### Initialize Terraform

```bash
terraform init
```

### Apply only the base infrastructure first

```bash
terraform apply \
  -target=azurerm_resource_group.this \
  -target=azurerm_storage_account.this \
  -target=azurerm_storage_container.processed_images \
  -target=azurerm_container_registry.this \
  -target=azurerm_log_analytics_workspace.this \
  -target=azurerm_container_app_environment.this \
  -target=random_string.storage_suffix \
  -target=random_string.acr_suffix
```

This first apply creates:
- Resource Group
- Storage Account
- Blob Container
- Azure Container Registry
- Log Analytics Workspace
- Container Apps Environment

It does **not** create the Container App yet.

---

## Step 2: Get the Provisioned Values

Get the storage and ACR values:

```bash
terraform output -raw storage_account_name
terraform output -raw processed_images_container_name
terraform output -raw acr_name
terraform output -raw acr_login_server
```

---

## Step 3: Get the Storage Account Key

Get the storage account key from Azure CLI:

```bash
az storage account keys list \
  --resource-group rg-carclinch-dev \
  --account-name <storage_account_name> \
  --query "[0].value" \
  -o tsv
```

Example:

```bash
az storage account keys list \
  --resource-group rg-carclinch-dev \
  --account-name myStorageAccount \
  --query "[0].value" \
  -o tsv
```

---

## Step 4: Create the `.env` File

Create a `.env` file in the project root.

Example:

```env
AZURE_STORAGE_ACCOUNT_NAME=your_storage_account_name
AZURE_STORAGE_ACCOUNT_KEY=your_storage_account_key
AZURE_STORAGE_CONTAINER_NAME=processed-images
IMAGE_BASE_DIR=images
```

You can also keep a `.env.example` file like this:

```env
AZURE_STORAGE_ACCOUNT_NAME=
AZURE_STORAGE_ACCOUNT_KEY=
AZURE_STORAGE_CONTAINER_NAME=processed-images
IMAGE_BASE_DIR=images
```

### Quick way to populate values

From the project root:

```bash
export AZURE_STORAGE_ACCOUNT_NAME=$(cd infrastructure && terraform output -raw storage_account_name)

export AZURE_STORAGE_ACCOUNT_KEY=$(az storage account keys list \
  --resource-group rg-carclinch-dev \
  --account-name "$AZURE_STORAGE_ACCOUNT_NAME" \
  --query "[0].value" \
  -o tsv)
```

---

## Step 5: Log in to Azure Container Registry

Use the ACR name from Terraform:

```bash
az acr login --name <acr_name>
```

Example:

```bash
az acr login --name myacrname
```

---

## 6. Build and Push the Docker Image to Azure Container Registry

After the infrastructure is created, push the API image to ACR.

`<acr_login_server>` is a placeholder.  
Get its real value from Terraform and store it in `ACR_LOGIN_SERVER` before running the Docker build command.

Run this from the project root:

```bash
export ACR_LOGIN_SERVER=$(cd infrastructure && terraform output -raw acr_login_server)
echo "$ACR_LOGIN_SERVER"
```

### 1. Get ACR details from Terraform

```bash
cd infrastructure
terraform output -raw acr_name
terraform output -raw acr_login_server
cd ..
```

### 2. Log in to ACR

```bash
az acr login --name <acr_name>
```

### 3. Build and push the image

#### On x86 machines

```bash
docker build -t carclinch-bg-removal-api:local .
docker tag carclinch-bg-removal-api:local "$ACR_LOGIN_SERVER/carclinch-bg-removal-api:latest"
docker push "$ACR_LOGIN_SERVER/carclinch-bg-removal-api:latest"
```

#### On Apple Silicon / Mac

```bash
docker buildx rm carclinch-builder || true
docker buildx create --use --name carclinch-builder

docker buildx build \
  --platform linux/amd64 \
  -t "$ACR_LOGIN_SERVER/carclinch-bg-removal-api:latest" \
  --push \
  .
```

### 4. Re-apply Terraform if needed

If the infrastructure is already up and only the image changed:

```bash
cd infrastructure
terraform apply
cd ..
```

If Terraform fails with an error saying the Container App already exists, delete the existing Container App and run `terraform apply` again:

```bash
az containerapp delete \
  --name ca-carclinch-dev \
  --resource-group rg-carclinch-dev \
  --yes

cd infrastructure
terraform apply
cd ..
```

---

## Step 7: Create the Container App

Now that the image exists in ACR, run the full Terraform apply:

```bash
cd infrastructure
terraform apply
```

This second apply creates or updates the Azure Container App successfully.

---

## Step 8: Get the Deployed URL

Get the stable Container App URL:

```bash
terraform output -raw container_app_url
```

Open:

```text
https://<container_app_url>
```

Then open the docs:

```text
https://<container_app_url>/docs
```

---

## Step 9: Test the Deployed Application

Verify that the following endpoints work:

- `GET /`
- `POST /replace-background`
- `POST /replace-background-all-models`
- `GET /images/{blob_name}`

---

## Running Locally with Docker

This is optional, but useful for local testing after the Azure values are available.

### Build the Docker image

From the project root:

```bash
docker build -t carclinch-bg-removal-api:local .
```

### Run the container

```bash
docker run --rm -p 8000:8000 --env-file .env carclinch-bg-removal-api:local
```

### Open the API docs

```text
http://127.0.0.1:8000/docs
```

---

## End-to-End Azure Deployment Flow

### Step 1: Log in to Azure

```bash
az login
az account set --subscription "<subscription-id-or-name>"
```

### Step 2: Register required providers

```bash
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights
az provider register --namespace Microsoft.ContainerRegistry
az provider register --namespace Microsoft.Storage
```

### Step 3: Provision base infrastructure

```bash
cd infrastructure
terraform init

terraform apply \
  -target=azurerm_resource_group.this \
  -target=azurerm_storage_account.this \
  -target=azurerm_storage_container.processed_images \
  -target=azurerm_container_registry.this \
  -target=azurerm_log_analytics_workspace.this \
  -target=azurerm_container_app_environment.this \
  -target=random_string.storage_suffix \
  -target=random_string.acr_suffix
```

### Step 4: Get Terraform outputs

```bash
terraform output -raw storage_account_name
terraform output -raw processed_images_container_name
terraform output -raw acr_name
terraform output -raw acr_login_server
```

### Step 5: Get the storage key

```bash
az storage account keys list \
  --resource-group rg-carclinch-dev \
  --account-name <storage_account_name> \
  --query "[0].value" \
  -o tsv
```

### Step 6: Create the `.env` file

```env
AZURE_STORAGE_ACCOUNT_NAME=your_storage_account_name
AZURE_STORAGE_ACCOUNT_KEY=your_storage_account_key
AZURE_STORAGE_CONTAINER_NAME=processed-images
IMAGE_BASE_DIR=images
```

### Step 7: Log in to ACR

```bash
az acr login --name <acr_name>
```

### Step 8: Build and push the Docker image

#### x86 machines

```bash
docker build -t carclinch-bg-removal-api:local .
docker tag carclinch-bg-removal-api:local <acr_login_server>/carclinch-bg-removal-api:latest
docker push <acr_login_server>/carclinch-bg-removal-api:latest
```

#### Apple Silicon

```bash
docker buildx create --use --name carclinch-builder || docker buildx use carclinch-builder

docker buildx build \
  --platform linux/amd64 \
  -t <acr_login_server>/carclinch-bg-removal-api:latest \
  --push \
  .
```

### Step 9: Apply Terraform again

```bash
cd infrastructure
terraform apply
```

### Step 10: Get the deployed URL

```bash
terraform output -raw container_app_url
```

### Step 11: Test the app

```text
https://<container_app_url>/docs
```

---

## Local Validation Checklist

Before deploying, make sure:
- `.env` exists
- Docker image builds successfully
- local container starts successfully
- `/docs` opens locally
- `/replace-background` works locally
- `/replace-background-all-models` works locally
- `GET /images/{blob_name}` works locally

---

## Azure Validation Checklist

After deployment, make sure:
- `az login` completed successfully
- correct Azure subscription is selected
- required providers are registered
- base Terraform apply completes successfully
- ACR is created
- image is pushed to ACR
- second Terraform apply completes successfully
- Container App is deployed successfully
- `terraform output -raw container_app_url` returns a valid URL
- root endpoint works
- `/docs` opens
- `/replace-background` works
- `/replace-background-all-models` works
- `/images/{blob_name}` serves images correctly

---

## Destroy Infrastructure

To avoid cloud costs:

```bash
cd infrastructure
terraform destroy
```

---

## Notes

- The API stores generated images in Azure Blob Storage.
- The backend serves private blob images through `/images/{blob_name}`.
- For Azure Container Apps deployment from a Mac with Apple Silicon, always build the Docker image as `linux/amd64`.
- Terraform local files such as `.terraform/`, `terraform.tfstate`, and related files should not be committed to Git.

---

## Quick Start Summary

### Azure First

```bash
az login
az account set --subscription "<subscription-id-or-name>"

cd infrastructure
terraform init

terraform apply \
  -target=azurerm_resource_group.this \
  -target=azurerm_storage_account.this \
  -target=azurerm_storage_container.processed_images \
  -target=azurerm_container_registry.this \
  -target=azurerm_log_analytics_workspace.this \
  -target=azurerm_container_app_environment.this \
  -target=random_string.storage_suffix \
  -target=random_string.acr_suffix
```

### Push Image

```bash
terraform output -raw acr_name
terraform output -raw acr_login_server

az acr login --name <acr_name>

docker build -t carclinch-bg-removal-api:local .
docker tag carclinch-bg-removal-api:local <acr_login_server>/carclinch-bg-removal-api:latest
docker push <acr_login_server>/carclinch-bg-removal-api:latest
```

### Finish Deployment

```bash
cd infrastructure
terraform apply
terraform output -raw container_app_url
cd ..
```

### Local

```bash
docker build -t carclinch-bg-removal-api:local .
docker run --rm -p 8000:8000 --env-file .env carclinch-bg-removal-api:local
```

## Clean Up

To remove all provisioned Azure resources and avoid ongoing costs, run the following from the Terraform folder:

```bash
cd infrastructure
terraform destroy
```

Type `yes` when prompted.

This removes:
- Resource Group
- Storage Account
- Blob Container
- Azure Container Registry
- Log Analytics Workspace
- Container Apps Environment
- Container App

### Optional local clean up

Remove the local Docker image:

```bash
docker rmi carclinch-bg-removal-api:local
```

If you built and pushed with `buildx`, you can also remove the local builder:

```bash
docker buildx rm carclinch-builder || true
```

If you want to clear the exported shell variables:

```bash
unset AZURE_STORAGE_ACCOUNT_NAME
unset AZURE_STORAGE_ACCOUNT_KEY
unset ACR_LOGIN_SERVER
```

### Verify Azure resources are gone

```bash
az group show --name rg-carclinch-dev
```

If the resource group was destroyed successfully, Azure will return a not found error.