# Re-export from the installed async_trace package
try:
    from async_trace import *
except ImportError:
    # If not available, provide minimal stubs
    def EnhancedAsyncTracer(*args, **kwargs):
        return None

    def AsyncDebugger(*args, **kwargs):
        return None

    class FrameCapture:
        pass

    class AsyncCallChain:
        pass
