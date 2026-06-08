#!/usr/bin/env python3
"""
APIPulse-CLI - Lightweight Terminal API Health Monitoring Engine
轻量级终端API健康监控引擎

Setup script for installation via pip.
"""

import os
import sys
from setuptools import setup, find_packages

# Read README for long description
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
long_description = ""
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="apipulse-cli",
    version="1.0.0",
    description="Lightweight Terminal API Health Monitoring Engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="APIPulse Contributors",
    license="MIT",
    url="https://github.com/gitstq/APIPulse-CLI",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "apipulse=healthpulse.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Monitoring",
        "Topic :: Utilities",
    ],
    keywords=["api", "health", "monitor", "cli", "endpoint", "http", "ping"],
)
