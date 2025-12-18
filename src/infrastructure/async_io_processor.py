# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:32
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Asynchronous I/O processor for high-performance concurrent operations."""

import asyncio
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable

import aiofiles
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class AsyncTaskResult:
    """Result of an asynchronous task."""
    task_id: str
    success: bool
    result: Any
    error: Optional[str]
    execution_time: float
    timestamp: float


@dataclass
class BatchResult:
    """Result of a batch operation."""
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    total_time: float
    throughput: float
    results: List[AsyncTaskResult]


class AsyncIOProcessor:
    """High-performance asynchronous I/O processor."""

    def __init__(self, max_concurrent: int = 100, timeout: float = 30.0):
        self.max_concurrent = max_concurrent
        self.timeout = timeout

        # Semaphore for limiting concurrent operations
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # Thread pool for CPU-bound operations mixed with async
        self.thread_executor = ThreadPoolExecutor(max_workers=4)

        # HTTP session for connection reuse
        self.http_session: Optional[aiohttp.ClientSession] = None

        # Task tracking
        self.active_tasks = 0
        self.completed_tasks = 0

    async def __aenter__(self):
        """Async context manager entry."""
        # Create HTTP session with connection pooling
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent,
            limit_per_host=10,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=60
        )

        self.http_session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.http_session:
            await self.http_session.close()

    async def batch_http_requests(self, requests: List[Dict[str, Any]]) -> BatchResult:
        """Execute multiple HTTP requests concurrently."""
        start_time = time.time()

        async def execute_request(req: Dict[str, Any], idx: int) -> AsyncTaskResult:
            """Execute single HTTP request."""
            async with self.semaphore:
                task_start = time.time()

                try:
                    url = req['url']
                    method = req.get('method', 'GET')
                    headers = req.get('headers', {})
                    data = req.get('data')
                    json_data = req.get('json')

                    async with self.http_session.request(
                            method=method,
                            url=url,
                            headers=headers,
                            data=data,
                            json=json_data
                    ) as response:
                        result_data = await response.text()
                        status = response.status

                        # Try to parse JSON if content-type indicates it
                        if 'application/json' in response.headers.get('content-type', ''):
                            try:
                                result_data = json.loads(result_data)
                            except json.JSONDecodeError:
                                pass  # Keep as text

                        return AsyncTaskResult(
                            task_id=f"http_{idx}",
                            success=status < 400,
                            result={'status': status, 'data': result_data, 'headers': dict(response.headers)},
                            error=None,
                            execution_time=time.time() - task_start,
                            timestamp=time.time()
                        )

                except Exception as e:
                    return AsyncTaskResult(
                        task_id=f"http_{idx}",
                        success=False,
                        result=None,
                        error=str(e),
                        execution_time=time.time() - task_start,
                        timestamp=time.time()
                    )

        # Execute all requests concurrently
        tasks = [execute_request(req, i) for i, req in enumerate(requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions in results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(AsyncTaskResult(
                    task_id="error",
                    success=False,
                    result=None,
                    error=str(result),
                    execution_time=0.0,
                    timestamp=time.time()
                ))
            else:
                processed_results.append(result)

        total_time = time.time() - start_time
        successful = sum(1 for r in processed_results if r.success)
        throughput = len(processed_results) / total_time if total_time > 0 else 0

        batch_result = BatchResult(
            total_tasks=len(requests),
            successful_tasks=successful,
            failed_tasks=len(requests) - successful,
            total_time=total_time,
            throughput=throughput,
            results=processed_results
        )

        logger.info(".2f"
                    f"successful: {successful}/{len(requests)}")

        return batch_result

    async def batch_file_operations(self, operations: List[Dict[str, Any]]) -> BatchResult:
        """Execute multiple file operations concurrently."""
        start_time = time.time()

        async def execute_file_op(op: Dict[str, Any], idx: int) -> AsyncTaskResult:
            """Execute single file operation."""
            async with self.semaphore:
                task_start = time.time()

                try:
                    op_type = op['type']
                    file_path = op['path']

                    if op_type == 'read':
                        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                            content = await f.read()
                        result = {'content': content, 'size': len(content)}

                    elif op_type == 'write':
                        content = op['content']
                        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                            await f.write(content)
                        result = {'bytes_written': len(content)}

                    elif op_type == 'append':
                        content = op['content']
                        async with aiofiles.open(file_path, 'a', encoding='utf-8') as f:
                            await f.write(content)
                        result = {'bytes_appended': len(content)}

                    else:
                        raise ValueError(f"Unsupported operation type: {op_type}")

                    return AsyncTaskResult(
                        task_id=f"file_{idx}",
                        success=True,
                        result=result,
                        error=None,
                        execution_time=time.time() - task_start,
                        timestamp=time.time()
                    )

                except Exception as e:
                    return AsyncTaskResult(
                        task_id=f"file_{idx}",
                        success=False,
                        result=None,
                        error=str(e),
                        execution_time=time.time() - task_start,
                        timestamp=time.time()
                    )

        # Execute all file operations concurrently
        tasks = [execute_file_op(op, i) for i, op in enumerate(operations)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(AsyncTaskResult(
                    task_id="error",
                    success=False,
                    result=None,
                    error=str(result),
                    execution_time=0.0,
                    timestamp=time.time()
                ))
            else:
                processed_results.append(result)

        total_time = time.time() - start_time
        successful = sum(1 for r in processed_results if r.success)
        throughput = len(processed_results) / total_time if total_time > 0 else 0

        return BatchResult(
            total_tasks=len(operations),
            successful_tasks=successful,
            failed_tasks=len(operations) - successful,
            total_time=total_time,
            throughput=throughput,
            results=processed_results
        )

    async def mixed_io_operations(self, http_requests: List[Dict], file_ops: List[Dict]) -> Dict[str, BatchResult]:
        """Execute HTTP and file operations concurrently."""
        # Run both types of operations in parallel
        http_task = self.batch_http_requests(http_requests)
        file_task = self.batch_file_operations(file_ops)

        http_result, file_result = await asyncio.gather(http_task, file_task)

        return {
            'http_requests': http_result,
            'file_operations': file_result
        }

    async def process_with_cpu_work(self, io_operations: List[Dict[str, Any]],
                                    cpu_callback: Callable) -> BatchResult:
        """Process I/O operations with CPU-intensive work."""
        start_time = time.time()

        async def process_with_cpu(op: Dict[str, Any], idx: int) -> AsyncTaskResult:
            """Process I/O operation followed by CPU work."""
            async with self.semaphore:
                task_start = time.time()

                try:
                    # First, do I/O operation
                    if 'url' in op:
                        # HTTP request
                        async with self.http_session.request(
                                method=op.get('method', 'GET'),
                                url=op['url'],
                                headers=op.get('headers', {}),
                                json=op.get('json')
                        ) as response:
                            io_result = await response.json()
                    else:
                        # File operation
                        async with aiofiles.open(op['path'], 'r') as f:
                            io_result = await f.read()

                    # Then do CPU work in thread pool
                    cpu_result = await asyncio.get_event_loop().run_in_executor(
                        self.thread_executor,
                        cpu_callback,
                        io_result,
                        op
                    )

                    return AsyncTaskResult(
                        task_id=f"mixed_{idx}",
                        success=True,
                        result={'io_result': io_result, 'cpu_result': cpu_result},
                        error=None,
                        execution_time=time.time() - task_start,
                        timestamp=time.time()
                    )

                except Exception as e:
                    return AsyncTaskResult(
                        task_id=f"mixed_{idx}",
                        success=False,
                        result=None,
                        error=str(e),
                        execution_time=time.time() - task_start,
                        timestamp=time.time()
                    )

        # Execute mixed operations
        tasks = [process_with_cpu(op, i) for i, op in enumerate(io_operations)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(AsyncTaskResult(
                    task_id="error",
                    success=False,
                    result=None,
                    error=str(result),
                    execution_time=0.0,
                    timestamp=time.time()
                ))
            else:
                processed_results.append(result)

        total_time = time.time() - start_time
        successful = sum(1 for r in processed_results if r.success)
        throughput = len(processed_results) / total_time if total_time > 0 else 0

        return BatchResult(
            total_tasks=len(io_operations),
            successful_tasks=successful,
            failed_tasks=len(io_operations) - successful,
            total_time=total_time,
            throughput=throughput,
            results=processed_results
        )

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            'max_concurrent': self.max_concurrent,
            'timeout': self.timeout,
            'thread_pool_workers': 4,
            'active_tasks': self.active_tasks,
            'completed_tasks': self.completed_tasks,
            'http_session_active': self.http_session is not None
        }
