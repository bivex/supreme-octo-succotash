# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:13:00
# Last Updated: 2025-12-18T12:28:33
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Async debugging utilities using async-trace."""

import logging
import time
from typing import Dict, Any, Optional
import asyncio
logger = logging.getLogger(__name__)

# Check if async-trace is available
try:
    from async_trace import print_trace, collect_async_trace, save_trace_to_json, save_trace_to_html, save_trace, log_trace_to_file
    ASYNC_TRACE_AVAILABLE = True
except ImportError:
    ASYNC_TRACE_AVAILABLE = False
    print_trace = None
    collect_async_trace = None
    save_trace_to_json = None
    save_trace_to_html = None
    save_trace = None
    log_trace_to_file = None

def debug_async_trace(message: str = "Async call stack:") -> None:
    """Print current async call stack for debugging."""
    if not ASYNC_TRACE_AVAILABLE:
        logger.warning("⚠️  async-trace not available. Install with: pip install async-trace")
        return

    print(f"\n🔍 {message}")
    try:
        # Determine if we are in an async context
        try:
            asyncio.get_running_loop()
            ctx = "(async context)"
        except RuntimeError:
            ctx = "(sync context)"

        print(f"🧭 Context: {ctx}")
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

def save_trace_to_file(filename: str = None, format: str = "json") -> Optional[str]:
    """Save current async trace to file for later analysis.

    Args:
        filename: Optional filename. If None, generates timestamped name.
        format: Format to save in ('json', 'html')

    Returns:
        Path to saved file or None if async-trace not available or no event loop
    """
    if not ASYNC_TRACE_AVAILABLE:
        logger.warning("⚠️  async-trace not available for saving traces")
        return None

    try:
        # Check if we have a running event loop before attempting to save trace
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            logger.warning("⚠️  Skipping async trace save: no running event loop")
            return None

        filepath = save_trace(filename, format)
        logger.info(f"💾 Async trace saved to: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"❌ Error saving async trace: {e}")
        return None

def log_trace_to_continuous_file(filename: str = "async_trace_continuous.jsonl") -> Optional[str]:
    """Append current trace to continuous log file for monitoring.

    Args:
        filename: Log filename (default: async_trace_continuous.jsonl)

    Returns:
        Path to log file or None if async-trace not available
    """
    if not ASYNC_TRACE_AVAILABLE:
        logger.warning("⚠️  async-trace not available for continuous logging")
        return None

    try:
        filepath = log_trace_to_file(filename)
        logger.debug(f"📝 Trace appended to continuous log: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"❌ Error logging trace to file: {e}")
        return None

def save_debug_snapshot(reason: str = "debug") -> Optional[str]:
    """Save a debug snapshot of current async state (HTML) with threads/loop info if available."""
    timestamp = time.strftime("%H%M%S")
    filename = f"debug_snapshot_{reason}_{timestamp}.html"

    if not ASYNC_TRACE_AVAILABLE:
        logger.warning("⚠️  async-trace not available for debug snapshots")
        return None

    try:
        # Check if we have a running event loop before attempting to save trace
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            logger.warning("⚠️  Skipping debug snapshot: no running event loop")
            return None

        # Prefer richer snapshot if extended API is present
        try:
            from async_trace import save_full_trace
            filepath = save_full_trace(filename, format="html")
        except Exception:
            filepath = save_trace_to_file(filename, "html")

        if filepath:
            logger.info(f"📸 Debug snapshot saved: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"❌ Error saving debug snapshot: {e}")
        return None
