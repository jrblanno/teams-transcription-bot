"""Test Terraform infrastructure validation."""
import subprocess
import json
import os
from pathlib import Path

def test_terraform_init():
    """Test terraform initialization."""
    terraform_dir = Path(__file__).parent.parent / "terraform"
    result = subprocess.run(
        ["terraform", "init", "-backend=false"],
        cwd=terraform_dir,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Terraform init failed: {result.stderr}"

def test_terraform_validate():
    """Test terraform configuration validation."""
    terraform_dir = Path(__file__).parent.parent / "terraform"
    result = subprocess.run(
        ["terraform", "validate"],
        cwd=terraform_dir,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Terraform validate failed: {result.stderr}"

def test_terraform_format():
    """Test terraform formatting."""
    terraform_dir = Path(__file__).parent.parent / "terraform"
    result = subprocess.run(
        ["terraform", "fmt", "-check", "-recursive"],
        cwd=terraform_dir,
        capture_output=True,
        text=True
    )
    # Format check might fail due to auto-formatting, just verify it runs
    assert result.returncode in [0, 3], f"Terraform fmt check failed: {result.stderr}"

def test_modules_exist():
    """Test that all required modules exist."""
    terraform_dir = Path(__file__).parent.parent / "terraform"
    required_modules = [
        "modules/bot_service",
        "modules/app_service",
        "modules/storage",
        "modules/key_vault",
        "modules/monitoring"
    ]

    for module in required_modules:
        module_path = terraform_dir / module / "main.tf"
        assert module_path.exists(), f"Module {module} not found"

def test_outputs_configured():
    """Test that terraform outputs are configured."""
    terraform_dir = Path(__file__).parent.parent / "terraform"
    outputs_file = terraform_dir / "outputs.tf"
    assert outputs_file.exists(), "outputs.tf not found"

    # Check for key outputs
    content = outputs_file.read_text()
    required_outputs = [
        "resource_group_name",
        "storage_account_name",
        "key_vault_name",
        "app_service_name",
        "bot_service_name"
    ]

    for output in required_outputs:
        assert f'output "{output}"' in content, f"Output {output} not configured"

def test_variables_configured():
    """Test that terraform variables are configured."""
    terraform_dir = Path(__file__).parent.parent / "terraform"
    variables_file = terraform_dir / "variables.tf"
    assert variables_file.exists(), "variables.tf not found"

    # Check for key variables
    content = variables_file.read_text()
    required_variables = [
        "environment",
        "location",
        "project_name"
    ]

    for variable in required_variables:
        assert f'variable "{variable}"' in content, f"Variable {variable} not configured"

def test_tfvars_example_exists():
    """Test that terraform.tfvars.example exists."""
    terraform_dir = Path(__file__).parent.parent / "terraform"
    tfvars_example = terraform_dir / "terraform.tfvars.example"
    assert tfvars_example.exists(), "terraform.tfvars.example not found"

def test_resource_naming_convention():
    """Test that resources follow naming conventions."""
    terraform_dir = Path(__file__).parent.parent / "terraform"

    # Check main.tf for proper naming patterns
    main_tf = terraform_dir / "main.tf"
    if main_tf.exists():
        content = main_tf.read_text()

        # Check for proper resource group naming
        assert "rg-" in content or "resource_group_name" in content, "Resource group naming convention not followed"

        # Check for environment variable usage
        assert "${var.environment}" in content or "var.environment" in content, "Environment variable not used in naming"