# Local configuration values
locals {
  app_service_plan_name = "${var.name_prefix}-${var.random_suffix}-plan"
  app_service_name      = "${var.name_prefix}-${var.random_suffix}-app"

  # Environment-specific settings
  always_on = var.always_on != null ? var.always_on : (
    var.environment == "prod" ? true :
    var.environment == "staging" ? true :
    false
  )

  # Python runtime string for Linux App Service
  python_runtime = "PYTHON|${var.python_version}"

  # Default app settings that will be merged with user-provided settings
  default_app_settings = {
    # Python-specific settings
    "PYTHONPATH"                     = "/home/site/wwwroot"
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "1"
    "ENABLE_ORYX_BUILD"              = "true"

    # Bot Framework settings
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"

    # Performance settings
    "WEBSITE_DYNAMIC_CACHE"      = "0"
    "WEBSITE_LOCAL_CACHE_OPTION" = "Never"

    # Environment identification
    "ENVIRONMENT"           = var.environment
    "AZURE_SUBSCRIPTION_ID" = data.azurerm_client_config.current.subscription_id
    "AZURE_TENANT_ID"       = data.azurerm_client_config.current.tenant_id
    "AZURE_RESOURCE_GROUP"  = var.resource_group_name

    # Storage configuration
    "STORAGE_ACCOUNT_NAME" = var.storage_account_name

    # Application Insights
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = "InstrumentationKey=${var.application_insights_key}"
    "APPINSIGHTS_INSTRUMENTATIONKEY"        = var.application_insights_key

    # Key Vault reference format (will be populated by specific services)
    # These will be overridden with actual Key Vault references
    "BOT_APP_ID"            = "@Microsoft.KeyVault(VaultName=${split("/", var.key_vault_id)[8]};SecretName=bot-app-id)"
    "BOT_APP_PASSWORD"      = "@Microsoft.KeyVault(VaultName=${split("/", var.key_vault_id)[8]};SecretName=bot-app-password)"
    "AZURE_CLIENT_ID"       = "@Microsoft.KeyVault(VaultName=${split("/", var.key_vault_id)[8]};SecretName=azure-client-id)"
    "AZURE_CLIENT_SECRET"   = "@Microsoft.KeyVault(VaultName=${split("/", var.key_vault_id)[8]};SecretName=azure-client-secret)"
    "AZURE_SPEECH_KEY"      = "@Microsoft.KeyVault(VaultName=${split("/", var.key_vault_id)[8]};SecretName=azure-speech-key)"
    "AZURE_SPEECH_REGION"   = "@Microsoft.KeyVault(VaultName=${split("/", var.key_vault_id)[8]};SecretName=azure-speech-region)"
    "AZURE_SPEECH_ENDPOINT" = "@Microsoft.KeyVault(VaultName=${split("/", var.key_vault_id)[8]};SecretName=azure-speech-endpoint)"

    # Key Vault URI for application use
    "KEY_VAULT_URI" = "https://${split("/", var.key_vault_id)[8]}.vault.azure.net/"
  }

  # Merge default and custom app settings
  final_app_settings = merge(local.default_app_settings, var.app_settings)
}

# Get current Azure client configuration
data "azurerm_client_config" "current" {}

# App Service Plan
resource "azurerm_service_plan" "main" {
  name                = local.app_service_plan_name
  location            = var.location
  resource_group_name = var.resource_group_name
  os_type             = var.os_type
  sku_name            = var.sku_name

  # Worker count for scaling (can be adjusted based on environment)
  worker_count = var.environment == "prod" ? 2 : 1

  tags = merge(var.tags, {
    Component = "AppServicePlan"
    OS        = var.os_type
    SKU       = var.sku_name
  })
}

# App Service with system-assigned managed identity
resource "azurerm_linux_web_app" "main" {
  name                = local.app_service_name
  location            = var.location
  resource_group_name = var.resource_group_name
  service_plan_id     = azurerm_service_plan.main.id

  # Security settings
  https_only                    = var.enable_https_only
  client_affinity_enabled       = var.enable_client_affinity
  public_network_access_enabled = true

  # System-assigned managed identity for secure access to Azure resources
  identity {
    type = "SystemAssigned"
  }

  # Application configuration
  app_settings = local.final_app_settings

  # Connection strings
  dynamic "connection_string" {
    for_each = var.connection_strings
    content {
      name  = connection_string.key
      type  = connection_string.value.type
      value = connection_string.value.value
    }
  }

  # Site configuration for Python
  site_config {
    # Python runtime configuration
    application_stack {
      python_version = var.python_version
    }

    # Always on setting (important for production bots)
    always_on = local.always_on

    # Security settings
    minimum_tls_version = var.minimum_tls_version
    ftps_state          = "Disabled" # Disable FTP for security
    http2_enabled       = true

    # Health check settings
    health_check_path                 = "/health"
    health_check_eviction_time_in_min = 2

    # Logging configuration (removed detailed_error_logging_enabled - not supported)

    # Note: Application logs are configured at the app level, not in site_config

    # Note: HTTP logging is configured at the app service level, not in site_config

    # CORS settings (if needed for bot testing tools)
    cors {
      allowed_origins     = var.environment == "prod" ? [] : ["https://botframework.com", "https://chatbot.botframework.com"]
      support_credentials = false
    }

    # Default documents
    default_documents = ["index.html", "Default.htm", "Default.html"]

    # Use 32-bit worker process for Basic tiers
    use_32_bit_worker = contains(["B1", "B2", "B3"], var.sku_name)

    # Auto-heal settings for production
    dynamic "auto_heal_setting" {
      for_each = var.environment == "prod" ? [1] : []
      content {
        action {
          action_type = "Recycle"
        }
        trigger {
          requests {
            count    = 100
            interval = "00:01:00"
          }
          slow_request {
            count      = 10
            interval   = "00:01:00"
            time_taken = "00:01:00"
          }
        }
      }
    }
  }

  # VNet integration (if subnet provided)
  dynamic "site_config" {
    for_each = var.subnet_id != null ? [1] : []
    content {
      vnet_route_all_enabled = true
    }
  }

  tags = merge(var.tags, {
    Component   = "AppService"
    Runtime     = "Python"
    Version     = var.python_version
    Environment = var.environment
  })

  lifecycle {
    # Ignore changes to app_settings that might be updated by deployment
    ignore_changes = [
      app_settings["WEBSITE_RUN_FROM_PACKAGE"],
      app_settings["SCM_REPOSITORY_PATH"],
    ]
  }
}

# VNet integration (if subnet provided)
resource "azurerm_app_service_virtual_network_swift_connection" "main" {
  count          = var.subnet_id != null ? 1 : 0
  app_service_id = azurerm_linux_web_app.main.id
  subnet_id      = var.subnet_id
}

# Note: Backup configuration for Linux Web Apps requires different approach
# Using deployment slots and git-based deployment for backup strategy
# Backup configuration would be handled at the infrastructure level

# Custom domain binding (can be added if needed)
# resource "azurerm_app_service_custom_hostname_binding" "main" {
#   hostname            = var.custom_domain
#   app_service_name    = azurerm_linux_web_app.main.name
#   resource_group_name = var.resource_group_name
# }

# Note: Availability tests are handled in the monitoring module

# Note: Diagnostic settings will be configured separately to avoid validation issues