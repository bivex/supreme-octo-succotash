"""API Worker for async operations."""

from PyQt6.QtCore import QThread, pyqtSignal


class APIWorker(QThread):
    """
    Worker thread for API operations.

    Executes API calls in a background thread to prevent UI freezing.
    Emits signals when the operation completes or encounters an error.
    """
    finished = pyqtSignal(object)  # Result data
    error = pyqtSignal(str)       # Error message

    def __init__(self, func, *args, **kwargs):
        """
        Initialize API worker.

        Args:
            func: The function to execute in the background
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
        """
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.is_finished = False

    def run(self):
        """Execute the function and emit appropriate signals."""
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.is_finished = True

    def __del__(self):
        """Ensure thread cleanup when object is destroyed."""
        if self.isRunning():
            self.wait()  # Wait for thread to finish before destruction
