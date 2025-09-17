# Local configuration values
locals {
  log_analytics_workspace_name = "${var.name_prefix}-${var.random_suffix}-law"
  application_insights_name    = "${var.name_prefix}-${var.random_suffix}-ai"
  action_group_name            = "${var.name_prefix}-${var.random_suffix}-ag"

  # Environment-specific configurations
  retention_in_days = var.environment == "prod" ? 365 : (
    var.environment == "staging" ? 180 : 90
  )

  workspace_retention = var.environment == "prod" ? 90 : (
    var.environment == "staging" ? 60 : 30
  )

  # Data cap based on environment
  daily_data_cap = var.daily_data_cap_in_gb != null ? var.daily_data_cap_in_gb : (
    var.environment == "prod" ? null : (
      var.environment == "staging" ? 5 : 1
    )
  )
}

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "main" {
  name                = local.log_analytics_workspace_name
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = var.workspace_sku
  retention_in_days   = var.workspace_retention_in_days != null ? var.workspace_retention_in_days : local.workspace_retention

  # Data ingestion settings
  daily_quota_gb                     = var.workspace_daily_quota_gb
  internet_ingestion_enabled         = true
  internet_query_enabled             = true
  reservation_capacity_in_gb_per_day = var.workspace_sku == "CapacityReservation" ? 100 : null

  tags = merge(var.tags, {
    Component = "LogAnalytics"
    Purpose   = "Centralized Logging"
  })

}

# Application Insights
resource "azurerm_application_insights" "main" {
  name                = local.application_insights_name
  location            = var.location
  resource_group_name = var.resource_group_name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = var.application_type

  # Data retention and sampling
  retention_in_days                     = local.retention_in_days
  daily_data_cap_in_gb                  = local.daily_data_cap
  daily_data_cap_notifications_disabled = var.daily_data_cap_notifications_disabled
  sampling_percentage                   = var.sampling_percentage

  # Privacy settings
  disable_ip_masking = var.disable_ip_masking

  # Integration settings
  internet_ingestion_enabled = true
  internet_query_enabled     = true

  tags = merge(var.tags, {
    Component  = "ApplicationInsights"
    Purpose    = "Application Monitoring"
    AppService = var.app_service_name
  })

  depends_on = [azurerm_log_analytics_workspace.main]
}

# Store Application Insights instrumentation key in Key Vault
resource "azurerm_key_vault_secret" "app_insights_key" {
  name         = "application-insights-instrumentation-key"
  value        = azurerm_application_insights.main.instrumentation_key
  key_vault_id = var.key_vault_id

  content_type = "application/x-api-key"

  tags = merge(var.tags, {
    Service     = "ApplicationInsights"
    KeyType     = "InstrumentationKey"
    GeneratedBy = "terraform"
  })
}

# Store Application Insights connection string in Key Vault
resource "azurerm_key_vault_secret" "app_insights_connection_string" {
  name         = "application-insights-connection-string"
  value        = azurerm_application_insights.main.connection_string
  key_vault_id = var.key_vault_id

  content_type = "text/connection-string"

  tags = merge(var.tags, {
    Service     = "ApplicationInsights"
    KeyType     = "ConnectionString"
    GeneratedBy = "terraform"
  })
}

# Log Analytics Solutions
resource "azurerm_log_analytics_solution" "solutions" {
  for_each = var.enable_log_analytics_solutions ? toset(var.solutions) : []

  solution_name         = each.value
  location              = var.location
  resource_group_name   = var.resource_group_name
  workspace_resource_id = azurerm_log_analytics_workspace.main.id
  workspace_name        = azurerm_log_analytics_workspace.main.name

  plan {
    publisher = "Microsoft"
    product   = "OMSGallery/${each.value}"
  }

  depends_on = [azurerm_log_analytics_workspace.main]
}

# Action Group for Alerts
resource "azurerm_monitor_action_group" "main" {
  count               = var.enable_action_groups ? 1 : 0
  name                = local.action_group_name
  resource_group_name = var.resource_group_name
  short_name          = substr(replace(var.name_prefix, "-", ""), 0, 12)

  # Email notification
  dynamic "email_receiver" {
    for_each = var.notification_email != "" ? [1] : []
    content {
      name          = "email-admin"
      email_address = var.notification_email
    }
  }

  # Webhook notification (e.g., Slack, Teams)
  dynamic "webhook_receiver" {
    for_each = var.webhook_url != "" ? [1] : []
    content {
      name                    = "webhook-notification"
      service_uri             = var.webhook_url
      use_common_alert_schema = true
    }
  }

  tags = var.tags
}

