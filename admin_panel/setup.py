
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:33
# Last Updated: 2025-12-18T12:28:33
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Setup script for Advertising Platform Admin Panel
"""

from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

python_versions_classifiers = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

classifiers_list = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
] + python_versions_classifiers

entry_points_list = {
    'console_scripts': [
        'advertising-admin=main:main',
    ],
}

app_name = "advertising-platform-admin"
app_version = "1.0.0"
app_description = (
    "PyQt6 Admin Panel for Advertising Platform"
)

setup(
    name=app_name,
    version=app_version,
    description=app_description,
    packages=find_packages(),
    install_requires=requirements,
    entry_points=entry_points_list,
    classifiers=classifiers_list,
)