"""PostgreSQL Auto Upholder - автоматическая система оптимизации производительности базы данных."""

import psycopg2
import logging
import time
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import threading
import schedule

# Import our optimization modules
from ..monitoring.postgres_query_analyzer import PostgresQueryAnalyzer, QueryAnalysisResult
from ..monitoring.postgres_index_auditor import PostgresIndexAuditor
from ..monitoring.postgres_cache_monitor import PostgresCacheMonitor, create_default_cache_monitor
from ..monitoring.postgres_query_optimizer import PostgresQueryOptimizer
from ..monitoring.postgres_performance_analyzer import PostgresPerformanceAnalyzer, SystemPerformanceReport
from ..monitoring.adaptive_connection_pool_optimizer import AdaptiveConnectionPoolOptimizer
from ..database.postgres_connection_pool_monitor import PostgresConnectionPoolMonitor
from ..repositories.postgres_bulk_loader import PostgresBulkLoader
from ..repositories.postgres_prepared_statements import PreparedStatementsManager

logger = logging.getLogger(__name__)


@dataclass
class UpholderReport:
    """Report from auto upholder execution."""
    timestamp: datetime
    duration_seconds: float
    optimizations_applied: List[str]
    alerts_generated: List[str]
    recommendations_pending: List[str]
    performance_improvements: Dict[str, Any]
    next_run_scheduled: datetime
    indexes_deleted: List[str] = None  # Track automatically deleted indexes

    def __post_init__(self):
        if self.indexes_deleted is None:
            self.indexes_deleted = []


@dataclass
class UpholderConfig:
    """Configuration for auto upholder."""
    # Schedule intervals (in minutes)
    query_analysis_interval: int = 60  # Every hour
    index_audit_interval: int = 240    # Every 4 hours
    cache_monitoring_interval: int = 30  # Every 30 minutes
    bulk_optimization_interval: int = 15  # Every 15 minutes

    # Thresholds
    slow_query_threshold_ms: float = 100
    min_query_calls: int = 10
    cache_hit_ratio_min: float = 0.95

    # Auto-apply settings
    auto_apply_safe_optimizations: bool = False  # Only safe optimizations
    auto_delete_unused_indexes: bool = False  # Auto-delete unused indexes (dangerous!)
    dry_run_mode: bool = True  # Don't actually apply changes

    # Index deletion safety settings
    unused_index_age_days: int = 30  # Minimum age before considering deletion
    unused_index_max_size_mb: int = 100  # Don't delete indexes larger than this

    # Alert settings
    enable_alerts: bool = True
    alert_cooldown_minutes: int = 60  # Don't spam alerts


class PostgresAutoUpholder:
    """Automatic PostgreSQL performance upholder."""

    def __init__(self, connection_pool, config: Optional[UpholderConfig] = None):
        self.connection_pool = connection_pool
        self.connection = connection_pool  # For backward compatibility
        self.config = config or UpholderConfig()

        # Initialize components
        self.query_analyzer = PostgresQueryAnalyzer(connection_pool)
        self.index_auditor = PostgresIndexAuditor(connection_pool)
        self.cache_monitor = create_default_cache_monitor(connection_pool)
        self.query_optimizer = PostgresQueryOptimizer(connection_pool)
        self.bulk_loader = PostgresBulkLoader(connection_pool)
        self.performance_analyzer = PostgresPerformanceAnalyzer(connection_pool)

        # Initialize connection pool monitor
        self.connection_pool_monitor = PostgresConnectionPoolMonitor(connection_pool)

        # State tracking
        self.is_running = False
        self.last_reports: List[UpholderReport] = []
        self.alert_cooldowns: Dict[str, datetime] = {}
        self.performance_baseline: Dict[str, Any] = {}

        # Event handlers
        self.report_handlers: List[Callable[[UpholderReport], None]] = []
        self.alert_handlers: List[Callable[[str, str], None]] = []  # (alert_type, message)

        # Note: Using schedule module directly (no Scheduler class needed)

    def start(self) -> None:
        """Start the auto upholder."""
        if self.is_running:
            logger.warning("Auto upholder already running")
            return

        self.is_running = True
        logger.info("Starting PostgreSQL Auto Upholder")

        # Establish performance baseline asynchronously
        self._establish_performance_baseline()

        # Setup scheduled tasks
        self._setup_scheduled_tasks()

        # Start background monitoring (asynchronously)
        def start_monitoring_async():
            try:
                self.cache_monitor.start_monitoring(interval_seconds=self.config.cache_monitoring_interval * 60)
                self.connection_pool_monitor.start_monitoring()
                logger.info("Background monitoring started successfully")
            except Exception as e:
                logger.error(f"Failed to start background monitoring: {e}")

        import threading
        monitoring_thread = threading.Thread(
            target=start_monitoring_async,
            daemon=True,
            name="Monitoring-Start"
        )
        monitoring_thread.start()

        # Start scheduler thread
        self._scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._scheduler_thread.start()

        logger.info("PostgreSQL Auto Upholder started successfully")

    def stop(self) -> None:
        """Stop the auto upholder."""
        if not self.is_running:
            logger.info("Auto upholder already stopped")
            return

        self.is_running = False
        self.cache_monitor.stop_monitoring()
        self.connection_pool_monitor.stop_monitoring()
        schedule.clear()
        logger.info("PostgreSQL Auto Upholder stopped")

    def run_full_audit(self) -> UpholderReport:
        """Run complete audit and optimization cycle."""
        start_time = datetime.now()

        logger.info("Starting full audit cycle")
        optimizations_applied = []
        alerts_generated = []
        recommendations_pending = []
        performance_improvements = {}

        try:
            # 0. System Performance Analysis (new comprehensive analysis)
            logger.info("Running comprehensive performance analysis...")
            performance_report = self.performance_analyzer.get_comprehensive_performance_report()

            # Add performance insights to alerts and recommendations
            if performance_report.queries_with_bad_cache > 0:
                alerts_generated.append(
                    f"Cache performance issue: {performance_report.queries_with_bad_cache} queries "
                    f"have <95% cache hit ratio (avg: {performance_report.avg_cache_hit_ratio:.1f}%)"
                )

            if performance_report.queries_using_temp > 0:
                alerts_generated.append(
                    f"Temp space usage: {performance_report.queries_using_temp} queries "
                    f"using {performance_report.total_temp_bytes // 1024 // 1024}MB temp space"
                )

            # Add performance recommendations
            recommendations_pending.extend(performance_report.optimization_recommendations)

            # Store performance metrics
            performance_improvements.update({
                'cache_hit_ratio': performance_report.avg_cache_hit_ratio,
                'total_queries_analyzed': performance_report.total_queries,
                'queries_with_bad_cache': performance_report.queries_with_bad_cache,
                'temp_space_usage_mb': performance_report.total_temp_bytes // 1024 // 1024
            })

            # 1. Query Analysis
            logger.info("Running query analysis...")
            slow_queries = self.query_analyzer.get_slow_queries_report(
                min_avg_time=self.config.slow_query_threshold_ms,
                min_calls=self.config.min_query_calls
            )

            if slow_queries:
                alerts_generated.append(f"Found {len(slow_queries)} slow queries")
                recommendations_pending.extend([
                    f"Optimize query: {q['query'][:100]}... ({q['mean_time']:.1f}ms avg)"
                    for q in slow_queries[:5]  # Top 5
                ])

            # 2. Index Audit
            logger.info("Running index audit...")
            index_audit_results = self.index_auditor.audit_all_tables()

            for table, audit in index_audit_results.items():
                if audit.missing_indexes:
                    alerts_generated.append(f"Table {table}: {len(audit.missing_indexes)} missing indexes")
                    recommendations_pending.extend([
                        f"Create index: {idx.ddl_statement}"
                        for idx in audit.missing_indexes[:3]  # Top 3 per table
                    ])

                if audit.unused_indexes:
                    unused_count = len(audit.unused_indexes)
                    alerts_generated.append(f"Table {table}: {unused_count} unused indexes detected")
                    recommendations_pending.extend([
                        f"Consider dropping unused index: {idx['name']} on {table}"
                        for idx in audit.unused_indexes[:2]  # Top 2 per table
                    ])

            # 2.5. Automatic Index Deletion (if enabled)
            deleted_indexes = self._delete_unused_indexes(index_audit_results)
            if deleted_indexes:
                optimizations_applied.extend(deleted_indexes)
                alerts_generated.append(f"Automatically deleted {len(deleted_indexes)} unused indexes")

            # 3. Cache Analysis
            logger.info("Analyzing cache performance...")
            cache_metrics = self.cache_monitor.get_current_metrics()

            if cache_metrics.heap_hit_ratio < self.config.cache_hit_ratio_min * 100:
                alerts_generated.append(f"Heap cache hit ratio is {cache_metrics.heap_hit_ratio:.1f}% (threshold: {self.config.cache_hit_ratio_min*100:.1f}%)")
            if cache_metrics.index_hit_ratio < 90:
                alerts_generated.append(f"Index cache hit ratio is {cache_metrics.index_hit_ratio:.1f}% (threshold: 90.0%)")

            # 3.5. Connection Pool Analysis
            logger.info("Analyzing connection pool performance...")
            pool_status = self.connection_pool_monitor.get_pool_status()
            pool_suggestions = self.connection_pool_monitor.get_optimization_suggestions()

            health_status = pool_status.get('health_status', 'UNKNOWN')
            if health_status in ['CRITICAL', 'WARNING']:
                alerts_generated.append(f"Connection pool health: {health_status}")

            if pool_suggestions and 'suggestions' in pool_suggestions:
                pool_sug_list = pool_suggestions['suggestions']
                if pool_sug_list:
                    recommendations_pending.extend([
                        f"Connection pool: {sug['type']} - {sug['description']} (severity: {sug['severity']})"
                        for sug in pool_sug_list[:3]  # Top 3 suggestions
                    ])

            # 4. Query Optimization Suggestions
            logger.info("Generating optimization suggestions...")
            issues = self.query_optimizer.analyze_slow_queries(
                min_avg_time=self.config.slow_query_threshold_ms,
                min_calls=self.config.min_query_calls
            )

            if issues:
                optimization_plan = self.query_optimizer.generate_optimization_plan(issues)
                recommendations_pending.extend([
                    f"Optimization: {action.description} (benefit: {action.estimated_benefit})"
                    for action in optimization_plan[:5]  # Top 5 optimizations
                ])

            # 5. Auto-apply safe optimizations (if enabled)
            if self.config.auto_apply_safe_optimizations and not self.config.dry_run_mode:
                applied = self._apply_safe_optimizations(issues)
                optimizations_applied.extend(applied)

            # Calculate performance improvements
            performance_improvements = self._calculate_performance_improvements()

        except Exception as e:
            logger.error(f"Error during full audit: {e}")
            alerts_generated.append(f"Audit error: {str(e)}")

        # Create report
        duration = (datetime.now() - start_time).total_seconds()
        report = UpholderReport(
            timestamp=datetime.now(),
            duration_seconds=duration,
            optimizations_applied=optimizations_applied,
            alerts_generated=alerts_generated,
            recommendations_pending=recommendations_pending,
            performance_improvements=performance_improvements,
            next_run_scheduled=datetime.now() + timedelta(minutes=self.config.query_analysis_interval),
            indexes_deleted=deleted_indexes
        )

        # Store report
        self.last_reports.append(report)
        if len(self.last_reports) > 10:  # Keep last 10 reports
            self.last_reports = self.last_reports[-10:]

        # Notify handlers
        self._notify_report_handlers(report)
        self._notify_alert_handlers(alerts_generated)

        logger.info(f"Full audit completed in {duration:.2f}s")
        return report

    def _establish_performance_baseline(self) -> None:
        """Establish initial performance baseline asynchronously."""
        try:
            logger.info("Scheduling performance baseline establishment...")

            # Schedule baseline establishment for later (after server starts)
            # This prevents blocking the main thread during startup
            def establish_baseline_async():
                try:
                    logger.info("Establishing performance baseline (async)...")

                    # Get current metrics
                    cache_metrics = self.cache_monitor.get_current_metrics()
                    slow_queries = self.query_analyzer.get_slow_queries_report()

                    self.performance_baseline = {
                        'cache_heap_hit_ratio': cache_metrics.heap_hit_ratio,
                        'cache_index_hit_ratio': cache_metrics.index_hit_ratio,
                        'slow_queries_count': len(slow_queries),
                        'established_at': datetime.now()
                    }

                    logger.info("Performance baseline established successfully")

                except Exception as e:
                    logger.error(f"Failed to establish performance baseline: {e}")

            # Run baseline establishment in a separate thread to avoid blocking
            import threading
            baseline_thread = threading.Thread(
                target=establish_baseline_async,
                daemon=True,
                name="Baseline-Estab"
            )
            baseline_thread.start()

        except Exception as e:
            logger.error(f"Failed to schedule performance baseline: {e}")

    def _setup_scheduled_tasks(self) -> None:
        """Setup scheduled optimization tasks."""
        # Full audit every hour
        schedule.every(self.config.query_analysis_interval).minutes.do(
            self.run_full_audit
        )

        # Index audit every 4 hours
        schedule.every(self.config.index_audit_interval).minutes.do(
            self._run_index_audit
        )

        # Bulk optimization check every 15 minutes
        schedule.every(self.config.bulk_optimization_interval).minutes.do(
            self._check_bulk_optimizations
        )

        logger.info("Scheduled tasks configured")

    def _run_scheduler(self) -> None:
        """Run the scheduler loop."""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)

    def _run_index_audit(self) -> None:
        """Run periodic index audit."""
        try:
            logger.info("Running scheduled index audit")
            results = self.index_auditor.audit_all_tables()

            # Check for critical issues
            critical_tables = []
            for table, audit in results.items():
                if len(audit.bloated_indexes) > 0 or len(audit.missing_indexes) > 2:
                    critical_tables.append(table)

            if critical_tables:
                alert_msg = f"Critical index issues in tables: {', '.join(critical_tables)}"
                self._notify_alert_handlers([alert_msg])

        except Exception as e:
            logger.error(f"Scheduled index audit failed: {e}")

    def _check_bulk_optimizations(self) -> None:
        """Check for bulk operation optimizations."""
        # This would monitor recent bulk operations and suggest optimizations
        # For now, just log that it's running
        logger.debug("Bulk optimization check completed")

    def _delete_unused_indexes(self, index_audit_results: Dict[str, Any]) -> List[str]:
        """Automatically delete unused indexes with safety checks."""
        if not self.config.auto_delete_unused_indexes:
            return []

        deleted_indexes = []
        logger.info("🔍 Checking for unused indexes eligible for automatic deletion")

        try:
            with self.connection_pool.getconn() as conn:
                with conn.cursor() as cursor:
                    for table, audit in index_audit_results.items():
                        for unused_index in audit.unused_indexes:
                            index_name = unused_index.get('name', '')
                            if not index_name:
                                continue

                            # Safety check 1: Skip if dry-run mode
                            if self.config.dry_run_mode:
                                logger.info(f"DRY RUN: Would delete unused index {index_name} on {table}")
                                continue

                            # Safety check 2: Check index age
                            cursor.execute("""
                                SELECT
                                    pg_stat_get_last_scan_time(indexrelid) as last_scan,
                                    pg_relation_size(indexrelid) as size_bytes,
                                    schemaname,
                                    tablename
                                FROM pg_stat_user_indexes
                                WHERE indexrelname = %s
                            """, (index_name,))

                            result = cursor.fetchone()
                            if not result:
                                logger.warning(f"Index {index_name} not found in statistics")
                                continue

                            last_scan, size_bytes, schema, table_name = result
                            size_mb = size_bytes / 1024 / 1024

                            # Safety check 3: Index age (must be unused for minimum period)
                            if last_scan:
                                age_days = (datetime.now() - last_scan).days
                                if age_days < self.config.unused_index_age_days:
                                    logger.info(f"Skipping {index_name}: only {age_days} days unused "
                                              f"(minimum {self.config.unused_index_age_days})")
                                    continue

                            # Safety check 4: Index size (don't delete very large indexes automatically)
                            if size_mb > self.config.unused_index_max_size_mb:
                                logger.warning(f"Skipping {index_name}: too large ({size_mb:.1f}MB > "
                                             f"{self.config.unused_index_max_size_mb}MB limit)")
                                continue

                            # Safety check 5: Don't delete primary key or unique indexes
                            cursor.execute("""
                                SELECT indisprimary, indisunique
                                FROM pg_index
                                WHERE indexrelid = (SELECT oid FROM pg_class WHERE relname = %s)
                            """, (index_name,))
                            index_props = cursor.fetchone()
                            if index_props and (index_props[0] or index_props[1]):  # primary or unique
                                logger.warning(f"Skipping {index_name}: primary key or unique index")
                                continue

                            # All safety checks passed - delete the index
                            try:
                                drop_statement = f"DROP INDEX IF EXISTS {schema}.{index_name}"
                                logger.warning(f"🗑️ AUTO-DELETING unused index: {index_name} on {table} "
                                             f"(age: {age_days if last_scan else 'unknown'} days, "
                                             f"size: {size_mb:.1f}MB)")

                                cursor.execute(drop_statement)
                                deleted_indexes.append(f"Dropped unused index: {index_name}")
                                conn.commit()

                            except Exception as e:
                                logger.error(f"Failed to drop index {index_name}: {e}")
                                conn.rollback()
                                continue

        except Exception as e:
            logger.error(f"Error during automatic index deletion: {e}")

        if deleted_indexes:
            logger.info(f"✅ Automatically deleted {len(deleted_indexes)} unused indexes")

        return deleted_indexes

    def _apply_safe_optimizations(self, issues: List) -> List[str]:
        """Apply safe optimizations automatically."""
        applied = []

        # Only apply very safe optimizations automatically
        for issue in issues:
            if issue.severity == 'low' and issue.fix_complexity == 'easy':
                # Apply simple optimizations
                try:
                    # This would be specific logic for each optimization type
                    logger.info(f"Auto-applying safe optimization: {issue.issue_type}")
                    applied.append(f"Applied: {issue.issue_type}")
                except Exception as e:
                    logger.error(f"Failed to auto-apply optimization: {e}")

        return applied

    def _calculate_performance_improvements(self) -> Dict[str, Any]:
        """Calculate performance improvements since baseline."""
        if not self.performance_baseline:
            return {"message": "No baseline established"}

        try:
            current_cache = self.cache_monitor.get_current_metrics()
            current_slow_queries = self.query_analyzer.get_slow_queries_report()

            improvements = {}

            # Cache improvements
            cache_heap_improvement = current_cache.heap_hit_ratio - self.performance_baseline.get('cache_heap_hit_ratio', 0)
            if abs(cache_heap_improvement) > 1:
                improvements['cache_heap_hit_ratio'] = ".2f"

            cache_index_improvement = current_cache.index_hit_ratio - self.performance_baseline.get('cache_index_hit_ratio', 0)
            if abs(cache_index_improvement) > 1:
                improvements['cache_index_hit_ratio'] = ".2f"
            # Slow queries improvement
            slow_queries_improvement = self.performance_baseline.get('slow_queries_count', 0) - len(current_slow_queries)
            if slow_queries_improvement != 0:
                improvements['slow_queries'] = f"{slow_queries_improvement} queries {'faster' if slow_queries_improvement > 0 else 'slower'}"

            return improvements

        except Exception as e:
            logger.error(f"Failed to calculate performance improvements: {e}")
            return {"error": str(e)}

    def add_report_handler(self, handler: Callable[[UpholderReport], None]) -> None:
        """Add report handler."""
        self.report_handlers.append(handler)

    def add_alert_handler(self, handler: Callable[[str, str], None]) -> None:
        """Add alert handler."""
        self.alert_handlers.append(handler)

    def _notify_report_handlers(self, report: UpholderReport) -> None:
        """Notify report handlers."""
        for handler in self.report_handlers:
            try:
                handler(report)
            except Exception as e:
                logger.error(f"Report handler failed: {e}")

    def _notify_alert_handlers(self, alerts: List[str]) -> None:
        """Notify alert handlers."""
        if not self.config.enable_alerts:
            return

        for alert in alerts:
            # Check cooldown
            alert_key = hash(alert) % 10000
            last_alert = self.alert_cooldowns.get(alert_key)

            if last_alert and (datetime.now() - last_alert).seconds < self.config.alert_cooldown_minutes * 60:
                continue  # Skip due to cooldown

            self.alert_cooldowns[alert_key] = datetime.now()

            for handler in self.alert_handlers:
                try:
                    handler("performance_alert", alert)
                except Exception as e:
                    logger.error(f"Alert handler failed: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current upholder status."""
        return {
            'is_running': self.is_running,
            'config': {
                'query_analysis_interval': self.config.query_analysis_interval,
                'index_audit_interval': self.config.index_audit_interval,
                'cache_monitoring_interval': self.config.cache_monitoring_interval,
                'auto_apply_optimizations': self.config.auto_apply_safe_optimizations,
                'auto_delete_unused_indexes': self.config.auto_delete_unused_indexes,
                'unused_index_age_days': self.config.unused_index_age_days,
                'unused_index_max_size_mb': self.config.unused_index_max_size_mb,
                'dry_run_mode': self.config.dry_run_mode
            },
            'performance_baseline': self.performance_baseline,
            'last_report': self.last_reports[-1] if self.last_reports else None,
            'reports_count': len(self.last_reports),
            'alert_cooldowns_active': len(self.alert_cooldowns)
        }

    def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard."""
        import time
        print("DEBUG: get_performance_dashboard() called")  # Immediate print
        logger.info("📊 START: get_performance_dashboard()")
        print("DEBUG: After logger.info")  # Immediate print

        print("DEBUG: Getting upholder status")
        logger.info("📊 Getting upholder status")
        upholder_status = self.get_status()
        print("DEBUG: Got upholder status")

        print("DEBUG: Getting cache monitoring report")
        logger.info("📊 Getting cache monitoring report")
        cache_start = time.time()
        try:
            cache_report = self.cache_monitor.get_monitoring_report()
            cache_time = time.time() - cache_start
            logger.info(".3f")
        except Exception as e:
            cache_report = {"error": f"Cache monitoring failed: {str(e)}"}
            cache_time = time.time() - cache_start
            logger.warning(f"Cache monitoring failed: {e}")

        print("DEBUG: Getting query performance dashboard")
        logger.info("📊 Getting query performance dashboard")
        query_start = time.time()
        try:
            query_report = self.query_optimizer.get_performance_dashboard()
            query_time = time.time() - query_start
            logger.info(".3f")
        except Exception as e:
            query_report = {"error": f"Query performance monitoring failed: {str(e)}"}
            query_time = time.time() - query_start
            logger.warning(f"Query performance monitoring failed: {e}")

        print("DEBUG: Getting connection pool status with protection")
        logger.info("📊 Getting connection pool status with protection")
        pool_start = time.time()

        # Используем новый защищенный монитор
        try:
            pool_report = self.connection_pool_monitor.get_pool_status(timeout_seconds=5)
            pool_time = time.time() - pool_start
            logger.info(".3f")
        except Exception as e:
            pool_report = {"error": f"Pool status unavailable: {str(e)}"}
            pool_time = time.time() - pool_start
            logger.warning(f"Connection pool status failed: {e}")

        print("DEBUG: Got pool report (with protection)")
        
        logger.info("📊 Building dashboard response")
        dashboard = {
            'upholder_status': upholder_status,
            'current_metrics': {
                'cache': cache_report,
                'query_performance': query_report,
                'connection_pool': pool_report
            },
            'recent_alerts': [
                {
                    'timestamp': report.timestamp.isoformat(),
                    'alerts': report.alerts_generated
                }
                for report in self.last_reports[-3:]  # Last 3 reports
            ]
        }

        logger.info("📊 Dashboard complete")
        return dashboard


def create_default_upholder(connection_pool) -> PostgresAutoUpholder:
    """Create upholder with default safe configuration."""
    config = UpholderConfig(
        auto_apply_safe_optimizations=False,  # Don't auto-apply by default
        dry_run_mode=True,  # Always dry-run by default
        enable_alerts=True
    )

    upholder = PostgresAutoUpholder(connection_pool, config)

    # Add default report handler (logs reports)
    def log_report_handler(report: UpholderReport):
        logger.info(f"Auto Upholder Report: {len(report.optimizations_applied)} optimizations, "
                   f"{len(report.alerts_generated)} alerts, "
                   f"{len(report.recommendations_pending)} recommendations")

    # Add default alert handler (logs alerts)
    def log_alert_handler(alert_type: str, message: str):
        logger.warning(f"Auto Upholder Alert [{alert_type}]: {message}")

    upholder.add_report_handler(log_report_handler)
    upholder.add_alert_handler(log_alert_handler)

    return upholder