# Availability Test
resource "azurerm_application_insights_web_test" "main" {
  count                   = var.enable_availability_tests ? 1 : 0
  name                    = "${var.app_service_name}-availability-test"
  location                = var.location
  resource_group_name     = var.resource_group_name
  application_insights_id = azurerm_application_insights.main.id
  kind                    = "ping"
  frequency               = 300 # 5 minutes
  timeout                 = 30
  enabled                 = true
  retry_enabled           = true
  geo_locations           = var.availability_test_locations

  configuration = <<XML
<WebTest Name="${var.app_service_name}-availability-test" Id="ABD48585-0831-40CB-9069-682EA6BB3583" Enabled="True" CssProjectStructure="" CssIteration="" Timeout="30" WorkItemIds="" xmlns="http://microsoft.com/schemas/VisualStudio/TeamTest/2010" Description="" CredentialUserName="" CredentialPassword="" PreAuthenticate="True" Proxy="default" StopOnError="False" RecordedResultFile="" ResultsLocale="">
  <Items>
    <Request Method="GET" Guid="a5f10126-e4cd-570d-961c-cea43999a200" Version="1.1" Url="https://${var.app_service_name}.azurewebsites.net/health" ThinkTime="0" Timeout="30" ParseDependentRequests="True" FollowRedirects="True" RecordResult="True" Cache="False" ResponseTimeGoal="0" Encoding="utf-8" ExpectedHttpStatusCode="200" ExpectedResponseUrl="" ReportingName="" IgnoreHttpStatusCode="False" />
  </Items>
</WebTest>
XML

  tags = var.tags

  depends_on = [azurerm_application_insights.main]
}

# Metric Alerts
resource "azurerm_monitor_metric_alert" "app_service_cpu" {
  count               = var.enable_action_groups ? 1 : 0
  name                = "${var.app_service_name}-high-cpu"
  resource_group_name = var.resource_group_name
  scopes              = ["/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${var.resource_group_name}/providers/Microsoft.Web/sites/${var.app_service_name}"]
  description         = "High CPU usage alert for ${var.app_service_name}"
  severity            = 2
  frequency           = "PT5M"
  window_size         = "PT15M"
  enabled             = true

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "CpuPercentage"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = var.environment == "prod" ? 80 : 90
  }

  action {
    action_group_id = azurerm_monitor_action_group.main[0].id
  }

  tags = var.tags
}

resource "azurerm_monitor_metric_alert" "app_service_memory" {
  count               = var.enable_action_groups ? 1 : 0
  name                = "${var.app_service_name}-high-memory"
  resource_group_name = var.resource_group_name
  scopes              = ["/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${var.resource_group_name}/providers/Microsoft.Web/sites/${var.app_service_name}"]
  description         = "High memory usage alert for ${var.app_service_name}"
  severity            = 2
  frequency           = "PT5M"
  window_size         = "PT15M"
  enabled             = true

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "MemoryPercentage"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = var.environment == "prod" ? 85 : 95
  }

  action {
    action_group_id = azurerm_monitor_action_group.main[0].id
  }

  tags = var.tags
}

resource "azurerm_monitor_metric_alert" "app_service_response_time" {
  count               = var.enable_action_groups ? 1 : 0
  name                = "${var.app_service_name}-slow-response"
  resource_group_name = var.resource_group_name
  scopes              = ["/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${var.resource_group_name}/providers/Microsoft.Web/sites/${var.app_service_name}"]
  description         = "Slow response time alert for ${var.app_service_name}"
  severity            = 3
  frequency           = "PT5M"
  window_size         = "PT15M"
  enabled             = true

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "AverageResponseTime"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = var.environment == "prod" ? 5 : 10 # seconds
  }

  action {
    action_group_id = azurerm_monitor_action_group.main[0].id
  }

  tags = var.tags
}

# Availability Test Alert
resource "azurerm_monitor_metric_alert" "availability_test" {
  count               = var.enable_availability_tests && var.enable_action_groups ? 1 : 0
  name                = "${var.app_service_name}-availability-failure"
  resource_group_name = var.resource_group_name
  scopes              = [azurerm_application_insights_web_test.main[0].id]
  description         = "Availability test failure alert for ${var.app_service_name}"
  severity            = 1 # High severity for availability issues
  frequency           = "PT1M"
  window_size         = "PT5M"
  enabled             = true

  criteria {
    metric_namespace = "Microsoft.Insights/webtests"
    metric_name      = "availabilityResults/availabilityPercentage"
    aggregation      = "Average"
    operator         = "LessThan"
    threshold        = 90 # Less than 90% availability triggers alert
  }

  action {
    action_group_id = azurerm_monitor_action_group.main[0].id
  }

  tags = var.tags

  depends_on = [azurerm_application_insights_web_test.main]
}

# Get current Azure client configuration
data "azurerm_client_config" "current" {}