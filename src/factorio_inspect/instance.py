"""Factorio instance management for sandbox environments."""

from typing import Dict, List, Optional, Any
import asyncio
import docker
import importlib.resources
from pathlib import Path
from .config import FactorioConfig


class FactorioInstance:
    """Manages a single Factorio server instance with Docker containerization."""
    
    def __init__(self, config: FactorioConfig, instance_id: str):
        """Initialize a Factorio instance with configuration."""
        self.config = config
        self.instance_id = instance_id
        self.container: Optional[docker.models.containers.Container] = None
        self.docker_client: Optional[docker.DockerClient] = None
        self._initialized = False
    
    @staticmethod
    def get_fle_scenario_path(scenario_name: str) -> str:
        """Get absolute path to FLE scenario using importlib.resources."""
        fle_package = importlib.resources.files("fle")
        scenario_path = fle_package / "cluster" / "scenarios" / scenario_name
        
        # Convert to absolute path
        with importlib.resources.as_file(scenario_path) as resolved_path:
            return str(Path(resolved_path).resolve())
    
    async def start(self) -> None:
        """Start the Factorio server container."""
        if self._initialized:
            return
        
        # Initialize Docker client
        self.docker_client = docker.from_env()
        
        # Calculate ports for this instance
        game_port = self.config.base_port + hash(self.instance_id) % 1000
        rcon_port = self.config.rcon_port + hash(self.instance_id) % 1000
        
        container_name = f"{self.config.container_name_prefix}-{self.instance_id}"
        
        # Docker run configuration
        run_config = {
            "image": self.config.docker_image,
            "name": container_name,
            "entrypoint": "",
            "command": [
                "/opt/factorio/bin/x64/factorio",
                "--start-server-load-scenario", "default_lab_scenario",
                "--port", "34197",
                "--rcon-port", "27015",
                "--rcon-password", "factorio"
            ],
            "ports": {
                "34197/udp": game_port,
                "27015/tcp": rcon_port
            },
            "volumes": {
                self.get_fle_scenario_path("default_lab_scenario"): {"bind": "/opt/factorio/scenarios/default_lab_scenario", "mode": "ro"},
                self.get_fle_scenario_path("open_world"): {"bind": "/opt/factorio/scenarios/open_world", "mode": "ro"}
            },
            "environment": {
                "FACTORIO_SERVER_NAME": f"Inspect-AI-{self.instance_id}",
                "FACTORIO_VISIBILITY": "lan" if not self.config.headless else "hidden"
            },
            "mem_limit": self.config.memory_limit,
            "cpu_count": int(self.config.cpu_limit),
            "detach": True,
            "remove": False
        }
        
        try:
            # Start the container
            self.container = self.docker_client.containers.run(**run_config)
            
            # Wait for container to be ready
            await self._wait_for_ready()
            
            self._initialized = True
            
        except Exception as e:
            if self.container:
                try:
                    self.container.remove(force=True)
                except Exception:
                    pass
            raise RuntimeError(f"Failed to start Factorio instance {self.instance_id}: {e}")
    
    async def stop(self) -> None:
        """Stop the Factorio server container."""
        if not self._initialized or not self.container:
            return
        
        try:
            self.container.stop(timeout=10)
            self.container.remove()
            self.container = None
        except Exception as e:
            # Try force remove if stop fails
            try:
                if self.container:
                    self.container.remove(force=True)
                self.container = None
            except Exception:
                pass
            raise RuntimeError(f"Failed to stop Factorio instance {self.instance_id}: {e}")
        finally:
            self._initialized = False
            if self.docker_client:
                self.docker_client.close()
                self.docker_client = None
    
    async def execute_python_code(self, _code: str, _timeout: Optional[float] = None) -> str:
        """Execute Python code in the Factorio environment via REPL."""
        raise NotImplementedError("execute_python_code method not implemented yet")
    
    async def execute_tool(self, _tool_name: str, _args: Dict[str, Any]) -> Any:
        """Execute a Factorio API tool with given arguments."""
        raise NotImplementedError("execute_tool method not implemented yet")
    
    async def get_game_state(self) -> Dict[str, Any]:
        """Get current game state information."""
        raise NotImplementedError("get_game_state method not implemented yet")
    
    async def reset_game_state(self, _scenario: Optional[str] = None) -> None:
        """Reset the game to initial state or load a scenario."""
        raise NotImplementedError("reset_game_state method not implemented yet")
    
    async def health_check(self) -> bool:
        """Check if the Factorio instance is healthy and responsive."""
        raise NotImplementedError("health_check method not implemented yet")
    
    async def get_logs(self, _lines: int = 100) -> List[str]:
        """Get recent log lines from the Factorio server."""
        raise NotImplementedError("get_logs method not implemented yet")
    
    @property
    def is_running(self) -> bool:
        """Check if the instance is currently running."""
        if not self._initialized or not self.container:
            return False
        
        try:
            self.container.reload()
            return self.container.status == "running"
        except Exception:
            return False
    
    @property
    def connection_info(self) -> Dict[str, Any]:
        """Get connection information for the instance."""
        raise NotImplementedError("connection_info property not implemented yet")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Async context manager exit."""
        await self.stop()
    
    async def _wait_for_ready(self, max_attempts: int = 30) -> None:
        """Wait for the Factorio container to be ready."""
        for attempt in range(max_attempts):
            if not self.container:
                raise RuntimeError("Container not available")
            
            try:
                self.container.reload()
                if attempt % 5 == 0:  # Only print every 5 attempts to reduce noise
                    print(f"Attempt {attempt}: Container status: {self.container.status}")
                
                if self.container.status == "running":
                    # Container is running, wait a bit more for Factorio to initialize
                    print("Container is running, waiting for Factorio to initialize...")
                    await asyncio.sleep(2)
                    return
                elif self.container.status == "exited":
                    # Container exited, check logs
                    logs = self.container.logs().decode()
                    raise RuntimeError(f"Container exited. Logs: {logs}")
            except Exception as e:
                if attempt % 10 == 0:  # Only print errors occasionally
                    print(f"Exception during readiness check: {e}")
            
            await asyncio.sleep(1)
        
        raise RuntimeError(f"Factorio container failed to become ready after {max_attempts} attempts")