"""Configuration classes for Factorio-Inspect AI integration."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class FactorioConfig(BaseModel):
    """Configuration for Factorio sandbox environment."""
    
    # Docker configuration
    docker_image: str = Field(default="factorio:latest", description="Docker image to use")
    container_name_prefix: str = Field(default="factorio-inspect", description="Prefix for container names")
    
    # Network configuration
    base_port: int = Field(default=34197, description="Base UDP port for Factorio servers")
    rcon_port: int = Field(default=27015, description="Base TCP port for RCON")
    rcon_password: str = Field(default="factorio", description="Password for RCON connections")
    port_range: int = Field(default=100, description="Range of ports to use for multiple instances")
    
    # Game configuration
    headless: bool = Field(default=True, description="Run Factorio server in headless mode")
    default_scenario: Optional[str] = Field(default=None, description="Default scenario to load")
    save_file: Optional[str] = Field(default=None, description="Save file to load on startup")
    
    # Execution configuration
    timeout: float = Field(default=300.0, description="Default timeout for operations in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries for failed operations")
    health_check_interval: float = Field(default=30.0, description="Health check interval in seconds")
    
    # Resource limits
    memory_limit: str = Field(default="2g", description="Docker memory limit")
    cpu_limit: float = Field(default=2.0, description="Docker CPU limit")
    
    # Logging configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    
    # Advanced options
    enable_mods: bool = Field(default=False, description="Enable mod support")
    # Note: These fields are simplified to make the config hashable
    # For complex configurations, consider creating specialized config objects
    
    class Config:
        """Pydantic configuration."""
        extra = "forbid"
        frozen = True  # Make the model immutable and hashable


class FactorioToolConfig(BaseModel):
    """Configuration for Factorio API tools."""
    
    tool_name: str = Field(description="Name of the tool")
    enabled: bool = Field(default=True, description="Whether the tool is enabled")
    timeout: float = Field(default=30.0, description="Tool execution timeout")
    max_retries: int = Field(default=2, description="Maximum retries for tool execution")
    
    class Config:
        """Pydantic configuration."""
        extra = "forbid"
        frozen = True


class FactorioEvaluationConfig(BaseModel):
    """Configuration for evaluation scenarios."""
    
    scenario_name: str = Field(description="Name of the evaluation scenario")
    description: Optional[str] = Field(default=None, description="Description of the scenario")
    initial_state: Dict[str, Any] = Field(default_factory=dict, description="Initial game state")
    success_criteria: Dict[str, Any] = Field(default_factory=dict, description="Success criteria")
    time_limit: Optional[float] = Field(default=None, description="Time limit for the scenario")
    
    class Config:
        """Pydantic configuration."""
        extra = "forbid"
        frozen = True