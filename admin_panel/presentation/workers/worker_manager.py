from .api_worker import APIWorker

class WorkerManager:
    def __init__(self, main_window):
        self.main_window = main_window

    def create_worker(self, func, *args, **kwargs):
        worker = APIWorker(func, *args, **kwargs)
        # Optionally, connect worker signals to main_window or other handlers
        # For now, just return the worker
        return worker
