#!/usr/bin/env python3
"""
Setup script for Advertising Platform Admin Panel
"""

from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="advertising-platform-admin",
    version="1.0.0",
    description="PyQt6 Admin Panel for Advertising Platform",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'advertising-admin=main:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)