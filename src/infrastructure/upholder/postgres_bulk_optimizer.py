# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:13:27
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Optimized bulk operations using vectorization and threading."""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class BulkOperationMetrics:
    """Metrics for bulk operations."""
    operation_type: str
    records_processed: int
    processing_time: float
    throughput: float  # records per second
    memory_usage: int  # bytes
    success_rate: float


class PostgresBulkOptimizer:
    """High-performance bulk operations optimizer using vectorization."""

    def __init__(self, connection_pool, max_workers: int = 4):
        self.connection_pool = connection_pool
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def vectorized_bulk_insert_clicks(self, clicks_data: List[Dict[str, Any]]) -> BulkOperationMetrics:
        """Vectorized bulk insert for clicks using pandas and numpy."""
        start_time = time.time()

        try:
            # Convert to DataFrame for vectorized operations
            df = pd.DataFrame(clicks_data)

            # Vectorized data validation and transformation
            df['is_valid'] = self._vectorized_validate_clicks(df)
            df['processed_at'] = pd.Timestamp.now()

            # Filter valid records using vectorized boolean indexing
            valid_clicks = df[df['is_valid']].copy()

            if len(valid_clicks) == 0:
                return BulkOperationMetrics(
                    operation_type="bulk_insert_clicks",
                    records_processed=0,
                    processing_time=time.time() - start_time,
                    throughput=0.0,
                    memory_usage=0,
                    success_rate=0.0
                )

            # Vectorized duplicate detection
            duplicates = self._vectorized_find_duplicates(valid_clicks)

            # Remove duplicates using vectorized operations
            if len(duplicates) > 0:
                valid_clicks = valid_clicks[~valid_clicks.index.isin(duplicates)]

            # Bulk insert using optimized COPY command
            success_count = self._bulk_insert_with_copy(valid_clicks)

            processing_time = time.time() - start_time
            throughput = success_count / processing_time if processing_time > 0 else 0

            return BulkOperationMetrics(
                operation_type="bulk_insert_clicks",
                records_processed=success_count,
                processing_time=processing_time,
                throughput=throughput,
                memory_usage=df.memory_usage(deep=True).sum(),
                success_rate=success_count / len(clicks_data)
            )

        except Exception as e:
            logger.error(f"Bulk insert failed: {e}")
            return BulkOperationMetrics(
                operation_type="bulk_insert_clicks",
                records_processed=0,
                processing_time=time.time() - start_time,
                throughput=0.0,
                memory_usage=0,
                success_rate=0.0
            )

    def _vectorized_validate_clicks(self, df: pd.DataFrame) -> np.ndarray:
        """Vectorized validation of click data."""
        # Vectorized null checks
        has_required_fields = (
                df['campaign_id'].notna() &
                df['click_id'].notna() &
                df['timestamp'].notna()
        )

        # Vectorized timestamp validation
        valid_timestamps = pd.to_datetime(df['timestamp'], errors='coerce').notna()

        # Vectorized URL validation (basic)
        valid_urls = df['referrer_url'].str.match(r'^https?://', na=False)

        return has_required_fields & valid_timestamps & valid_urls

    def _vectorized_find_duplicates(self, df: pd.DataFrame) -> np.ndarray:
        """Find duplicate clicks using vectorized operations."""
        # Vectorized duplicate detection by click_id
        duplicate_mask = df.duplicated(subset=['click_id'], keep='first')
        return df[duplicate_mask].index

    def _bulk_insert_with_copy(self, df: pd.DataFrame) -> int:
        """Bulk insert using PostgreSQL COPY for maximum performance."""
        conn = self.connection_pool.getconn()
        try:
            # Convert DataFrame to CSV format in memory
            csv_data = df.to_csv(index=False, header=False, sep='\t')

            # Use COPY command for bulk insert
            with conn.cursor() as cursor:
                cursor.copy_expert("""
                    COPY clicks (
                        campaign_id, click_id, timestamp, ip_address,
                        user_agent, referrer_url, is_valid, processed_at
                    ) FROM STDIN WITH (FORMAT csv, DELIMITER E'\t', HEADER false)
                """, csv_data)

            conn.commit()
            return len(df)

        finally:
            self.connection_pool.putconn(conn)

    async def parallel_bulk_operations(self, operations: List[Tuple[str, List[Dict]]]) -> Dict[
        str, BulkOperationMetrics]:
        """Execute multiple bulk operations in parallel using asyncio."""
        start_time = time.time()

        async def execute_operation(op_type: str, data: List[Dict]) -> Tuple[str, BulkOperationMetrics]:
            """Execute single operation in thread pool."""
            loop = asyncio.get_event_loop()

            if op_type == "clicks":
                result = await loop.run_in_executor(
                    self.executor,
                    self.vectorized_bulk_insert_clicks,
                    data
                )
            elif op_type == "conversions":
                result = await loop.run_in_executor(
                    self.executor,
                    self._bulk_insert_conversions,
                    data
                )
            else:
                # Default bulk insert
                result = await loop.run_in_executor(
                    self.executor,
                    self._generic_bulk_insert,
                    op_type, data
                )

            return op_type, result

        # Execute all operations concurrently
        tasks = [execute_operation(op_type, data) for op_type, data in operations]
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time
        logger.info(".2f")

        return dict(results)

    def _bulk_insert_conversions(self, conversions_data: List[Dict]) -> BulkOperationMetrics:
        """Bulk insert conversions with vectorized processing."""
        # Similar implementation to clicks but for conversions
        start_time = time.time()

        try:
            df = pd.DataFrame(conversions_data)

            # Vectorized validation
            df['is_valid'] = self._vectorized_validate_conversions(df)
            valid_conversions = df[df['is_valid']]

            if len(valid_conversions) == 0:
                return BulkOperationMetrics(
                    operation_type="bulk_insert_conversions",
                    records_processed=0,
                    processing_time=time.time() - start_time,
                    throughput=0.0,
                    memory_usage=0,
                    success_rate=0.0
                )

            # Bulk insert
            success_count = self._bulk_insert_with_copy_conversions(valid_conversions)

            processing_time = time.time() - start_time
            throughput = success_count / processing_time if processing_time > 0 else 0

            return BulkOperationMetrics(
                operation_type="bulk_insert_conversions",
                records_processed=success_count,
                processing_time=processing_time,
                throughput=throughput,
                memory_usage=df.memory_usage(deep=True).sum(),
                success_rate=success_count / len(conversions_data)
            )

        except Exception as e:
            logger.error(f"Bulk conversions insert failed: {e}")
            return BulkOperationMetrics(
                operation_type="bulk_insert_conversions",
                records_processed=0,
                processing_time=time.time() - start_time,
                throughput=0.0,
                memory_usage=0,
                success_rate=0.0
            )

    def _vectorized_validate_conversions(self, df: pd.DataFrame) -> np.ndarray:
        """Vectorized validation for conversions."""
        has_required = (
                df['click_id'].notna() &
                df['conversion_type'].notna() &
                df['timestamp'].notna() &
                df['amount'].notna()
        )

        # Vectorized amount validation
        valid_amounts = df['amount'] >= 0

        return has_required & valid_amounts

    def _bulk_insert_with_copy_conversions(self, df: pd.DataFrame) -> int:
        """Bulk insert conversions using COPY."""
        conn = self.connection_pool.getconn()
        try:
            csv_data = df.to_csv(index=False, header=False, sep='\t')

            with conn.cursor() as cursor:
                cursor.copy_expert("""
                    COPY conversions (
                        click_id, conversion_type, timestamp, amount,
                        currency, is_valid, processed_at
                    ) FROM STDIN WITH (FORMAT csv, DELIMITER E'\t', HEADER false)
                """, csv_data)

            conn.commit()
            return len(df)

        finally:
            self.connection_pool.putconn(conn)

    def _generic_bulk_insert(self, table_name: str, data: List[Dict]) -> BulkOperationMetrics:
        """Generic bulk insert for any table."""
        start_time = time.time()

        try:
            df = pd.DataFrame(data)
            csv_data = df.to_csv(index=False, header=False, sep='\t')

            conn = self.connection_pool.getconn()
            try:
                with conn.cursor() as cursor:
                    # Generic COPY command
                    columns = ', '.join(df.columns)
                    cursor.copy_expert(f"""
                        COPY {table_name} ({columns})
                        FROM STDIN WITH (FORMAT csv, DELIMITER E'\t', HEADER false)
                    """, csv_data)

                conn.commit()
                success_count = len(df)

            finally:
                self.connection_pool.putconn(conn)

            processing_time = time.time() - start_time
            throughput = success_count / processing_time if processing_time > 0 else 0

            return BulkOperationMetrics(
                operation_type=f"bulk_insert_{table_name}",
                records_processed=success_count,
                processing_time=processing_time,
                throughput=throughput,
                memory_usage=df.memory_usage(deep=True).sum(),
                success_rate=1.0
            )

        except Exception as e:
            logger.error(f"Generic bulk insert failed for {table_name}: {e}")
            return BulkOperationMetrics(
                operation_type=f"bulk_insert_{table_name}",
                records_processed=0,
                processing_time=time.time() - start_time,
                throughput=0.0,
                memory_usage=0,
                success_rate=0.0
            )
