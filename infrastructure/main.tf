resource "random_string" "storage_suffix" {
  length  = 6
  upper   = false
  special = false
  numeric = true
}

resource "azurerm_resource_group" "this" {
  name     = "rg-${var.project_name}-${var.environment}"
  location = var.location
}

resource "azurerm_storage_account" "this" {
  name                     = "${var.project_name}${var.environment}${random_string.storage_suffix.result}"
  resource_group_name      = azurerm_resource_group.this.name
  location                 = azurerm_resource_group.this.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  min_tls_version                 = "TLS1_2"
  public_network_access_enabled   = true
  allow_nested_items_to_be_public = false
}

resource "azurerm_storage_container" "processed_images" {
  name                  = "processed-images"
  storage_account_id    = azurerm_storage_account.this.id
  container_access_type = "private"
}

resource "random_string" "acr_suffix" {
  length  = 6
  upper   = false
  special = false
  numeric = true
}

resource "azurerm_container_registry" "this" {
  name                = "${var.acr_name_prefix}${var.environment}${random_string.acr_suffix.result}"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  sku                 = "Basic"
  admin_enabled       = true
}

resource "azurerm_log_analytics_workspace" "this" {
  name                = "law-${var.project_name}-${var.environment}"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_container_app_environment" "this" {
  name                       = "cae-${var.project_name}-${var.environment}"
  location                   = azurerm_resource_group.this.location
  resource_group_name        = azurerm_resource_group.this.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id
}

resource "azurerm_container_app" "api" {
  name                         = "ca-${var.project_name}-${var.environment}"
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = azurerm_resource_group.this.name
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  registry {
    server               = azurerm_container_registry.this.login_server
    username             = azurerm_container_registry.this.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.this.admin_password
  }

  secret {
    name  = "blob-account-name"
    value = azurerm_storage_account.this.name
  }

  secret {
    name  = "blob-account-key"
    value = azurerm_storage_account.this.primary_access_key
  }

  secret {
    name  = "blob-container-name"
    value = azurerm_storage_container.processed_images.name
  }

  ingress {
    external_enabled = true
    target_port      = 8000

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 1
    max_replicas = 3

    container {
      name   = "api"
      image  = "${azurerm_container_registry.this.login_server}/carclinch-bg-removal-api:latest"
      cpu    = 2.0
      memory = "4Gi"

      env {
        name        = "AZURE_STORAGE_ACCOUNT_NAME"
        secret_name = "blob-account-name"
      }

      env {
        name        = "AZURE_STORAGE_ACCOUNT_KEY"
        secret_name = "blob-account-key"
      }

      env {
        name        = "AZURE_STORAGE_CONTAINER_NAME"
        secret_name = "blob-container-name"
      }

      env {
        name  = "IMAGE_BASE_DIR"
        value = "images"
      }
    }
  }
}
