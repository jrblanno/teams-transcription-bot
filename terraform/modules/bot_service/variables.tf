variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region for the Bot Service"
  type        = string
}

variable "name_prefix" {
  description = "Name prefix for the Bot Service"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "bot_app_id" {
  description = "Bot application ID from Azure AD app registration"
  type        = string
  sensitive   = true
}

variable "bot_app_password" {
  description = "Bot application password from Azure AD app registration"
  type        = string
  sensitive   = true
}

variable "messaging_endpoint" {
  description = "HTTPS messaging endpoint for the bot"
  type        = string
  validation {
    condition     = can(regex("^https://", var.messaging_endpoint))
    error_message = "Messaging endpoint must be an HTTPS URL."
  }
}

variable "display_name" {
  description = "Display name for the bot"
  type        = string
  default     = ""
}

variable "description" {
  description = "Description of the bot"
  type        = string
  default     = "Teams Meeting Transcription Bot - Provides real-time transcription with speaker diarization"
}

variable "icon_url" {
  description = "Icon URL for the bot"
  type        = string
  default     = ""
}

variable "sku" {
  description = "SKU for the Bot Service"
  type        = string
  default     = "F0"
  validation {
    condition     = contains(["F0", "S1"], var.sku)
    error_message = "Bot Service SKU must be either F0 (free) or S1 (standard)."
  }
}

variable "enable_teams_channel" {
  description = "Whether to enable Microsoft Teams channel"
  type        = bool
  default     = true
}

variable "enable_webchat_channel" {
  description = "Whether to enable Web Chat channel for testing"
  type        = bool
  default     = true
}

variable "enable_directline_channel" {
  description = "Whether to enable Direct Line channel"
  type        = bool
  default     = false
}

variable "directline_sites" {
  description = "Direct Line sites configuration"
  type = list(object({
    name                            = string
    enabled                         = bool
    v1_allowed                      = bool
    v3_allowed                      = bool
    enhanced_authentication_enabled = bool
    trusted_origins                 = list(string)
  }))
  default = []
}

variable "enable_analytics" {
  description = "Whether to enable analytics for the bot"
  type        = bool
  default     = true
}

variable "cmk_key_vault_key_id" {
  description = "Customer managed key from Key Vault for encryption"
  type        = string
  default     = null
}

variable "public_network_access_enabled" {
  description = "Whether public network access is enabled"
  type        = bool
  default     = true
}

variable "streaming_endpoint_enabled" {
  description = "Whether streaming endpoint is enabled"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags to apply to the Bot Service"
  type        = map(string)
  default     = {}
}