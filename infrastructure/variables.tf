variable "project_name" {
  type        = string
  description = "Short project name used in naming resources"
  default     = "carclinch"
}

variable "environment" {
  type        = string
  description = "Environment name"
  default     = "dev"
}

variable "location" {
  type        = string
  description = "Azure region"
  default     = "southafricanorth"
}
variable "acr_name_prefix" {
  type        = string
  description = "Short prefix for ACR name"
  default     = "carclinch"
}