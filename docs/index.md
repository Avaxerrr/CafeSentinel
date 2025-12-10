# CafeSentinel - Technical Documentation

## Overview

CafeSentinel is a network monitoring and occupancy tracking application for internet cafes. It monitors network infrastructure (router, server, internet gateway), tracks client PC activity, captures screenshots, and sends notifications to Discord channels.

The application uses a dual-process self-healing architecture where two executables monitor each other and automatically restart on failure. All sensitive configuration and credential data is encrypted and stored in disguised file formats for security.

## Architecture

### Dual-Process System

```
CafeSentinel.exe (Main Application)
├─ PySide6 GUI (system tray + main window)
├─ Network monitoring worker thread
├─ Screenshot capture service
├─ Discord notification service
├─ Flask REST API server (port 5000)
└─ Monitors SentinelService.exe (5-second heartbeat)

SentinelService.exe (Watchdog)
├─ Monitors CafeSentinel.exe process
├─ Restarts main app on crash/termination
├─ Logs lifecycle events to info.log
└─ Runs with elevated privileges
```

### Mutual Monitoring
- Each process checks if the other is running every 5 seconds
- If either process terminates, the other restarts it within 2 seconds
- Only stoppable via password-protected shutdown from main app
- Uses process name detection via Windows tasklist command

### Security Layer
- Configuration stored encrypted as `cscf.dll` (not plaintext JSON)
- Passwords stored encrypted as `cron.dll` 
- Encryption uses machine-specific keys derived from hardware fingerprint
- Log files sanitized to prevent revealing internal file structure
- All sensitive files disguised with .dll extension to avoid casual inspection

## Project Structure

```
CafeSentinel/
├── controllers/
│   └── system_tray_app.py           # System tray controller, starts all services
├── models/
│   ├── app_logger.py                # Daily rotating log system with retention
│   ├── config_manager.py            # Encrypted config singleton manager
│   ├── discord_notifier.py          # Discord webhook client
│   ├── event_logger.py              # CSV incident logging
│   ├── network_tools.py             # ICMP ping implementation
│   ├── screen_capture.py            # Screenshot capture (mss library)
│   ├── security_manager.py          # Password vault with Fernet encryption
│   ├── sentinel_worker.py           # Main monitoring worker thread
│   └── session_manager.py           # PC occupancy tracking
├── utils/
│   └── resource_manager.py          # Path resolution for compiled/script mode
├── views/
│   ├── main_window.py               # GUI dashboard
│   ├── setup_wizard.py              # First-run password setup
│   ├── settings_dialog.py           # Local configuration editor
│   └── settings_pages/
│       ├── network_page.py          # Network settings tab
│       ├── monitoring_page.py       # Monitoring settings tab
│       ├── discord_page.py          # Discord settings tab
│       └── system_page.py           # System settings tab (log retention)
├── assets/icons/                    # Icon resources
├── api_server.py                    # Flask REST API server
├── interface.py                     # Main application entry point
├── watchdog_service.py              # Watchdog process entry point
├── startup_manager.py               # Windows startup registration
├── resources.qrc                    # Qt resource file
├── build.py                         # Nuitka build script
├── cscf.dll                         # Encrypted configuration (auto-generated)
├── cron.dll                         # Encrypted password vault (first-run)
├── info.log                         # Current day log file
├── probes/                          # Archived log files folder
└── config_backups/                  # Encrypted config backup folder
```

## Technical Stack

- **GUI Framework:** PySide6 (Qt for Python)
- **Network Monitoring:** Raw ICMP sockets (requires admin privileges)
- **Screenshot Capture:** mss library, output as WebP format
- **HTTP Server:** Flask with CORS support (REST API for remote management)
- **Encryption:** cryptography library (Fernet symmetric encryption)
- **Notifications:** Discord webhooks via requests library
- **Compilation:** Nuitka with optional LTO optimization
- **Platform:** Windows only (uses Windows-specific process management)

---

## Documentation Contents

- [**Monitoring System**](monitoring.md) - SentinelWorker, Network Monitoring, PC Tracking
- [**Configuration System**](configuration.md) - File Structure, Schema, API, Hot-Reload
- [**Security System**](security.md) - Encryption, Password Management, Admin Requirements
- [**Logging System**](logging.md) - Architecture, Rotation, Format, API Serving
- [**Features & UI**](features.md) - Screenshots, Discord Integration, Settings Dialog
- [**Deployment & Build**](deployment.md) - Compilation, Startup Registration, Dependencies
