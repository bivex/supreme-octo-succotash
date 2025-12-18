
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:33
# Last Updated: 2025-12-18T12:28:33
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""PostgreSQL Auto Upholder Runner - скрипт для запуска автоматической оптимизации."""

import sys
import os
import logging
import argparse
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from infrastructure.upholder.postgres_auto_upholder import create_default_upholder
from container import container


def setup_logging(log_level: str = 'INFO'):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('postgres_upholder.log'),
            logging.StreamHandler()
        ]
    )


def run_once(connection) -> None:
    """Run one-time optimization audit."""
    print("🚀 Starting one-time PostgreSQL optimization audit...")

    upholder = create_default_upholder(connection)

    try:
        report = upholder.run_full_audit()

        print("\n✅ Audit completed!")
        print(f"⏱️  Duration: {report.duration_seconds:.2f} seconds")
        print(f"🔧 Optimizations applied: {len(report.optimizations_applied)}")
        print(f"🚨 Alerts generated: {len(report.alerts_generated)}")
        print(f"💡 Recommendations pending: {len(report.recommendations_pending)}")

        if report.alerts_generated:
            print("\n🚨 ALERTS:")
            for alert in report.alerts_generated[:10]:  # Show first 10
                print(f"  - {alert}")

        if report.recommendations_pending:
            print("\n💡 RECOMMENDATIONS:")
            for rec in report.recommendations_pending[:10]:  # Show first 10
                print(f"  - {rec}")

        if report.performance_improvements:
            print("\n📈 PERFORMANCE IMPROVEMENTS:")
            for key, value in report.performance_improvements.items():
                print(f"  - {key}: {value}")

        # Save detailed report
        report_file = f"upholder_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': report.timestamp.isoformat(),
                'duration_seconds': report.duration_seconds,
                'optimizations_applied': report.optimizations_applied,
                'alerts_generated': report.alerts_generated,
                'recommendations_pending': report.recommendations_pending,
                'performance_improvements': report.performance_improvements
            }, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: {report_file}")

    except Exception as e:
        print(f"❌ Audit failed: {e}")
        raise


def run_continuous(connection, duration_minutes: int = 60) -> None:
    """Run continuous optimization monitoring."""
    print(f"🚀 Starting continuous PostgreSQL optimization for {duration_minutes} minutes...")

    upholder = create_default_upholder(connection)
    upholder.start()

    try:
        import time
        end_time = time.time() + (duration_minutes * 60)

        while time.time() < end_time:
            time.sleep(60)  # Check every minute
            status = upholder.get_status()

            if status['last_report']:
                report = status['last_report']
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                     f"Report: {len(report.alerts_generated)} alerts, "
                     f"{len(report.recommendations_pending)} recommendations")

    except KeyboardInterrupt:
        print("\n⏹️  Stopping continuous monitoring...")
    finally:
        upholder.stop()
        print("✅ Continuous monitoring stopped")


def get_dashboard(connection) -> None:
    """Get current performance dashboard."""
    print("📊 Getting PostgreSQL performance dashboard...")

    upholder = create_default_upholder(connection)

    try:
        dashboard = upholder.get_performance_dashboard()

        print("\n=== POSTGRESQL PERFORMANCE DASHBOARD ===")

        # Status
        status = dashboard['upholder_status']
        print(f"🤖 Upholder Status: {'Running' if status['is_running'] else 'Stopped'}")
        print(f"⚙️  Auto-apply: {status['config']['auto_apply_optimizations']}")
        print(f"🧪 Dry-run: {status['config']['dry_run_mode']}")

        # Cache metrics
        cache = dashboard['current_metrics']['cache']
        print("\n💾 Cache Performance:")
        print(f"  Heap hit ratio: {cache['average_metrics'].get('heap_hit_ratio', 0):.1f}%")
        print(f"  Index hit ratio: {cache['average_metrics'].get('index_hit_ratio', 0):.1f}%")
        # Query performance
        query_perf = dashboard['current_metrics']['query_performance']
        if 'total_issues' in query_perf:
            print("\n🔍 Query Performance:")
            print(f"  Issues found: {query_perf['total_issues']}")

            if query_perf.get('top_slow_queries'):
                print("  Top slow queries:")
                for i, query in enumerate(query_perf['top_slow_queries'][:3], 1):
                    print(f"    {i}. {query.get('query', 'N/A')} ({query.get('mean_time', 0):.1f}ms)")
        # Recent alerts
        if dashboard.get('recent_alerts'):
            print("\n🚨 Recent Alerts:")
            for alert_info in dashboard['recent_alerts']:
                timestamp = alert_info['timestamp'][:19]  # YYYY-MM-DDTHH:MM:SS
                alerts = alert_info['alerts']
                if alerts:
                    print(f"  {timestamp}: {len(alerts)} alerts")
                    for alert in alerts[:2]:  # Show first 2 per report
                        print(f"    - {alert}")

    except Exception as e:
        print(f"❌ Failed to get dashboard: {e}")
        raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='PostgreSQL Auto Upholder Runner')
    parser.add_argument(
        'command',
        choices=['once', 'continuous', 'dashboard'],
        help='Command to run'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=60,
        help='Duration in minutes for continuous mode (default: 60)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # Get database connection
    try:
        connection = container.get_db_connection()
        print("✅ Database connection established")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return 1

    try:
        if args.command == 'once':
            run_once(connection)
        elif args.command == 'continuous':
            run_continuous(connection, args.duration)
        elif args.command == 'dashboard':
            get_dashboard(connection)

    except Exception as e:
        print(f"❌ Command failed: {e}")
        return 1
    finally:
        # Cleanup connection
        try:
            container.release_db_connection(connection)
        except:
            pass

    return 0


if __name__ == '__main__':
    sys.exit(main())
