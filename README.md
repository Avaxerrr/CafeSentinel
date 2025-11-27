<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![Status](https://img.shields.io/badge/status-stable-green)

# CafeSentinel

</div>

CafeSentinel is a professional-grade network monitoring and occupancy tracking system designed for Internet Cafes and LAN Centers. It is engineered as a **high-performance, self-healing application** compiled with Nuitka for stealth and stability.

Unlike basic scripts, CafeSentinel operates as a dual-process system (Watchdog + GUI) to ensure zero downtime, providing real-time visual auditing and automated reporting to Discord.

## Key Capabilities

### 1. Infrastructure Monitoring
*   **Tri-Point Status:** Continuously pings Router, Server, and Internet Gateway.
*   **Cascading Failure Logic:** Intelligently detects if an "Internet Outage" is actually just a "Router Failure," suppressing false alarms.
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
*   📶 **Router:** White (OK) / Red (Offline)
*   🖥️ **Server:** White (OK) / Red (Offline)
*   🌐 **Internet:** White (OK) / Red (Offline)
*   🔢 **Clients:** Dynamic badge showing active PC count.

---

## Architecture

CafeSentinel uses a **Dual-Executable Architecture** for resilience:

1.  **SentinelService.exe (The Watchdog):** A lightweight background process that checks if the main app is running. If the app crashes or is closed without a password, the Watchdog instantly restarts it.
2.  **CafeSentinel.exe (The Interface):** The main PySide6 GUI application that handles scanning and user interaction.

---

## Build System

This project is designed to be compiled, not run as a raw script. It includes a custom `build.py` system that utilizes **Nuitka** with Link Time Optimization (LTO) to produce optimized, standalone binaries.

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

**The Build Script will automatically:**
1.  Clean previous build artifacts.
2.  Compile `resources.qrc` into `resources_rc.py` (embedding icons).
3.  Compile the **Main App** and **Watchdog** into separate standalone folders.
4.  Generate `START_SENTINEL.vbs` (A stealth launcher script).
5.  Package everything into a `dist/CafeSentinel_Deploy` folder ready for deployment.

---

## Deployment

To install on a target machine:

1.  Copy the entire `CafeSentinel_Deploy` folder from your build output.
2.  Open the folder and run **`install_monitor.bat`** as Administrator.
    *   *This registers the Watchdog to run with highest privileges at user logon.*
3.  (Optional) To start immediately without logging out, run `START_SENTINEL.vbs`.

## Configuration

The application generates a `config.json` file on first run. You can edit this file to hot-reload settings instantly:

