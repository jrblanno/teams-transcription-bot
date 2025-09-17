"""
Test project structure and setup validation
"""
import os
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent


class TestProjectStructure:
    """Validate project structure follows the defined architecture"""

    def test_root_files_exist(self):
        """Test that essential root files exist"""
        required_files = [
            "README.md",
            "requirements.txt",
            "setup.py",
            ".gitignore",
        ]

        for file_name in required_files:
            file_path = PROJECT_ROOT / file_name
            assert file_path.exists(), f"Required file {file_name} does not exist"

    def test_src_directory_structure(self):
        """Test that src directory has proper module structure"""
        src_path = PROJECT_ROOT / "src"
        assert src_path.exists(), "src directory does not exist"
        assert src_path.is_dir(), "src must be a directory"

        # Check for __init__.py in src
        assert (src_path / "__init__.py").exists(), "src/__init__.py does not exist"

        # Check required modules
        required_modules = [
            "bot",
            "audio",
            "transcription",
            "graph_api"
        ]

        for module_name in required_modules:
            module_path = src_path / module_name
            assert module_path.exists(), f"Module {module_name} does not exist"
            assert module_path.is_dir(), f"{module_name} must be a directory"
            assert (module_path / "__init__.py").exists(), f"{module_name}/__init__.py does not exist"

    def test_terraform_directory_exists(self):
        """Test that terraform directory exists"""
        terraform_path = PROJECT_ROOT / "terraform"
        assert terraform_path.exists(), "terraform directory does not exist"
        assert terraform_path.is_dir(), "terraform must be a directory"

    def test_tests_directory_structure(self):
        """Test that tests directory exists and is properly structured"""
        tests_path = PROJECT_ROOT / "tests"
        assert tests_path.exists(), "tests directory does not exist"
        assert tests_path.is_dir(), "tests must be a directory"
        assert (tests_path / "__init__.py").exists(), "tests/__init__.py does not exist"

    def test_python_package_importable(self):
        """Test that src package is importable"""
        # Add src to path
        sys.path.insert(0, str(PROJECT_ROOT))

        try:
            import src
            assert src is not None
        except ImportError as e:
            pytest.fail(f"Cannot import src package: {e}")

    def test_setup_py_valid(self):
        """Test that setup.py contains valid package configuration"""
        setup_path = PROJECT_ROOT / "setup.py"
        assert setup_path.exists(), "setup.py does not exist"

        # Read and validate basic structure
        with open(setup_path, 'r') as f:
            content = f.read()
            assert "setup(" in content, "setup.py must contain setup() call"
            assert "name=" in content, "setup.py must define package name"
            assert "version=" in content, "setup.py must define version"
            assert "packages=" in content or "find_packages()" in content, "setup.py must define packages"

    def test_requirements_txt_valid(self):
        """Test that requirements.txt contains required dependencies"""
        req_path = PROJECT_ROOT / "requirements.txt"
        assert req_path.exists(), "requirements.txt does not exist"

        with open(req_path, 'r') as f:
            content = f.read()

        # Check for essential dependencies mentioned in the issue
        required_packages = [
            "botbuilder-core",
            "botbuilder-schema",
            "msal",
            "azure-cognitiveservices-speech",
            "azure-storage-blob",
            "aiohttp",
            "python-dotenv",
            "pytest",
        ]

        for package in required_packages:
            assert package in content, f"Required package {package} not in requirements.txt"

    def test_gitignore_configured(self):
        """Test that .gitignore is properly configured for Python projects"""
        gitignore_path = PROJECT_ROOT / ".gitignore"
        assert gitignore_path.exists(), ".gitignore does not exist"

        with open(gitignore_path, 'r') as f:
            content = f.read()

        # Check for Python-specific ignores
        python_ignores = [
            "__pycache__",
            "*.pyc",
            ".env",
            "venv",
            ".pytest_cache",
        ]

        for ignore_pattern in python_ignores:
            assert ignore_pattern in content, f"Pattern {ignore_pattern} not in .gitignore"


class TestModuleInitialization:
    """Test that modules are properly initialized"""

    def test_bot_module_structure(self):
        """Test bot module has expected structure"""
        bot_path = PROJECT_ROOT / "src" / "bot"
        assert bot_path.exists(), "bot module does not exist"

        # Bot module should be importable
        sys.path.insert(0, str(PROJECT_ROOT))
        try:
            import src.bot
            assert src.bot is not None
        except ImportError as e:
            pytest.fail(f"Cannot import bot module: {e}")

    def test_audio_module_structure(self):
        """Test audio module has expected structure"""
        audio_path = PROJECT_ROOT / "src" / "audio"
        assert audio_path.exists(), "audio module does not exist"

        # Audio module should be importable
        sys.path.insert(0, str(PROJECT_ROOT))
        try:
            import src.audio
            assert src.audio is not None
        except ImportError as e:
            pytest.fail(f"Cannot import audio module: {e}")

    def test_transcription_module_structure(self):
        """Test transcription module has expected structure"""
        transcription_path = PROJECT_ROOT / "src" / "transcription"
        assert transcription_path.exists(), "transcription module does not exist"

        # Transcription module should be importable
        sys.path.insert(0, str(PROJECT_ROOT))
        try:
            import src.transcription
            assert src.transcription is not None
        except ImportError as e:
            pytest.fail(f"Cannot import transcription module: {e}")

    def test_graph_api_module_structure(self):
        """Test graph_api module has expected structure"""
        graph_api_path = PROJECT_ROOT / "src" / "graph_api"
        assert graph_api_path.exists(), "graph_api module does not exist"

        # Graph API module should be importable
        sys.path.insert(0, str(PROJECT_ROOT))
        try:
            import src.graph_api
            assert src.graph_api is not None
        except ImportError as e:
            pytest.fail(f"Cannot import graph_api module: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])