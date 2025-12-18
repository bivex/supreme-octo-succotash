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

from .api_worker import APIWorker

class WorkerManager:
    def __init__(self, main_window):
        self.main_window = main_window

    def create_worker(self, func, *args, **kwargs):
        worker = APIWorker(func, *args, **kwargs)
        # Optionally, connect worker signals to main_window or other handlers
        # For now, just return the worker
        return worker
