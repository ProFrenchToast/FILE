"""Factorio Sandbox Environment for Inspect AI integration."""

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
        """Write a file to the sandbox."""
        raise NotImplementedError("write_file method not implemented yet")
    
    async def read_file(self, file: str, text: bool = True) -> str | bytes:
        """Read a file from the sandbox."""
        raise NotImplementedError("read_file method not implemented yet")
    
    @classmethod
    async def task_init(
        cls,
        task_name: str,
        config: Optional[FactorioConfig] = None,
        **kwargs
    ) -> None:
        """Initialize global resources for the task."""
        raise NotImplementedError("task_init method not implemented yet")
    
    @classmethod
    async def sample_init(
        cls,
        task_name: str,
        config: Optional[FactorioConfig] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, "FactorioSandboxEnvironment"]:
        """Initialize sandbox environment for a sample."""
        raise NotImplementedError("sample_init method not implemented yet")
    
    @classmethod
    async def sample_cleanup(
        cls,
        task_name: str,
        config: Optional[FactorioConfig] = None,
        environments: Optional[Dict[str, "FactorioSandboxEnvironment"]] = None,
        interrupted: bool = False,
        **kwargs
    ) -> None:
        """Clean up sandbox environment after sample completion."""
        raise NotImplementedError("sample_cleanup method not implemented yet")
    
    @classmethod
    async def task_cleanup(
        cls,
        task_name: str,
        config: Optional[FactorioConfig] = None,
        **kwargs
    ) -> None:
        """Clean up global resources after task completion."""
        raise NotImplementedError("task_cleanup method not implemented yet")
    
    @classmethod
    def default_concurrency(cls) -> SandboxEnvironmentSpec:
        """Return default concurrency limits for Factorio environments."""
        return SandboxEnvironmentSpec(type="factorio")