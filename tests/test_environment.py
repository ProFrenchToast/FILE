"""Tests for FactorioSandboxEnvironment."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from factorio_inspect.environment import FactorioSandboxEnvironment
from factorio_inspect.instance import FactorioInstance
from factorio_inspect.config import FactorioConfig


class TestFactorioSandboxEnvironment:
    """Test cases for FactorioSandboxEnvironment."""
    
    @pytest.fixture
    def mock_instance(self):
        """Create a mock FactorioInstance."""
        instance = Mock(spec=FactorioInstance)
        instance.start = AsyncMock()
        instance.stop = AsyncMock()
        instance.execute_python_code = AsyncMock()
        instance.is_running = True
        return instance
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return FactorioConfig()
    
    @pytest.fixture
    def environment(self, mock_instance):
        """Create a FactorioSandboxEnvironment instance."""
        return FactorioSandboxEnvironment(mock_instance)
    
    def test_init(self, mock_instance):
        """Test environment initialization."""
        env = FactorioSandboxEnvironment(mock_instance)
        assert env.instance == mock_instance
    
    @pytest.mark.asyncio
    async def test_exec_when_instance_not_running(self, environment):
        """Test exec returns failure when instance is not running."""
        environment.instance.is_running = False
        
        result = await environment.exec(["echo", "test"])
        
        assert result.success is False
        assert result.returncode == 1
        assert result.stderr == "Factorio instance is not running"
        assert result.stdout == ""
    
    @pytest.mark.asyncio
    async def test_exec_python_code_success(self, environment):
        """Test successful Python code execution."""
        environment.instance.is_running = True
        environment.instance.execute_python_code = AsyncMock(return_value="Hello World")
        
        result = await environment.exec(["python", "-c", "print('Hello World')"])
        
        assert result.success is True
        assert result.returncode == 0
        assert result.stdout == "Hello World"
        assert result.stderr == ""
        environment.instance.execute_python_code.assert_called_once_with("print('Hello World')", 30.0)
    
    @pytest.mark.asyncio
    async def test_exec_python_code_failure(self, environment):
        """Test Python code execution failure."""
        environment.instance.is_running = True
        environment.instance.execute_python_code = AsyncMock(side_effect=Exception("Python error"))
        
        result = await environment.exec(["python", "-c", "invalid_code"])
        
        assert result.success is False
        assert result.returncode == 1
        assert result.stdout == ""
        assert result.stderr == "Python error"
    
    @pytest.mark.asyncio
    async def test_exec_shell_command_success(self, environment):
        """Test successful shell command execution."""
        environment.instance.is_running = True
        
        # Mock container exec_run
        mock_exec_result = Mock()
        mock_exec_result.exit_code = 0
        mock_exec_result.output = b"test output"
        environment.instance.container = Mock()
        environment.instance.container.exec_run.return_value = mock_exec_result
        
        result = await environment.exec(["echo", "test"])
        
        assert result.success is True
        assert result.returncode == 0
        assert result.stdout == "test output"
        assert result.stderr == ""
    
    @pytest.mark.asyncio
    async def test_write_file_not_implemented(self, environment):
        """Test that write_file method raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await environment.write_file("test.txt", "content")
    
    @pytest.mark.asyncio
    async def test_read_file_not_implemented(self, environment):
        """Test that read_file method raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await environment.read_file("test.txt")
    
    @pytest.mark.asyncio
    async def test_task_init_not_implemented(self, config):
        """Test that task_init method raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await FactorioSandboxEnvironment.task_init("test_task", config)
    
    @pytest.mark.asyncio
    async def test_sample_init_not_implemented(self, config):
        """Test that sample_init method raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await FactorioSandboxEnvironment.sample_init("test_task", config)
    
    @pytest.mark.asyncio
    async def test_sample_cleanup_not_implemented(self, config):
        """Test that sample_cleanup method raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await FactorioSandboxEnvironment.sample_cleanup("test_task", config)
    
    @pytest.mark.asyncio
    async def test_task_cleanup_not_implemented(self, config):
        """Test that task_cleanup method raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await FactorioSandboxEnvironment.task_cleanup("test_task", config)
    
    def test_default_concurrency(self):
        """Test default concurrency settings."""
        spec = FactorioSandboxEnvironment.default_concurrency()
        assert spec.type == "factorio"
    
    def test_sandbox_registration(self):
        """Test that the sandbox is properly registered."""
        # This would test the @sandboxenv decorator
        # For now, just verify the class exists and has the right methods
        assert hasattr(FactorioSandboxEnvironment, 'exec')
        assert hasattr(FactorioSandboxEnvironment, 'write_file')
        assert hasattr(FactorioSandboxEnvironment, 'read_file')
        assert hasattr(FactorioSandboxEnvironment, 'sample_init')
        assert hasattr(FactorioSandboxEnvironment, 'sample_cleanup')