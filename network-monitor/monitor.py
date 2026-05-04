#!/usr/bin/env python3
"""
Network Device Monitor
Monitors network devices for availability and response time.
Sends alerts when devices go down or exceed latency thresholds.

Author: Jack Ke Jiang
"""

import subprocess
import platform
import time
import csv
import yaml
import smtplib
import argparse
import sys
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path


def load_config(config_path="devices.yaml"):
    """Load device configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def ping_device(ip, count=3):
    """
    Ping a device and return (is_alive, avg_latency_ms).
    Works on both Windows and Linux.
    """
    param = "-n" if platform.system().lower() == "windows" else "-c"
    timeout_param = "-w" if platform.system().lower() == "windows" else "-W"

    try:
        result = subprocess.run(
            ["ping", param, str(count), timeout_param, "2", ip],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            # Parse average latency from ping output
            output = result.stdout
            if platform.system().lower() == "windows":
                # Windows: "Average = 5ms"
                for line in output.split("\n"):
                    if "Average" in line:
                        avg = line.split("=")[-1].strip().replace("ms", "")
                        return True, float(avg)
            else:
                # Linux: "rtt min/avg/max/mdev = 1.0/2.5/4.0/1.0 ms"
                for line in output.split("\n"):
                    if "avg" in line:
                        parts = line.split("=")[1].strip().split("/")
                        return True, float(parts[1])

            # Ping succeeded but couldn't parse latency
            return True, 0.0
        else:
            return False, 0.0

    except (subprocess.TimeoutExpired, Exception):
        return False, 0.0


def log_status(log_file, device_name, ip, status, latency_ms):
    """Append status entry to CSV log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = Path(log_file).exists()

    with open(log_file, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "device", "ip", "status", "latency_ms"])
        writer.writerow([timestamp, device_name, ip, status, f"{latency_ms:.1f}" if latency_ms else "---"])


def send_alert(config, device_name, ip, status, latency_ms=None):
    """Send email alert for device status change."""
    alert_config = config.get("alert", {})
    if not alert_config.get("email"):
        return

    subject = f"[NETWORK ALERT] {device_name} ({ip}) is {status}"

    if status == "DOWN":
        body = (
            f"Device: {device_name}\n"
            f"IP: {ip}\n"
            f"Status: UNREACHABLE\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Action required: Investigate connectivity to this device."
        )
    elif status == "HIGH_LATENCY":
        body = (
            f"Device: {device_name}\n"
            f"IP: {ip}\n"
            f"Status: HIGH LATENCY ({latency_ms:.1f}ms)\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Warning: Response time exceeds configured threshold."
        )
    else:
        body = (
            f"Device: {device_name}\n"
            f"IP: {ip}\n"
            f"Status: RECOVERED\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Device is back online."
        )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = alert_config.get("email")
    msg["To"] = alert_config.get("email")

    try:
        server = smtplib.SMTP(
            alert_config.get("smtp_server", "localhost"),
            alert_config.get("smtp_port", 587)
        )
        server.starttls()
        if alert_config.get("smtp_user") and alert_config.get("smtp_pass"):
            server.login(alert_config["smtp_user"], alert_config["smtp_pass"])
        server.sendmail(msg["From"], [msg["To"]], msg.as_string())
        server.quit()
        print(f"  ALERT sent to {alert_config['email']}")
    except Exception as e:
        print(f"  Failed to send alert: {e}")


def monitor_devices(config, run_once=False):
    """Main monitoring loop."""
    devices = config.get("devices", [])
    monitoring = config.get("monitoring", {})
    interval = monitoring.get("interval_seconds", 60)
    retry_count = monitoring.get("retry_count", 3)
    log_file = monitoring.get("log_file", "status_log.csv")

    # Track previous status for change detection
    previous_status = {}

    print("=" * 70)
    print("  NETWORK DEVICE MONITOR")
    print(f"  Monitoring {len(devices)} devices | Interval: {interval}s | Retries: {retry_count}")
    print("=" * 70)
    print()

    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"--- Check at {timestamp} ---")

        for device in devices:
            name = device["name"]
            ip = device["ip"]
            threshold = device.get("threshold_ms", 100)

            is_alive, latency = ping_device(ip, count=retry_count)

            if is_alive:
                if latency > threshold:
                    status = "HIGH_LATENCY"
                    print(f"  {name:30s} | {ip:15s} | WARNING | {latency:.1f}ms (threshold: {threshold}ms)")
                else:
                    status = "UP"
                    print(f"  {name:30s} | {ip:15s} | UP      | {latency:.1f}ms")
            else:
                status = "DOWN"
                print(f"  {name:30s} | {ip:15s} | DOWN    | ---")

            # Log status
            log_status(log_file, name, ip, status, latency)

            # Check for status change and send alert
            prev = previous_status.get(ip)
            if prev and prev != status:
                if status == "DOWN":
                    send_alert(config, name, ip, "DOWN")
                elif status == "HIGH_LATENCY":
                    send_alert(config, name, ip, "HIGH_LATENCY", latency)
                elif prev in ("DOWN", "HIGH_LATENCY") and status == "UP":
                    send_alert(config, name, ip, "RECOVERED")

            previous_status[ip] = status

        print()

        if run_once:
            break

        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Network Device Monitor")
    parser.add_argument("--config", default="devices.yaml", help="Path to config file")
    parser.add_argument("--once", action="store_true", help="Run a single check and exit")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"Error: Config file '{args.config}' not found.")
        print("Create a devices.yaml file with your network devices. See README for format.")
        sys.exit(1)

    try:
        monitor_devices(config, run_once=args.once)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
