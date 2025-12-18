# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:34
# Last Updated: 2025-12-18T12:28:34
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
Base controller class for separation of concerns in MainWindow.
"""

from typing import Any, Callable, Optional
from abc import ABC, abstractmethod


class BaseController(ABC):
    """Base class for all controllers."""

    def __init__(self, main_window):
        self.main_window = main_window
        self.container = main_window.container

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the controller."""
        pass


class WorkerManager:
    """Manages background workers for API operations."""

    def __init__(self, main_window):
        self.main_window = main_window
        self.active_workers = []

    def create_worker(self, func: Callable, *args, **kwargs) -> Any:
        """Create and start a background worker."""
        from ..workers import APIWorker

        worker = APIWorker(func, *args, **kwargs)
        self.active_workers.append(worker)

        def cleanup_worker():
            if worker in self.active_workers:
                self.active_workers.remove(worker)

        worker.finished.connect(cleanup_worker)
        worker.start()
        return worker