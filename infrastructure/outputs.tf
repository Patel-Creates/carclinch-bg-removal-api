output "resource_group_name" {
  value = azurerm_resource_group.this.name
}

output "storage_account_name" {
  value = azurerm_storage_account.this.name
}

output "processed_images_container_name" {
  value = azurerm_storage_container.processed_images.name
}

output "blob_endpoint" {
  value = azurerm_storage_account.this.primary_blob_endpoint
}

output "acr_name" {
  value = azurerm_container_registry.this.name
}

output "acr_login_server" {
  value = azurerm_container_registry.this.login_server
}

output "acr_admin_username" {
  value     = azurerm_container_registry.this.admin_username
  sensitive = true
}

output "acr_admin_password" {
  value     = azurerm_container_registry.this.admin_password
  sensitive = true
}

output "container_app_url" {
  value = azurerm_container_app.api.ingress[0].fqdn
}
