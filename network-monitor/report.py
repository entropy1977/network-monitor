#!/usr/bin/env python3
"""
Network Availability Report Generator
Reads the status log and generates an availability summary report.

Author: Jack Ke Jiang
"""

import csv
import argparse
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path


def generate_report(log_file="status_log.csv", hours=24):
    """Generate availability report from log data."""

    if not Path(log_file).exists():
        print(f"Error: Log file '{log_file}' not found. Run monitor.py first.")
        return

    cutoff_time = datetime.now() - timedelta(hours=hours)

    # Collect data per device
    device_stats = defaultdict(lambda: {"total_checks": 0, "up_checks": 0, "down_checks": 0,
                                         "high_latency": 0, "latencies": [], "type": ""})

    with open(log_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                timestamp = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")
            except (ValueError, KeyError):
                continue

            if timestamp < cutoff_time:
                continue

            device = row["device"]
            status = row["status"]
            latency = row.get("latency_ms", "---")

            device_stats[device]["total_checks"] += 1

            if status == "UP":
                device_stats[device]["up_checks"] += 1
                if latency != "---":
                    try:
                        device_stats[device]["latencies"].append(float(latency))
                    except ValueError:
                        pass
            elif status == "DOWN":
                device_stats[device]["down_checks"] += 1
            elif status == "HIGH_LATENCY":
                device_stats[device]["high_latency"] += 1
                if latency != "---":
                    try:
                        device_stats[device]["latencies"].append(float(latency))
                    except ValueError:
                        pass

    # Print report
    print("=" * 75)
    print(f"  NETWORK AVAILABILITY REPORT — Last {hours} hours")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)
    print()
    print(f"  {'Device':<25s} {'Availability':>12s} {'Avg Latency':>12s} {'Down':>6s} {'Warnings':>9s}")
    print(f"  {'-'*25} {'-'*12} {'-'*12} {'-'*6} {'-'*9}")

    for device, stats in sorted(device_stats.items()):
        total = stats["total_checks"]
        if total == 0:
            continue

        availability = (stats["up_checks"] + stats["high_latency"]) / total * 100
        avg_latency = sum(stats["latencies"]) / len(stats["latencies"]) if stats["latencies"] else 0

        print(f"  {device:<25s} {availability:>10.1f}%  {avg_latency:>9.1f}ms  {stats['down_checks']:>5d}  {stats['high_latency']:>8d}")

    print()
    print("=" * 75)

    # Summary
    total_devices = len(device_stats)
    all_up = sum(1 for d in device_stats.values() if d["down_checks"] == 0)
    print(f"  Summary: {all_up}/{total_devices} devices had 100% availability")
    print("=" * 75)


def main():
    parser = argparse.ArgumentParser(description="Network Availability Report")
    parser.add_argument("--log", default="status_log.csv", help="Path to log file")
    parser.add_argument("--hours", type=int, default=24, help="Hours to report on (default: 24)")
    args = parser.parse_args()

    generate_report(args.log, args.hours)


if __name__ == "__main__":
    main()
