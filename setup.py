from setuptools import find_packages, setup

setup(
    name="nicegui-chat",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "nicegui",
        "pydantic",
        "structlog",
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "fastapi",
    ],
    python_requires=">=3.8",
)
