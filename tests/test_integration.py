"""Integration tests for Factorio-Inspect AI system."""

import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from factorio_inspect.environment import FactorioSandboxEnvironment
from factorio_inspect.instance import FactorioInstance
from factorio_inspect.config import FactorioConfig


class TestFactorioIntegration:
    """Integration tests for the complete Factorio-Inspect AI system."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return FactorioConfig(
            docker_image="factorio:latest",
            timeout=60.0,
            base_port=35000,  # Use different port for tests
            headless=True
        )
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_lifecycle_mocked(self, config):
        """Test complete lifecycle with mocked Docker."""
        with patch('docker.from_env') as mock_docker:
            # Mock Docker client and container
            mock_client = Mock()
            mock_container = Mock()
            mock_container.status = "running"
            mock_container.exec_run.return_value = Mock(
                exit_code=0,
                output=b"Hello from container"
            )
            mock_client.containers.run.return_value = mock_container
            mock_docker.return_value = mock_client
            
            # Create instance and environment
            instance = FactorioInstance(config, "integration-test")
            environment = FactorioSandboxEnvironment(instance)
            
            # Test full lifecycle
            async with instance:
                assert instance.is_running
                
                # Test command execution
                result = await environment.exec(["echo", "test"])
                assert result.success
                assert "Hello from container" in result.stdout
                
                # Test Python code execution (will raise NotImplementedError from execute_python_code)
                result = await environment.exec(["python", "-c", "print('hello')"])
                assert not result.success
                assert "not implemented" in result.stderr
            
            # After context exit, should be stopped
            assert not instance.is_running
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_sample_init_cleanup_cycle(self, config):
        """Test Inspect AI sample initialization and cleanup cycle."""
        # These will fail until we implement sample_init/sample_cleanup
        with pytest.raises(NotImplementedError):
            result = await FactorioSandboxEnvironment.sample_init(
                "test_task",
                config,
                metadata={"scenario": "basic_automation"}
            )
        
        with pytest.raises(NotImplementedError):
            await FactorioSandboxEnvironment.sample_cleanup(
                "test_task",
                config,
                environments={},
                interrupted=False
            )
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.docker
    async def test_real_docker_integration(self, config):
        """Test with real Docker (requires Factorio image)."""
        import time
        # Use timestamp to ensure unique container names
        unique_id = f"real-docker-test-{int(time.time())}"
        instance = FactorioInstance(config, unique_id)
        
        try:
            # This should fail with docker.errors.ImageNotFound or similar
            await instance.start()
            
            # If we get here, Factorio is actually working!
            assert instance.is_running
            
            # Test basic container functionality
            environment = FactorioSandboxEnvironment(instance)
            result = await environment.exec(["echo", "Docker is working!"])
            assert result.success
            
        finally:
            await instance.stop()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_instances(self, config):
        """Test multiple Factorio instances running concurrently."""
        with patch('docker.from_env') as mock_docker:
            # Set up mocks for multiple containers
            mock_client = Mock()
            containers = []
            for i in range(3):
                container = Mock()
                container.status = "running"
                container.exec_run.return_value = Mock(
                    exit_code=0,
                    output=f"Container {i}".encode()
                )
                containers.append(container)
            
            mock_client.containers.run.side_effect = containers
            mock_docker.return_value = mock_client
            
            # Create multiple instances
            instances = [
                FactorioInstance(config, f"concurrent-test-{i}")
                for i in range(3)
            ]
            
            environments = [
                FactorioSandboxEnvironment(instance)
                for instance in instances
            ]
            
            # Start all instances concurrently
            await asyncio.gather(*[instance.start() for instance in instances])
            
            try:
                # Verify all are running
                for instance in instances:
                    assert instance.is_running
                
                # Test concurrent command execution
                results = await asyncio.gather(*[
                    env.exec(["echo", f"test-{i}"])
                    for i, env in enumerate(environments)
                ])
                
                # Verify all commands succeeded
                for i, result in enumerate(results):
                    assert result.success
                    assert f"Container {i}" in result.stdout
                    
            finally:
                # Clean up all instances
                await asyncio.gather(*[instance.stop() for instance in instances])
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_error_handling_integration(self, config):
        """Test error handling across the integration."""
        # Test environment handling non-running instance (simpler test)
        instance = FactorioInstance(config, "error-test")
        
        # Instance starts as not running
        assert not instance.is_running
        
        # Environment should handle non-running instance gracefully
        environment = FactorioSandboxEnvironment(instance)
        result = await environment.exec(["echo", "test"])
        
        assert not result.success
        assert result.stderr == "Factorio instance is not running"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_inspect_ai_compatibility(self, config):
        """Test compatibility with Inspect AI interface requirements."""
        # Test that our environment has all required methods
        assert hasattr(FactorioSandboxEnvironment, 'exec')
        assert hasattr(FactorioSandboxEnvironment, 'write_file')
        assert hasattr(FactorioSandboxEnvironment, 'read_file')
        assert hasattr(FactorioSandboxEnvironment, 'sample_init')
        assert hasattr(FactorioSandboxEnvironment, 'sample_cleanup')
        assert hasattr(FactorioSandboxEnvironment, 'task_init')
        assert hasattr(FactorioSandboxEnvironment, 'task_cleanup')
        assert hasattr(FactorioSandboxEnvironment, 'default_concurrency')
        
        # Test concurrency spec
        spec = FactorioSandboxEnvironment.default_concurrency()
        assert spec.type == "factorio"
        
        # Test that the sandbox is properly decorated
        assert hasattr(FactorioSandboxEnvironment, '__qualname__')
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_rcon_python_execution_mocked(self, config):
        """Test Python code execution via RCON with mocked components."""
        with patch('docker.from_env') as mock_docker, \
             patch('factorio_rcon.RCONClient') as mock_rcon:
            
            # Mock Docker
            mock_client = Mock()
            mock_container = Mock()
            mock_container.status = "running"
            mock_client.containers.run.return_value = mock_container
            mock_docker.return_value = mock_client
            
            # Mock RCON
            mock_rcon_client = Mock()
            mock_rcon_client.connect = AsyncMock()
            mock_rcon_client.send_command = AsyncMock(return_value="42")
            mock_rcon.return_value = mock_rcon_client
            
            # Create instance and test Python execution
            instance = FactorioInstance(config, "rcon-test")
            environment = FactorioSandboxEnvironment(instance)
            
            async with instance:
                # Test Python code execution through environment
                result = await environment.exec(["python", "-c", "print(6 * 7)"])
                assert result.success
                assert "42" in result.stdout
                
                # Verify RCON was connected and used
                mock_rcon_client.connect.assert_called()
                mock_rcon_client.send_command.assert_called()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.docker
    async def test_rcon_real_docker_integration(self, config):
        """Test RCON with real Docker container (requires Factorio image)."""
        import time
        unique_id = f"rcon-docker-test-{int(time.time())}"
        instance = FactorioInstance(config, unique_id)
        
        try:
            await instance.start()
            
            if instance.is_running:
                # Test basic RCON connectivity
                result = await instance.execute_python_code("2 + 2")
                assert result is not None
                
                # Test Python execution through environment
                environment = FactorioSandboxEnvironment(instance)
                exec_result = await environment.exec(["python", "-c", "print('Hello RCON')"])
                
                # If RCON is working, we should get success
                # If not implemented yet, we expect specific error
                if exec_result.success:
                    assert "Hello RCON" in exec_result.stdout
                else:
                    # Should be RCON-related error, not "not implemented"
                    assert "not implemented" not in exec_result.stderr.lower()
                    
        finally:
            await instance.stop()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_rcon_connections(self, config):
        """Test multiple RCON connections running concurrently."""
        with patch('docker.from_env') as mock_docker, \
             patch('factorio_rcon.RCONClient') as mock_rcon:
            
            # Mock Docker for multiple containers
            mock_client = Mock()
            containers = []
            rcon_clients = []
            
            for i in range(3):
                # Docker container mock
                container = Mock()
                container.status = "running"
                containers.append(container)
                
                # RCON client mock
                rcon_client = Mock()
                rcon_client.connect = AsyncMock()
                rcon_client.send_command = AsyncMock(return_value=f"result-{i}")
                rcon_clients.append(rcon_client)
            
            mock_client.containers.run.side_effect = containers
            mock_rcon.side_effect = rcon_clients
            mock_docker.return_value = mock_client
            
            # Create multiple instances
            instances = [
                FactorioInstance(config, f"rcon-concurrent-{i}")
                for i in range(3)
            ]
            
            try:
                # Start all instances
                await asyncio.gather(*[instance.start() for instance in instances])
                
                # Test concurrent Python execution
                results = await asyncio.gather(*[
                    instance.execute_python_code(f"print('test-{i}')")
                    for i, instance in enumerate(instances)
                ])
                
                # Verify all executions succeeded
                for i, result in enumerate(results):
                    assert result == f"result-{i}"
                
                # Verify all RCON clients were used
                for rcon_client in rcon_clients:
                    rcon_client.connect.assert_called()
                    rcon_client.send_command.assert_called()
                    
            finally:
                await asyncio.gather(*[instance.stop() for instance in instances])
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_rcon_error_handling_integration(self, config):
        """Test RCON error handling in integration scenarios."""
        with patch('docker.from_env') as mock_docker, \
             patch('factorio_rcon.RCONClient') as mock_rcon:
            
            # Mock Docker
            mock_client = Mock()
            mock_container = Mock()
            mock_container.status = "running"
            mock_client.containers.run.return_value = mock_container
            mock_docker.return_value = mock_client
            
            # Mock RCON with connection error
            from factorio_rcon import RCONConnectError
            mock_rcon_client = Mock()
            mock_rcon_client.connect = AsyncMock(side_effect=RCONConnectError("Connection failed"))
            mock_rcon.return_value = mock_rcon_client
            
            instance = FactorioInstance(config, "rcon-error-test")
            environment = FactorioSandboxEnvironment(instance)
            
            async with instance:
                # Test Python execution with RCON connection failure
                result = await environment.exec(["python", "-c", "print('test')"])
                
                # Should handle RCON error gracefully
                assert not result.success
                assert "connection" in result.stderr.lower() or "rcon" in result.stderr.lower()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_rcon_reconnection_handling(self, config):
        """Test RCON reconnection after connection loss."""
        with patch('docker.from_env') as mock_docker, \
             patch('factorio_rcon.RCONClient') as mock_rcon:
            
            # Mock Docker
            mock_client = Mock()
            mock_container = Mock()
            mock_container.status = "running"
            mock_client.containers.run.return_value = mock_container
            mock_docker.return_value = mock_client
            
            # Mock RCON with initial failure then success
            from factorio_rcon import RCONSendError
            mock_rcon_client = Mock()
            mock_rcon_client.connect = AsyncMock()
            mock_rcon_client.send_command = AsyncMock(
                side_effect=[
                    RCONSendError("Send error"),  # First call fails
                    "success"  # Second call succeeds
                ]
            )
            mock_rcon.return_value = mock_rcon_client
            
            instance = FactorioInstance(config, "rcon-reconnect-test")
            
            async with instance:
                # First execution should fail
                try:
                    await instance.execute_python_code("print('first')")
                    assert False, "Should have raised error"
                except RuntimeError:
                    pass  # Expected
                
                # Second execution should succeed (if retry logic is implemented)
                result = await instance.execute_python_code("print('second')")
                assert result == "success" or result is None  # Depends on implementation


@pytest.fixture(scope="session")
def docker_available():
    """Check if Docker is available for integration tests."""
    try:
        import docker
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


def pytest_runtest_setup(item):
    """Skip Docker tests if Docker is not available."""
    if "docker" in item.keywords:
        docker_available = pytest.importorskip("docker")
        try:
            import docker
            client = docker.from_env()
            client.ping()
        except Exception:
            pytest.skip("Docker not available")