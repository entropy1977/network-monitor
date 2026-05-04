# Network Device Monitor

A lightweight Python-based network monitoring tool that checks the availability and response time of network devices (routers, switches, firewalls, servers) and sends alerts when devices go down or experience high latency.

## Why I Built This

In my previous role as Senior IT Engineer, I managed enterprise LAN/WAN infrastructure across eight departments. Proactive monitoring was critical — identifying issues before users reported them saved hours of troubleshooting and minimized service impact. This project demonstrates the kind of monitoring logic I implemented using Zabbix/SNMP in production environments, distilled into a standalone Python script.

## Features

- **Ping monitoring** — checks device availability via ICMP
- **Response time tracking** — logs latency and flags devices exceeding thresholds
- **Multi-device support** — monitors routers, switches, firewalls, and servers from a single config file
- **Alert notifications** — sends email alerts when devices go down or recover
- **Logging** — maintains a timestamped log of all status changes for incident investigation
- **CSV reporting** — generates daily availability reports for management review

## How It Works

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  devices.yaml   │────▶│   monitor.py │────▶│  status_log.csv │
│  (config)       │     │  (main loop) │     │  (history)      │
└─────────────────┘     └──────┬───────┘     └─────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
              ┌─────▼─────┐        ┌─────▼─────┐
              │   Alert   │        │  Report   │
              │  (email)  │        │  (daily)  │
              └───────────┘        └───────────┘
```

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/network-monitor.git
cd network-monitor
pip install -r requirements.txt
```

## Configuration

Edit `devices.yaml` to add your network devices:

```yaml
devices:
  - name: "Core Switch"
    ip: "192.168.1.1"
    type: "switch"
    threshold_ms: 50

  - name: "Edge Firewall"
    ip: "192.168.1.254"
    type: "firewall"
    threshold_ms: 30

  - name: "File Server"
    ip: "192.168.1.10"
    type: "server"
    threshold_ms: 20

alert:
  email: "admin@example.com"
  smtp_server: "smtp.example.com"
  smtp_port: 587

monitoring:
  interval_seconds: 60
  retry_count: 3
  log_file: "status_log.csv"
```

## Usage

```bash
# Start monitoring
python monitor.py

# Run a single check (no loop)
python monitor.py --once

# Generate availability report for the last 24 hours
python report.py --hours 24
```

## Sample Output

```
2026-05-02 09:15:01 | Core Switch (192.168.1.1)    | UP   | 2ms
2026-05-02 09:15:01 | Edge Firewall (192.168.1.254) | UP   | 5ms
2026-05-02 09:15:01 | File Server (192.168.1.10)   | DOWN | ---
2026-05-02 09:15:01 | ALERT: File Server is unreachable. Sending notification...
2026-05-02 09:16:02 | File Server (192.168.1.10)   | UP   | 8ms (recovered)
```

## Technologies Used

- **Python 3** — core scripting language
- **ICMP (ping)** — device availability checking
- **YAML** — human-readable configuration
- **SMTP** — email alerting
- **CSV** — logging and reporting

## Skills Demonstrated

- Network monitoring concepts (availability, latency, thresholds)
- Python scripting for IT automation
- Configuration management (YAML-based device inventory)
- Incident alerting and notification workflows
- Logging and reporting for operational visibility

## License

MIT License
