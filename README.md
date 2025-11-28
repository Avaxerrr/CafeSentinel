<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![Status](https://img.shields.io/badge/status-stable-green)

<img width="696" height="677" alt="image" src="https://github.com/user-attachments/assets/236d6e67-d3c5-42be-a52f-a7ed97677903" />

# CafeSentinel

</div>

CafeSentinel is a professional-grade network monitoring and occupancy tracking system designed for Internet Cafes and LAN Centers. It is engineered as a **high-performance, self-healing application** compiled with Nuitka for stealth and stability.

Unlike basic scripts, CafeSentinel operates as a dual-process system with **mutual monitoring** to ensure zero downtime, providing real-time visual auditing and automated reporting to Discord.

## Key Capabilities

### 1. Infrastructure Monitoring
*   **Tri-Point Status:** Continuously pings Router, Server, and Internet Gateway with configurable intervals.
*   **Cascading Failure Logic:** Intelligently detects if an "Internet Outage" is actually just a "Router Failure," suppressing false alarms.
*   **Noise Filtering:** Hysteresis logic filters transient network jitter (configurable threshold, default 10s) to prevent false incident reports from momentary packet loss.
*   **Dual DNS Verification:** Automatically verifies internet connectivity against both primary (8.8.8.8) and secondary (1.1.1.1) DNS servers before declaring an outage.
*   **Visual Dashboard:** Displays real-time status on a dedicated GUI grid.

### 2. Visual Auditing & Evidence
*   **Remote Screenshots:** Captures the host screen at set intervals (e.g., every 60 mins) and uploads it to a private Discord channel.
*   **Incident Proof:** Automatically snaps a screenshot the moment an internet outage is resolved, providing visual timestamps for ISP disputes.
*   **Privacy Vault:** Admin-protected "Privacy Mode" to temporarily disable screen capture.

### 3. Occupancy & Analytics
*   **Live Counter:** A dynamic System Tray badge shows the exact count of active PCs (e.g., "15").
*   **Session Logic:** Tracks uptime/downtime of client PCs to generate usage reports.
*   **Smart Freeze:** If the router disconnects, the system "freezes" occupancy data to prevent false "Mass Log-off" events in your reports.

### 4. System Tray Integration
Four distinct tray icons provide immediate status at a glance:
*   Router: White (OK) / Red (Offline)
*   Server: White (OK) / Red (Offline)
*   Internet: White (OK) / Red (Offline)
*   Clients: Dynamic badge showing active PC count.

---

## Architecture

CafeSentinel uses a **Dual-Executable Mutual Monitoring Architecture** for maximum resilience:

1.  **SentinelService.exe (The Watchdog):** A lightweight background process that monitors the main application. If CafeSentinel crashes or is forcibly closed, the Watchdog restarts it within 2 seconds.

2.  **CafeSentinel.exe (The Interface):** The main PySide6 GUI application that handles scanning, reporting, and user interaction. It actively monitors the Watchdog service and automatically respawns it if terminated.

**Self-Healing:** Both processes monitor each other via 5-second heartbeat checks. If either process is killed (even via Task Manager), the surviving process will automatically revive it, creating an unbreakable monitoring loop that can only be stopped via password-protected shutdown.

**Deployment Structure:**
```
CafeSentinel/
├── CafeSentinel.exe (Main Application)
├── config.json
├── install_monitor.bat
└── SentinelService/ (Nested Watchdog)
    └── SentinelService.exe
```

---

## Build System

This project is designed to be compiled, not run as a raw script. It includes a custom `build.py` system that utilizes **Nuitka** with optional Link Time Optimization (LTO) to produce optimized, standalone binaries.

### Prerequisites
*   Python 3.10+
*   Pip requirements: `nuitka`, `zstandard`, `pyside6`, `ordered-set`

### How to Build
1.  Install dependencies:
    ```
    pip install -r requirements.txt
    ```
2.  Run the build script:
    ```
    python build.py
    ```
3.  Select build mode:
    *   **Option 1: Fast Build** - No LTO, console visible. Ideal for testing and debugging.
    *   **Option 2: Production Build** - Full LTO optimization, no console. For deployment.

**The Build Script will automatically:**
1.  Clean previous build artifacts.
2.  Compile `resources.qrc` into `resources_rc.py` (embedding icons).
3.  Compile the **Main App** and **Watchdog** into separate standalone folders.
4.  Organize deployment with nested folder structure.
5.  Package everything into a `dist/CafeSentinelDeploy` folder ready for deployment.

---

## Deployment

To install on a target machine:

1.  Copy the entire `CafeSentinelDeploy/CafeSentinel` folder from your build output to the target machine.
2.  Navigate into the `CafeSentinel` folder and run **`install_monitor.bat`** as Administrator.
    *   This registers the **SentinelService** (Watchdog) to run with highest privileges at user logon.
    *   The Watchdog will then automatically launch the main application.
3.  The system will start automatically on next login. To start immediately, run `SentinelService\SentinelService.exe` manually.

**Security:** The application requires administrator privileges for raw ICMP ping operations and is protected by a password-based exit mechanism to prevent unauthorized shutdown.

---

## Configuration

The application generates a `config.json` file on first run. You can edit this file to hot-reload settings instantly without restarting the application.

### Key Configuration Options:

**Verification Settings:**
```
"verification_settings": {
    "retry_delay_seconds": 1.0,
    "secondary_target": "1.1.1.1",
    "min_incident_duration_seconds": 10
}
```
*   `min_incident_duration_seconds`: Minimum outage duration before logging/alerting. Filters transient network jitter.

**Monitor Settings:**
```
"monitor_settings": {
    "interval_seconds": 2,
    "pc_subnet": "192.168.1",
    "pc_start_range": 110,
    "pc_count": 20
}
```

**Screenshot Settings:**
```
"screenshot_settings": {
    "enabled": true,
    "interval_minutes": 60,
    "quality": 80,
    "resize_ratio": 1.0
}
```

Refer to `config.json` for complete configuration options including Discord webhooks, target IPs, and occupancy tracking settings.

---

## Features

- Hot-reload configuration without restart
- Password-protected privacy mode and shutdown
- Automated Discord notifications with embedded screenshots
- CSV-based incident logging with timestamps
- Session-based occupancy tracking with hourly snapshots
- Cascading failure detection to prevent false alarms
- Dual DNS verification for internet connectivity
- Intelligent incident filtering with configurable thresholds

---

## License

MIT License. See LICENSE file for details.