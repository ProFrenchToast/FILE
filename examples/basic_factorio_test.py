"""
Basic Factorio environment test.

This is a minimal test to verify the Factorio environment is working.
It's simpler than the full task and good for debugging.

Run with: inspect eval examples/basic_factorio_test.py
"""

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import includes
from inspect_ai.solver import generate
from inspect_ai.util import SandboxEnvironmentSpec
from factorio_inspect.config import FactorioConfig
from factorio_inspect.environment import FactorioSandboxEnvironment


@task
def basic_factorio_test():
    """Basic test to verify Factorio environment functionality."""
    
    sample = Sample(
        input="Execute this Python code: print('Factorio environment is working!')",
        target="Factorio environment is working!"
    )
    
    return Task(
        dataset=[sample],
        solver=generate(),
        scorer=includes(),  # Simple text matching scorer
        sandbox=SandboxEnvironmentSpec(
            "factorio",
            FactorioConfig(
                headless=True,
                timeout=30.0,
                base_port=36000,  # Different ports to avoid conflicts
                rcon_port=27600,
            )
        ),
        epochs=1
    )