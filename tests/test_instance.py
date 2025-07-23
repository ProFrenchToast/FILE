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
    async def test_execute_python_code_instance_not_running(self, instance):
        """Test that execute_python_code raises error when instance not running."""
        # Instance starts as not initialized
        assert instance._initialized is False
        
        with pytest.raises(RuntimeError, match="Factorio instance is not running"):
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
    
    # RCON-related test fixtures
    @pytest.fixture
    def mock_rcon_client(self):
        """Create a mock RCON client for testing."""
        mock_client = Mock()
        mock_client.connect = Mock()
        mock_client.close = Mock()
        mock_client.send_command = Mock()
        return mock_client
    
    @pytest.fixture
    def rcon_config(self):
        """Create config with RCON settings."""
        config = FactorioConfig()
        config.rcon_port = 27015
        config.rcon_password = "factorio"
        return config
    
    @pytest.mark.asyncio
    async def test_connect_rcon_success(self, instance, mock_rcon_client):
        """Test successful RCON connection."""
        with patch('factorio_rcon.RCONClient') as mock_rcon_class:
            mock_rcon_class.return_value = mock_rcon_client
            
            # Set up instance as if Docker container is running
            instance._initialized = True
            instance.container = Mock()
            
            await instance._connect_rcon()
            
            assert instance.rcon_client == mock_rcon_client
            mock_rcon_client.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_rcon_failure(self, instance):
        """Test RCON connection failure."""
        from factorio_rcon import RCONConnectError
        
        with patch('factorio_rcon.RCONClient') as mock_rcon_class:
            mock_client = Mock()
            mock_client.connect = Mock(side_effect=RCONConnectError("Connection failed"))
            mock_rcon_class.return_value = mock_client
            
            # Set up instance as if Docker container is running
            instance._initialized = True
            instance.container = Mock()
            
            with pytest.raises(RCONConnectError):
                await instance._connect_rcon()
    
    @pytest.mark.asyncio
    async def test_execute_python_code_basic(self, instance, mock_rcon_client):
        """Test basic Python code execution via RCON."""
        mock_rcon_client.send_command.return_value = "4"
        
        with patch('factorio_rcon.RCONClient') as mock_rcon_class:
            mock_rcon_class.return_value = mock_rcon_client
            
            # Set up instance as if running with RCON connected
            instance._initialized = True
            instance.container = Mock()
            instance.rcon_client = mock_rcon_client
            
            result = await instance.execute_python_code("2 + 2")
            
            assert result == "4"
            mock_rcon_client.send_command.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_python_code_with_output(self, instance, mock_rcon_client):
        """Test Python code execution with print output."""
        mock_rcon_client.send_command.return_value = "hello world"
        
        with patch('factorio_rcon.RCONClient') as mock_rcon_class:
            mock_rcon_class.return_value = mock_rcon_client
            
            # Set up instance as if running with RCON connected
            instance._initialized = True
            instance.container = Mock()
            instance.rcon_client = mock_rcon_client
            
            result = await instance.execute_python_code("print('hello world')")
            
            assert result == "hello world"
            mock_rcon_client.send_command.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_python_code_not_running(self, instance):
        """Test Python code execution when instance is not running."""
        # Instance not initialized
        instance._initialized = False
        
        with pytest.raises(Exception):  # Should raise appropriate exception
            await instance.execute_python_code("print('test')")
    
    @pytest.mark.asyncio
    async def test_execute_python_code_rcon_error(self, instance, mock_rcon_client):
        """Test Python code execution with RCON error."""
        from factorio_rcon import RCONSendError
        
        mock_rcon_client.send_command = Mock(side_effect=RCONSendError("Send error"))
        
        with patch('factorio_rcon.RCONClient') as mock_rcon_class:
            mock_rcon_class.return_value = mock_rcon_client
            
            # Set up instance as if running with RCON connected
            instance._initialized = True
            instance.container = Mock()
            instance.rcon_client = mock_rcon_client
            
            with pytest.raises(RuntimeError):
                await instance.execute_python_code("print('test')")
    
    @pytest.mark.asyncio
    async def test_execute_python_code_auto_connect(self, instance, mock_rcon_client):
        """Test that execute_python_code auto-connects RCON if not connected."""
        mock_rcon_client.send_command.return_value = "42"
        
        with patch('factorio_rcon.RCONClient') as mock_rcon_class:
            mock_rcon_class.return_value = mock_rcon_client
            
            # Set up instance as running but without RCON connected
            instance._initialized = True
            instance.container = Mock()
            instance.rcon_client = None
            
            result = await instance.execute_python_code("6 * 7")
            
            assert result == "42"
            mock_rcon_client.connect.assert_called_once()
            mock_rcon_client.send_command.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_disconnects_rcon(self, instance):
        """Test that stopping instance disconnects RCON client."""
        # Set up instance as if it was started with RCON
        mock_container = Mock()
        mock_client = Mock()
        mock_rcon_client = Mock()
        mock_rcon_client.close = AsyncMock()
        
        instance.container = mock_container
        instance.docker_client = mock_client
        instance.rcon_client = mock_rcon_client
        instance._initialized = True
        
        await instance.stop()
        
        mock_rcon_client.close.assert_called_once()
        assert instance.rcon_client is None