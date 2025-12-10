#!/usr/bin/env python3
"""
System resource monitor for performance testing
"""

import psutil
import time
import json
from datetime import datetime
from typing import Dict, List, Any
import threading
import matplotlib.pyplot as plt


class SystemMonitor:
    """Monitor system resources during performance tests"""

    def __init__(self, duration: int = 60, interval: float = 1.0):
        self.duration = duration
        self.interval = interval
        self.monitoring = False
        self.metrics = {
            'timestamp': [],
            'cpu_percent': [],
            'cpu_per_core': [],
            'memory_percent': [],
            'memory_used': [],
            'memory_available': [],
            'disk_usage': [],
            'network_sent': [],
            'network_recv': [],
            'connections': []
        }

        # Get initial network stats
        self.initial_net = psutil.net_io_counters()

    def start_monitoring(self):
        """Start system monitoring in background thread"""
        self.monitoring = True
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        print("📊 System monitoring started")

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        print("📊 System monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        end_time = time.time() + self.duration

        while self.monitoring and time.time() < end_time:
            self._collect_metrics()
            time.sleep(self.interval)

    def _collect_metrics(self):
        """Collect system metrics"""
        timestamp = datetime.now().isoformat()

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_per_core = psutil.cpu_percent(percpu=True)

        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used = memory.used / (1024**3)  # GB
        memory_available = memory.available / (1024**3)  # GB

        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent

        # Network metrics
        net = psutil.net_io_counters()
        net_sent = (net.bytes_sent - self.initial_net.bytes_sent) / (1024**2)  # MB
        net_recv = (net.bytes_recv - self.initial_net.bytes_recv) / (1024**2)  # MB

        # Connection metrics
        connections = len(psutil.net_connections())

        # Store metrics
        self.metrics['timestamp'].append(timestamp)
        self.metrics['cpu_percent'].append(cpu_percent)
        self.metrics['cpu_per_core'].append(cpu_per_core)
        self.metrics['memory_percent'].append(memory_percent)
        self.metrics['memory_used'].append(memory_used)
        self.metrics['memory_available'].append(memory_available)
        self.metrics['disk_usage'].append(disk_percent)
        self.metrics['network_sent'].append(net_sent)
        self.metrics['network_recv'].append(net_recv)
        self.metrics['connections'].append(connections)

    def get_summary(self) -> Dict[str, Any]:
        """Get monitoring summary"""
        if not self.metrics['cpu_percent']:
            return {'error': 'No metrics collected'}

        cpu_percent = self.metrics['cpu_percent']
        memory_percent = self.metrics['memory_percent']

        return {
            'duration': len(cpu_percent) * self.interval,
            'samples': len(cpu_percent),
            'cpu': {
                'avg_percent': sum(cpu_percent) / len(cpu_percent),
                'max_percent': max(cpu_percent),
                'min_percent': min(cpu_percent)
            },
            'memory': {
                'avg_percent': sum(memory_percent) / len(memory_percent),
                'max_percent': max(memory_percent),
                'min_percent': min(memory_percent),
                'avg_used_gb': sum(self.metrics['memory_used']) / len(self.metrics['memory_used']),
                'avg_available_gb': sum(self.metrics['memory_available']) / len(self.metrics['memory_available'])
            },
            'network': {
                'total_sent_mb': max(self.metrics['network_sent']),
                'total_recv_mb': max(self.metrics['network_recv'])
            },
            'connections': {
                'avg_connections': sum(self.metrics['connections']) / len(self.metrics['connections']),
                'max_connections': max(self.metrics['connections'])
            }
        }

    def save_metrics(self, filename: str = "system_metrics.json"):
        """Save metrics to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, indent=2, ensure_ascii=False)
        print(f"📊 Metrics saved to {filename}")

    def create_charts(self, filename: str = "system_monitor.png"):
        """Create monitoring charts"""
        try:
            if len(self.metrics['timestamp']) < 2:
                print("⚠️  Not enough data for charts")
                return

            # Create time axis (relative time in seconds)
            time_axis = [i * self.interval for i in range(len(self.metrics['timestamp']))]

            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

            # CPU Usage
            ax1.plot(time_axis, self.metrics['cpu_percent'], 'r-', linewidth=2, label='Total CPU')
            ax1.set_title('CPU Usage Over Time')
            ax1.set_ylabel('CPU %')
            ax1.set_xlabel('Time (seconds)')
            ax1.grid(True, alpha=0.3)
            ax1.legend()

            # Memory Usage
            ax2.plot(time_axis, self.metrics['memory_percent'], 'b-', linewidth=2, label='Memory %')
            ax2.set_title('Memory Usage Over Time')
            ax2.set_ylabel('Memory %')
            ax2.set_xlabel('Time (seconds)')
            ax2.grid(True, alpha=0.3)
            ax2.legend()

            # Network I/O
            ax3.plot(time_axis, self.metrics['network_sent'], 'g-', linewidth=2, label='Sent (MB)')
            ax3.plot(time_axis, self.metrics['network_recv'], 'orange', linewidth=2, label='Received (MB)')
            ax3.set_title('Network I/O Over Time')
            ax3.set_ylabel('Data (MB)')
            ax3.set_xlabel('Time (seconds)')
            ax3.grid(True, alpha=0.3)
            ax3.legend()

            # Active Connections
            ax4.plot(time_axis, self.metrics['connections'], 'purple', linewidth=2, label='Connections')
            ax4.set_title('Active Connections Over Time')
            ax4.set_ylabel('Connections')
            ax4.set_xlabel('Time (seconds)')
            ax4.grid(True, alpha=0.3)
            ax4.legend()

            plt.tight_layout()
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"📊 System charts saved to {filename}")

        except ImportError:
            print("⚠️  Matplotlib not available for chart generation")
        except Exception as e:
            print(f"⚠️  Error creating charts: {e}")


def main():
    """Main monitoring function"""
    print("🖥️  SYSTEM RESOURCE MONITOR")
    print("=" * 40)

    # Configuration
    MONITOR_DURATION = 30  # seconds
    MONITOR_INTERVAL = 0.5  # seconds

    print(f"Monitoring duration: {MONITOR_DURATION}s")
    print(f"Sampling interval: {MONITOR_INTERVAL}s")
    print(f"Expected samples: {int(MONITOR_DURATION / MONITOR_INTERVAL)}")
    print()

    # Create monitor
    monitor = SystemMonitor(duration=MONITOR_DURATION, interval=MONITOR_INTERVAL)

    # Start monitoring
    monitor.start_monitoring()

    # Wait for monitoring to complete
    print("⏳ Monitoring system resources...")
    time.sleep(MONITOR_DURATION + 1)

    # Stop monitoring
    monitor.stop_monitoring()

    # Get summary
    summary = monitor.get_summary()

    if 'error' in summary:
        print(f"❌ Monitoring failed: {summary['error']}")
        return

    print("\n📊 MONITORING SUMMARY")
    print("=" * 40)
    print(f"Duration: {summary['duration']:.1f}s")
    print(f"Samples collected: {summary['samples']}")

    print("
CPU Usage:"    print(".1f"    print(".1f"    print(".1f"
    print("
Memory Usage:"    print(".1f"    print(".1f"    print(".1f"    print(".1f"    print(".1f"
    print("
Network I/O:"    print(".1f"    print(".1f"
    print("
Connections:"    print(".0f"    print(".0f"
    # Performance assessment
    print("\n🎯 PERFORMANCE ASSESSMENT")
    print("=" * 40)

    cpu_avg = summary['cpu']['avg_percent']
    cpu_max = summary['cpu']['max_percent']
    mem_avg = summary['memory']['avg_percent']
    mem_max = summary['memory']['max_percent']

    # CPU assessment
    if cpu_max < 50:
        print("✅ CPU: Excellent (low utilization)")
    elif cpu_max < 80:
        print("✅ CPU: Good (moderate utilization)")
    elif cpu_max < 95:
        print("⚠️  CPU: High utilization - consider optimization")
    else:
        print("❌ CPU: Critical - immediate optimization needed")

    # Memory assessment
    if mem_max < 70:
        print("✅ Memory: Excellent (good headroom)")
    elif mem_max < 85:
        print("✅ Memory: Good (adequate memory)")
    elif mem_max < 95:
        print("⚠️  Memory: High usage - monitor closely")
    else:
        print("❌ Memory: Critical - memory optimization needed")

    # Save data
    print("\n💾 Saving monitoring data...")
    monitor.save_metrics()
    monitor.create_charts()

    print("\n✅ System monitoring completed!")
    print("📊 Check system_metrics.json and system_monitor.png for detailed analysis")


if __name__ == "__main__":
    main()
