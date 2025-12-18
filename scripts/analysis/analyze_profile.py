
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
"""
Analyze Python profiling data to find performance bottlenecks
"""

import pstats
import sys
from pathlib import Path


def analyze_profile(profile_file):
    """Analyze profiling data and identify bottlenecks."""
    print(f"=== Analyzing Profile: {profile_file} ===")

    # Load profile data
    stats = pstats.Stats(profile_file)

    print("\n=== TOP 20 MOST TIME-CONSUMING FUNCTIONS ===")
    stats.sort_stats('cumulative').print_stats(20)

    print("\n=== TOP 20 FUNCTIONS BY INTERNAL TIME ===")
    stats.sort_stats('time').print_stats(20)

    print("\n=== TOP 20 FUNCTIONS BY CALL COUNT ===")
    stats.sort_stats('calls').print_stats(20)

    print("\n=== FUNCTIONS WITH HIGHEST AVERAGE TIME PER CALL ===")
    # Get stats data
    stats_dict = {}
    for func, (cc, nc, tt, ct, callers) in stats.stats.items():
        if nc > 0:  # Avoid division by zero
            avg_time = tt / nc
            stats_dict[func] = {
                'calls': nc,
                'total_time': tt,
                'cumulative_time': ct,
                'avg_time': avg_time
            }

    # Sort by average time
    sorted_by_avg = sorted(stats_dict.items(), key=lambda x: x[1]['avg_time'], reverse=True)

    print("Function".ljust(60), "Calls".rjust(8), "Avg Time".rjust(12), "Total Time".rjust(12))
    print("-" * 95)
    for func, data in sorted_by_avg[:20]:
        func_name = f"{func[0]}:{func[1]}({func[2]})"
        if len(func_name) > 58:
            func_name = func_name[:55] + "..."
        print(f"{func_name:<60} {data['calls']:>8} {data['avg_time']:>12.6f} {data['total_time']:>12.6f}")

    print("\n=== POTENTIAL BOTTLENECKS IDENTIFIED ===")

    # Identify potential bottlenecks
    bottlenecks = []

    for func, data in sorted_by_avg[:50]:  # Check top 50
        func_name = f"{func[0]}:{func[1]}({func[2]})"

        # High average time per call (>0.001 seconds)
        if data['avg_time'] > 0.001 and data['calls'] > 10:
            bottlenecks.append({
                'type': 'HIGH_AVERAGE_TIME',
                'function': func_name,
                'calls': data['calls'],
                'avg_time': data['avg_time'],
                'total_time': data['total_time']
            })

        # Functions called many times with significant total time
        if data['calls'] > 1000 and data['total_time'] > 0.1:
            bottlenecks.append({
                'type': 'FREQUENT_CALLS',
                'function': func_name,
                'calls': data['calls'],
                'avg_time': data['avg_time'],
                'total_time': data['total_time']
            })

    if not bottlenecks:
        print("✅ No significant bottlenecks detected!")
        return

    # Sort bottlenecks by impact (total time)
    bottlenecks.sort(key=lambda x: x['total_time'], reverse=True)

    for i, bottleneck in enumerate(bottlenecks[:10], 1):
        print(f"\n{i}. {bottleneck['type']}: {bottleneck['function']}")
        print(f"   Calls: {bottleneck['calls']:,}")
        print(f"   Avg time per call: {bottleneck['avg_time']:.6f}s")
        print(f"   Total time: {bottleneck['total_time']:.6f}s")

    print(f"\n=== SUMMARY ===")
    print(f"Total functions profiled: {len(stats_dict)}")
    print(f"Potential bottlenecks found: {len(bottlenecks)}")

    # Calculate total time
    total_time = sum(data['total_time'] for data in stats_dict.values())
    print(f"Total execution time: {total_time:.6f}s")


if __name__ == "__main__":
    profile_file = r"C:\Users\Admin\AppData\Local\JetBrains\PyCharm2025.1\snapshots\supreme-octo-succotash\supreme-octo-succotash2.pstat"

    if not Path(profile_file).exists():
        print(f"Profile file not found: {profile_file}")
        sys.exit(1)

    analyze_profile(profile_file)
