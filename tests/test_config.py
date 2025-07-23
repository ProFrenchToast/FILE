"""Tests for configuration classes."""

import pytest
from pydantic import ValidationError
from factorio_inspect.config import FactorioConfig, FactorioToolConfig, FactorioEvaluationConfig


class TestFactorioConfig:
    """Test cases for FactorioConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = FactorioConfig()
        assert config.docker_image == "factorio:latest"
        assert config.container_name_prefix == "factorio-inspect"
        assert config.base_port == 34197
        assert config.rcon_port == 27015
        assert config.headless is True
        assert config.timeout == 300.0
        assert config.max_retries == 3
        assert config.memory_limit == "2g"
        assert config.cpu_limit == 2.0
        assert config.log_level == "INFO"
        assert config.enable_mods is False
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = FactorioConfig(
            docker_image="custom/factorio:latest",
            base_port=35000,
            headless=False,
            timeout=600.0,
            enable_mods=True
        )
        assert config.docker_image == "custom/factorio:latest"
        assert config.base_port == 35000
        assert config.headless is False
        assert config.timeout == 600.0
        assert config.enable_mods is True
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Test that config accepts negative timeout (no validation constraint yet)
        config = FactorioConfig(timeout=-1.0)
        assert config.timeout == -1.0


class TestFactorioToolConfig:
    """Test cases for FactorioToolConfig."""
    
    def test_tool_config_creation(self):
        """Test tool configuration creation."""
        config = FactorioToolConfig(tool_name="inspect_inventory")
        assert config.tool_name == "inspect_inventory"
        assert config.enabled is True
        assert config.timeout == 30.0
        assert config.max_retries == 2
    
    def test_tool_config_custom_values(self):
        """Test tool configuration with custom values."""
        config = FactorioToolConfig(
            tool_name="craft_item",
            enabled=False,
            timeout=60.0,
            max_retries=5
        )
        assert config.tool_name == "craft_item"
        assert config.enabled is False
        assert config.timeout == 60.0
        assert config.max_retries == 5
    
    def test_tool_config_validation(self):
        """Test tool configuration validation."""
        # Tool name is required
        with pytest.raises(ValidationError):
            FactorioToolConfig()


class TestFactorioEvaluationConfig:
    """Test cases for FactorioEvaluationConfig."""
    
    def test_evaluation_config_creation(self):
        """Test evaluation configuration creation."""
        config = FactorioEvaluationConfig(scenario_name="basic_automation")
        assert config.scenario_name == "basic_automation"
        assert config.description is None
        assert config.initial_state == {}
        assert config.success_criteria == {}
        assert config.time_limit is None
    
    def test_evaluation_config_full(self):
        """Test evaluation configuration with all fields."""
        config = FactorioEvaluationConfig(
            scenario_name="advanced_production",
            description="Test advanced production chains",
            initial_state={"resources": {"iron": 100, "copper": 50}},
            success_criteria={"items_produced": {"science-pack-1": 10}},
            time_limit=3600.0
        )
        assert config.scenario_name == "advanced_production"
        assert config.description == "Test advanced production chains"
        assert config.initial_state == {"resources": {"iron": 100, "copper": 50}}
        assert config.success_criteria == {"items_produced": {"science-pack-1": 10}}
        assert config.time_limit == 3600.0
    
    def test_evaluation_config_validation(self):
        """Test evaluation configuration validation."""
        # Scenario name is required
        with pytest.raises(ValidationError):
            FactorioEvaluationConfig()