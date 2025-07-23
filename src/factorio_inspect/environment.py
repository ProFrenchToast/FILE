"""Factorio Sandbox Environment for Inspect AI integration."""

import time
from typing import Dict, List, Optional, Any

from inspect_ai.util import ExecResult, SandboxEnvironment, SandboxEnvironmentSpec, sandboxenv
from .instance import FactorioInstance
from .config import FactorioConfig


@sandboxenv("factorio")
class FactorioSandboxEnvironment(SandboxEnvironment):
    """Factorio sandbox environment for Inspect AI evaluations."""
    
    def __init__(self, instance: FactorioInstance):
        """Initialize the sandbox environment with a Factorio instance."""
        self.instance = instance
    
    async def exec(
        self,
        cmd: List[str],
        input: Optional[str] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> ExecResult[str]:
        """Execute a command in the Factorio environment."""
        if not self.instance.is_running:
            return ExecResult(
                success=False,
                returncode=1,
                stdout="",
                stderr="Factorio instance is not running"
            )
        
        # Handle Python code execution
        if len(cmd) >= 2 and cmd[0] == "python" and cmd[1] == "-c":
            if len(cmd) < 3:
                return ExecResult(
                    success=False,
                    returncode=1,
                    stdout="",
                    stderr="No Python code provided"
                )
            
            python_code = cmd[2]
            try:
                result = await self.instance.execute_python_code(
                    python_code, 
                    timeout or 30.0
                )
                return ExecResult(
                    success=True,
                    returncode=0,
                    stdout=result,
                    stderr=""
                )
            except Exception as e:
                return ExecResult(
                    success=False,
                    returncode=1,
                    stdout="",
                    stderr=str(e)
                )
        
        # Handle shell commands through container exec
        try:
            if not self.instance.container:
                raise RuntimeError("Container not available")
            
            exec_result = self.instance.container.exec_run(
                cmd,
                stdout=True,
                stderr=True,
                stdin=input is not None,
                workdir=cwd,
                environment=env or {}
            )
            
            return ExecResult(
                success=exec_result.exit_code == 0,
                returncode=exec_result.exit_code,
                stdout=exec_result.output.decode('utf-8'),
                stderr=""
            )
            
        except Exception as e:
            return ExecResult(
                success=False,
                returncode=1,
                stdout="",
                stderr=f"Execution failed: {str(e)}"
            )
    
    async def write_file(self, file: str, contents: str | bytes) -> None:
        """Write a file to the sandbox.
        
        Note: File I/O operations are not supported in Factorio game environments.
        Factorio is a game environment where interaction happens through game mechanics
        and Python code execution via RCON, not through traditional file operations.
        
        Raises:
            NotImplementedError: Always, as file operations don't have meaningful
                semantics in the Factorio game environment.
        """
        raise NotImplementedError(
            "File I/O operations are not supported in Factorio game environments. "
            "Use Python code execution instead to interact with the game world."
        )
    
    async def read_file(self, file: str, text: bool = True) -> str | bytes:
        """Read a file from the sandbox.
        
        Note: File I/O operations are not supported in Factorio game environments.
        Factorio is a game environment where interaction happens through game mechanics
        and Python code execution via RCON, not through traditional file operations.
        
        Args:
            file: The file path to read (not used)
            text: Whether to read as text or binary (not used)
            
        Raises:
            NotImplementedError: Always, as file operations don't have meaningful
                semantics in the Factorio game environment.
        """
        raise NotImplementedError(
            "File I/O operations are not supported in Factorio game environments. "
            "Use Python code execution instead to interact with the game world."
        )
    
    @classmethod
    async def task_init(
        cls,
        task_name: str,
        config: Optional[FactorioConfig] = None,
        **kwargs
    ) -> None:
        """Initialize global resources for the task.
        
        For Factorio environments, no global initialization is needed
        as each sample gets its own isolated instance.
        """
        # No global initialization needed for Factorio environments
        pass
    
    @classmethod
    async def sample_init(
        cls,
        task_name: str,
        config: Optional[FactorioConfig] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, "FactorioSandboxEnvironment"]:
        """Initialize sandbox environment for a sample.
        
        Creates a new Factorio instance with unique ID and starts it up.
        Each sample gets its own isolated Docker container and game instance.
        
        Args:
            task_name: Name of the evaluation task
            config: Factorio configuration (uses default if None)
            metadata: Optional metadata (can contain scenario info, etc.)
            **kwargs: Additional arguments (ignored)
            
        Returns:
            Dict containing the sandbox environment: {"sandbox": FactorioSandboxEnvironment}
        """
        # Use default config if none provided
        if config is None:
            config = FactorioConfig()
        
        # Create unique instance ID using task name and timestamp
        timestamp = int(time.time() * 1000)  # milliseconds for uniqueness
        instance_id = f"{task_name}-{timestamp}"
        
        # Create and start the Factorio instance
        instance = FactorioInstance(config, instance_id)
        await instance.start()
        
        # Create the sandbox environment with the instance
        environment = cls(instance)
        
        return {"sandbox": environment}
    
    @classmethod
    async def sample_cleanup(
        cls,
        task_name: str,
        config: Optional[FactorioConfig] = None,
        environments: Optional[Dict[str, "FactorioSandboxEnvironment"]] = None,
        interrupted: bool = False,
        **kwargs
    ) -> None:
        """Clean up sandbox environment after sample completion.
        
        Stops all Factorio instances in the provided environments dict.
        Handles cleanup gracefully even if some instances fail to stop.
        
        Args:
            task_name: Name of the evaluation task
            config: Factorio configuration (not used in cleanup)
            environments: Dict of environments to clean up (from sample_init)
            interrupted: Whether cleanup is due to interruption (doesn't affect behavior)
            **kwargs: Additional arguments (ignored)
        """
        if not environments:
            # Nothing to clean up
            return
        
        # Stop all instances, continuing even if some fail
        for env_name, environment in environments.items():
            try:
                await environment.instance.stop()
            except Exception as e:
                # Log the error but continue with cleanup of other instances
                # In a real implementation, we might want proper logging here
                print(f"Warning: Failed to stop instance for {env_name}: {e}")
                continue
    
    @classmethod
    async def task_cleanup(
        cls,
        task_name: str,
        config: Optional[FactorioConfig] = None,
        cleanup: bool = True
    ) -> None:
        """Clean up global resources after task completion.
        
        For Factorio environments, no global cleanup is needed
        as cleanup is handled per-sample in sample_cleanup().
        
        Args:
            task_name: Name of task using the sandbox environment
            config: Factorio configuration (optional)
            cleanup: Whether to actually cleanup resources
        """
        # No global cleanup needed for Factorio environments
        pass
    
    @classmethod
    def default_concurrency(cls) -> int | None:
        """Return default concurrency limits for Factorio environments."""
        # Factorio containers use significant resources, so limit concurrent instances
        return 3
    
    @classmethod  
    def config_deserialize(cls, config: dict) -> FactorioConfig:
        """Deserialize config from dictionary for logging/reloading."""
        return FactorioConfig(**config)