"""Tests for FactorioInstance."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from factorio_inspect.instance import FactorioInstance
from factorio_inspect.config import FactorioConfig


class TestFactorioInstance:
    """Test cases for FactorioInstance."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return FactorioConfig()
    
    @pytest.fixture
    def instance(self, config):
        """Create a FactorioInstance."""
        return FactorioInstance(config, "test-instance-1")
    
    def test_init(self, config):
        """Test instance initialization."""
        instance = FactorioInstance(config, "test-instance-1")
        assert instance.config == config
        assert instance.instance_id == "test-instance-1"
        assert instance.container is None
        assert instance.docker_client is None
        assert instance._initialized is False
    
    @pytest.mark.asyncio
    async def test_start_with_mocked_docker(self, instance):
        """Test successful start with mocked Docker."""
        with patch('docker.from_env') as mock_docker_env:
            mock_client = Mock()
            mock_container = Mock()
            mock_container.status = "running"
            mock_client.containers.run.return_value = mock_container
            mock_docker_env.return_value = mock_client
            
            await instance.start()
            
            assert instance._initialized is True
            assert instance.container == mock_container
            assert instance.docker_client == mock_client
    
    @pytest.mark.asyncio
    async def test_stop_with_mocked_container(self, instance):
        """Test successful stop with mocked container."""
        # Set up instance as if it was started
        mock_container = Mock()
        mock_client = Mock()
        instance.container = mock_container
        instance.docker_client = mock_client
        instance._initialized = True
        
        await instance.stop()
        
        mock_container.stop.assert_called_once_with(timeout=10)
        mock_client.close.assert_called_once()
        assert instance.container is None
        assert instance.docker_client is None
        assert instance._initialized is False
    
    @pytest.mark.asyncio
    async def test_execute_python_code_not_implemented(self, instance):
        """Test that execute_python_code method raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await instance.execute_python_code("print('hello')")
    
    @pytest.mark.asyncio
    async def test_execute_tool_not_implemented(self, instance):
        """Test that execute_tool method raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await instance.execute_tool("inspect_inventory", {})
    
    @pytest.mark.asyncio
    async def test_get_game_state_not_implemented(self, instance):
        """Test that get_game_state method raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await instance.get_game_state()
    
    @pytest.mark.asyncio
    async def test_reset_game_state_not_implemented(self, instance):
        """Test that reset_game_state method raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await instance.reset_game_state()
    
    @pytest.mark.asyncio
    async def test_health_check_not_implemented(self, instance):
        """Test that health_check method raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await instance.health_check()
    
    @pytest.mark.asyncio
    async def test_get_logs_not_implemented(self, instance):
        """Test that get_logs method raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await instance.get_logs()
    
    def test_is_running_property_false_when_not_initialized(self, instance):
        """Test that is_running returns False when not initialized."""
        assert instance.is_running is False
    
    def test_is_running_property_true_when_running(self, instance):
        """Test that is_running returns True when container is running."""
        mock_container = Mock()
        mock_container.status = "running"
        instance.container = mock_container
        instance._initialized = True
        
        assert instance.is_running is True
        mock_container.reload.assert_called_once()
    
    def test_connection_info_property_not_implemented(self, instance):
        """Test that connection_info property raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            _ = instance.connection_info
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self, instance):
        """Test async context manager functionality."""
        with patch('docker.from_env') as mock_docker_env:
            mock_client = Mock()
            mock_container = Mock()
            mock_container.status = "running"
            mock_client.containers.run.return_value = mock_container
            mock_docker_env.return_value = mock_client
            
            async with instance as ctx:
                assert ctx == instance
                assert instance._initialized is True
            
            # After context exit, should be stopped
            mock_container.stop.assert_called_once()
            assert instance._initialized is False