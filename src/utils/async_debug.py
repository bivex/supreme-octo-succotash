"""Async debugging utilities using async-trace."""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Check if async-trace is available
try:
    from async_trace import print_trace, collect_async_trace
    ASYNC_TRACE_AVAILABLE = True
except ImportError:
    ASYNC_TRACE_AVAILABLE = False
    print_trace = None
    collect_async_trace = None

def debug_async_trace(message: str = "Async call stack:") -> None:
    """Print current async call stack for debugging."""
    if not ASYNC_TRACE_AVAILABLE:
        logger.warning("⚠️  async-trace not available. Install with: pip install async-trace")
        return

    print(f"\n🔍 {message}")
    try:
        print_trace()
    except Exception as e:
        logger.error(f"Error getting async trace: {e}")

def get_async_trace_data() -> Optional[Dict[str, Any]]:
    """Get structured async trace data."""
    if not ASYNC_TRACE_AVAILABLE:
        logger.warning("⚠️  async-trace not available. Install with: pip install async-trace")
        return None

    try:
        return collect_async_trace()
    except Exception as e:
        logger.error(f"Error collecting async trace: {e}")
        return None

def log_task_info() -> None:
    """Log information about current asyncio tasks."""
    import asyncio

    if not ASYNC_TRACE_AVAILABLE:
        logger.warning("⚠️  async-trace not available for detailed task info")
        return

    try:
        trace_data = get_async_trace_data()
        if trace_data:
            current_task = trace_data['current_task']
            frames = trace_data['frames']

            logger.info(f"📋 Current task: {current_task.get_name()}")
            logger.info(f"📊 Total frames in call stack: {len(frames)}")

            # Show task creation points
            task_frames = [f for f in frames if f['task']]
            if task_frames:
                logger.info(f"🎯 Task creation points ({len(task_frames)}):")
                for frame in task_frames:
                    task_name = frame['task'].get_name() if frame['task'] else "unknown"
                    logger.info(f"  • {frame['name']}() → creates {task_name}")

    except Exception as e:
        logger.error(f"Error logging task info: {e}")

# Convenience functions for common debugging scenarios
def debug_before_await(operation: str) -> None:
    """Log before an async operation."""
    logger.debug(f"⏳ Starting async operation: {operation}")
    debug_async_trace(f"Before {operation}")

def debug_after_await(operation: str) -> None:
    """Log after an async operation."""
    logger.debug(f"✅ Completed async operation: {operation}")
    debug_async_trace(f"After {operation}")

def debug_database_call(query_type: str = "query") -> None:
    """Debug database operations."""
    debug_async_trace(f"Database {query_type} call stack")

def debug_http_request(endpoint: str = "unknown") -> None:
    """Debug HTTP request handling."""
    debug_async_trace(f"HTTP request to {endpoint}")

def debug_task_creation() -> None:
    """Debug when tasks are being created."""
    debug_async_trace("Task creation point")
