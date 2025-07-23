"""
Simple Factorio task example for Inspect AI.

This demonstrates basic usage of the Factorio sandbox environment.
The task asks the model to execute Python code in the Factorio environment
to check the game state and perform basic interactions.

Run with: inspect eval examples/simple_factorio_task.py
"""

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import model_graded_qa
from inspect_ai.solver import generate
from inspect_ai.util import SandboxEnvironmentSpec
from factorio_inspect.config import FactorioConfig
from factorio_inspect.environment import FactorioSandboxEnvironment


@task
def simple_factorio_task():
    """A simple task that demonstrates Factorio environment usage."""
    
    # Create a single sample that asks the model to interact with Factorio
    sample = Sample(
        input=(
            "You are an AI agent in a Factorio game environment. "
            "Your task is to:\n"
            "1. Execute Python code to check if you can interact with the game\n"
            "2. Try to print a simple message using Python\n"
            "3. Report what you discovered about the environment\n\n"
            "Use Python code execution to explore the environment. "
            "For example, you can use: python -c \"print('Hello from Factorio!')\""
        ),
        target="The agent successfully executed Python code and reported their findings."
    )
    
    return Task(
        dataset=[sample],
        solver=[
            generate(),  # Let the model generate responses and execute commands
        ],
        scorer=model_graded_qa(),  # Use model-based scoring
        sandbox=SandboxEnvironmentSpec(
            "factorio",
            FactorioConfig(
                headless=True,           # Run without GUI for evaluation
                timeout=60.0,            # 60 second timeout
                base_port=35000,         # Use high port numbers to avoid conflicts
                rcon_port=27500,         # Use high RCON port
            )
        ),
        epochs=1
    )


if __name__ == "__main__":
    # Allow running the task directly for testing
    print("Simple Factorio Task")
    print("===================")
    print("This task demonstrates basic Factorio environment usage.")
    print("Run with: inspect eval examples/simple_factorio_task.py")
    print()
    print("The task will:")
    print("1. Start a Factorio server in a Docker container")
    print("2. Ask the model to execute Python code in the environment")
    print("3. Evaluate the model's ability to interact with the game")