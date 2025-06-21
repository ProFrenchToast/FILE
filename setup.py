from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="factorio-inspect",
    version="0.1.0",
    author="Patrick",
    description="Factorio learning environment integration for Inspect AI framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "inspect-ai>=0.3.0",
        "asyncio-tools>=0.3.0",
        "pydantic>=2.0.0",
        "docker>=6.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "analysis": [
            "jupyter>=1.0.0",
            "matplotlib>=3.5.0",
            "pandas>=1.5.0",
        ],
    },
    entry_points={
        "inspect_ai": [
            "factorio=factorio_inspect.environment:FactorioSandboxEnvironment",
        ],
    },
)