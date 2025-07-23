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
    async def test_write_file_not_supported_in_game_environment(self, environment):
        """Test that write_file raises NotImplementedError by design.
        
        File I/O operations don't have meaningful semantics in Factorio game environments.
        This is the correct behavior - interaction should happen through game mechanics.
        """
        with pytest.raises(NotImplementedError, match="File I/O operations are not supported"):
            await environment.write_file("test.txt", "content")
    
    @pytest.mark.asyncio
    async def test_read_file_not_supported_in_game_environment(self, environment):
        """Test that read_file raises NotImplementedError by design.
        
        File I/O operations don't have meaningful semantics in Factorio game environments.
        This is the correct behavior - interaction should happen through game mechanics.
        """
        with pytest.raises(NotImplementedError, match="File I/O operations are not supported"):
            await environment.read_file("test.txt")
    
    @pytest.mark.asyncio
    async def test_task_init_success(self, config):
        """Test that task_init method completes successfully."""
        # Should complete without error (no global init needed for Factorio)
        await FactorioSandboxEnvironment.task_init("test_task", config)
    
    @pytest.mark.asyncio
    async def test_sample_init_success(self, config):
        """Test successful sample initialization."""
        with patch('factorio_inspect.environment.FactorioInstance') as mock_instance_class:
            # Mock the instance creation and startup
            mock_instance = Mock()
            mock_instance.start = AsyncMock()
            mock_instance_class.return_value = mock_instance
            
            # Call sample_init
            result = await FactorioSandboxEnvironment.sample_init("test_task", config)
            
            # Verify the result structure
            assert isinstance(result, dict)
            assert "sandbox" in result
            assert isinstance(result["sandbox"], FactorioSandboxEnvironment)
            
            # Verify instance was created and started
            mock_instance_class.assert_called_once()
            mock_instance.start.assert_called_once()
            
            # Verify the environment has the correct instance
            assert result["sandbox"].instance == mock_instance
    
    @pytest.mark.asyncio
    async def test_sample_init_with_metadata(self, config):
        """Test sample initialization with metadata."""
        with patch('factorio_inspect.environment.FactorioInstance') as mock_instance_class:
            mock_instance = Mock()
            mock_instance.start = AsyncMock()
            mock_instance_class.return_value = mock_instance
            
            metadata = {"scenario": "custom_scenario", "difficulty": "hard"}
            
            result = await FactorioSandboxEnvironment.sample_init(
                "test_task", config, metadata=metadata
            )
            
            # Should still work with metadata
            assert "sandbox" in result
            assert isinstance(result["sandbox"], FactorioSandboxEnvironment)
            mock_instance.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sample_init_unique_instance_ids(self, config):
        """Test that multiple sample_init calls create unique instance IDs."""
        with patch('factorio_inspect.environment.FactorioInstance') as mock_instance_class:
            mock_instance1 = Mock()
            mock_instance1.start = AsyncMock()
            mock_instance2 = Mock()  
            mock_instance2.start = AsyncMock()
            mock_instance_class.side_effect = [mock_instance1, mock_instance2]
            
            # Create two sample environments
            result1 = await FactorioSandboxEnvironment.sample_init("task1", config)
            result2 = await FactorioSandboxEnvironment.sample_init("task2", config)
            
            # Should have created two different instances
            assert mock_instance_class.call_count == 2
            
            # The instance IDs should be different (we'll check this by verifying different calls)
            calls = mock_instance_class.call_args_list
            assert calls[0] != calls[1]  # Different arguments means different instance IDs
    
    @pytest.mark.asyncio
    async def test_sample_init_instance_start_failure(self, config):
        """Test handling of instance startup failure."""
        with patch('factorio_inspect.environment.FactorioInstance') as mock_instance_class:
            mock_instance = Mock()
            mock_instance.start = AsyncMock(side_effect=RuntimeError("Docker failed"))
            mock_instance_class.return_value = mock_instance
            
            # Should propagate the startup error
            with pytest.raises(RuntimeError, match="Docker failed"):
                await FactorioSandboxEnvironment.sample_init("test_task", config)
    
    @pytest.mark.asyncio
    async def test_sample_cleanup_success(self, config):
        """Test successful sample cleanup."""
        # Create mock environments
        mock_instance = Mock()
        mock_instance.stop = AsyncMock()
        mock_env = FactorioSandboxEnvironment(mock_instance)
        environments = {"sandbox": mock_env}
        
        # Call cleanup
        await FactorioSandboxEnvironment.sample_cleanup(
            "test_task", config, environments=environments
        )
        
        # Verify instance was stopped
        mock_instance.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sample_cleanup_no_environments(self, config):
        """Test cleanup with no environments provided."""
        # Should not crash when environments is None
        await FactorioSandboxEnvironment.sample_cleanup("test_task", config, environments=None)
        
        # Should not crash when environments is empty dict
        await FactorioSandboxEnvironment.sample_cleanup("test_task", config, environments={})
    
    @pytest.mark.asyncio
    async def test_sample_cleanup_interrupted(self, config):
        """Test cleanup when interrupted."""
        mock_instance = Mock()
        mock_instance.stop = AsyncMock()
        mock_env = FactorioSandboxEnvironment(mock_instance)
        environments = {"sandbox": mock_env}
        
        # Call cleanup with interrupted=True
        await FactorioSandboxEnvironment.sample_cleanup(
            "test_task", config, environments=environments, interrupted=True
        )
        
        # Should still stop the instance
        mock_instance.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sample_cleanup_multiple_environments(self, config):
        """Test cleanup with multiple environments."""
        # Create multiple mock environments
        mock_instance1 = Mock()
        mock_instance1.stop = AsyncMock()
        mock_env1 = FactorioSandboxEnvironment(mock_instance1)
        
        mock_instance2 = Mock()
        mock_instance2.stop = AsyncMock()
        mock_env2 = FactorioSandboxEnvironment(mock_instance2)
        
        environments = {"sandbox1": mock_env1, "sandbox2": mock_env2}
        
        # Call cleanup
        await FactorioSandboxEnvironment.sample_cleanup(
            "test_task", config, environments=environments
        )
        
        # Both instances should be stopped
        mock_instance1.stop.assert_called_once()
        mock_instance2.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sample_cleanup_stop_failure(self, config):
        """Test cleanup gracefully handles stop failures."""
        mock_instance1 = Mock()
        mock_instance1.stop = AsyncMock(side_effect=RuntimeError("Stop failed"))
        mock_env1 = FactorioSandboxEnvironment(mock_instance1)
        
        mock_instance2 = Mock()
        mock_instance2.stop = AsyncMock()  # This one should succeed
        mock_env2 = FactorioSandboxEnvironment(mock_instance2)
        
        environments = {"sandbox1": mock_env1, "sandbox2": mock_env2}
        
        # Cleanup should not raise error even if one instance fails to stop
        await FactorioSandboxEnvironment.sample_cleanup(
            "test_task", config, environments=environments
        )
        
        # Both stop methods should have been called
        mock_instance1.stop.assert_called_once()
        mock_instance2.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_task_cleanup_success(self, config):
        """Test that task_cleanup method completes successfully."""
        # Should complete without error (no global cleanup needed for Factorio)
        await FactorioSandboxEnvironment.task_cleanup("test_task", config)
    
    def test_default_concurrency(self):
        """Test default concurrency settings."""
        concurrency = FactorioSandboxEnvironment.default_concurrency()
        assert concurrency == 3  # Should return max concurrent instances
    
    def test_sandbox_registration(self):
        """Test that the sandbox is properly registered."""
        # This would test the @sandboxenv decorator
        # For now, just verify the class exists and has the right methods
        assert hasattr(FactorioSandboxEnvironment, 'exec')
        assert hasattr(FactorioSandboxEnvironment, 'write_file')
        assert hasattr(FactorioSandboxEnvironment, 'read_file')
        assert hasattr(FactorioSandboxEnvironment, 'sample_init')
        assert hasattr(FactorioSandboxEnvironment, 'sample_cleanup')