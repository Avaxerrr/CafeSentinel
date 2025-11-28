## CafeSentinel - Technical Documentation

### Overview

CafeSentinel is a network monitoring and occupancy tracking application for internet cafes. It monitors network infrastructure (router, server, internet gateway), tracks client PC activity, captures screenshots, and sends notifications to Discord channels.

The application uses a dual-process self-healing architecture where two executables monitor each other and automatically restart on failure.

### Architecture

**Dual-Process System:**

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
└─ Runs with elevated privileges
```

**Mutual Monitoring:**
- Each process checks if the other is running every 5 seconds
- If either process terminates, the other restarts it within 2 seconds
- Only stoppable via password-protected shutdown from main app

### Project Structure

```
CafeSentinel/
├── controllers/
│   └── system_tray_app.py           # System tray controller, starts all services
├── models/
│   ├── app_logger.py                # Logging system
│   ├── config_manager.py            # Config file management
│   ├── discord_notifier.py          # Discord webhook client
│   ├── event_logger.py              # CSV incident logging
│   ├── network_tools.py             # ICMP ping implementation
│   ├── screen_capture.py            # Screenshot capture (mss library)
│   ├── security_manager.py          # Encrypted password storage
│   ├── sentinel_worker.py           # Main monitoring worker
│   └── session_manager.py           # PC occupancy tracking
├── utils/
│   └── resource_manager.py          # Path resolution for compiled/script mode
├── views/
│   ├── main_window.py               # GUI dashboard
│   └── setup_wizard.py              # First-run password setup
├── assets/icons/                    # Icon resources
├── api_server.py                    # Flask REST API server
├── interface.py                     # Main application entry point
├── watchdog_service.py              # Watchdog process entry point
├── startup_manager.py               # Windows startup registration
├── resources.qrc                    # Qt resource file
├── build.py                         # Nuitka build script
└── config.json                      # Configuration file (auto-generated)
```

### Technical Stack

- **GUI Framework:** PySide6 (Qt for Python)
- **Network Monitoring:** Raw ICMP sockets (requires admin privileges)
- **Screenshot Capture:** mss library, saved as WebP
- **HTTP Server:** Flask (REST API for remote config)
- **Notifications:** Discord webhooks via requests library
- **Compilation:** Nuitka with optional LTO
- **Platform:** Windows only

### Core Components

**SentinelWorker (models/sentinel_worker.py):**
- Runs in separate QThread
- Performs network scans every N seconds (configurable)
- Implements hot-reload by checking config file modification time
- Emits Qt signals to update GUI
- Manages screenshot scheduling
- Coordinates with SessionManager for occupancy tracking

**SystemTrayController (controllers/system_tray_app.py):**
- Creates 4 system tray icons (router, server, internet, clients)
- Starts SentinelWorker in background thread
- Starts Flask API server in daemon thread
- Monitors watchdog process health
- Handles password-protected exit

**SessionManager (models/session_manager.py):**
- Tracks PC online/offline state changes
- Applies stability checks before confirming state change
- Batches notifications to avoid spam
- Sends hourly occupancy snapshots
- Freezes state during network outages

**Flask API Server (api_server.py):**
- Provides REST API on port 5000
- Endpoints: GET/POST /api/config, GET /api/status, GET /api/config/backups
- Thread-safe file access with locks
- Automatic config backup before updates
- Runs in daemon thread (terminates with main app)

### Configuration System

**File:** `config.json` (auto-generated on first run)

**Structure:**
```json
{
  "targets": {
    "router": "IP address",
    "server": "IP address", 
    "internet": "IP address"
  },
  "monitor_settings": {
    "interval_seconds": 2,
    "pc_subnet": "192.168.1",
    "pc_start_range": 110,
    "pc_count": 20
  },
  "verification_settings": {
    "retry_delay_seconds": 1.0,
    "secondary_target": "1.1.1.1",
    "min_incident_duration_seconds": 10
  },
  "screenshot_settings": {
    "enabled": true,
    "interval_minutes": 60,
    "quality": 80,
    "resize_ratio": 1.0
  },
  "occupancy_settings": {
    "enabled": true,
    "mode": "session",
    "min_session_minutes": 3,
    "batch_delay_seconds": 30,
    "hourly_snapshot_enabled": true
  },
  "discord_settings": {
    "enabled": false,
    "shop_name": "Shop Name",
    "webhook_alerts": "URL",
    "webhook_occupancy": "URL", 
    "webhook_screenshots": "URL"
  }
}
```

**Hot-Reload Implementation:**
- SentinelWorker checks config file mtime every monitor cycle
- If modification detected, reloads config and applies changes
- No application restart required
- Changes take effect within next monitor cycle (typically 2 seconds)

### Security System

**Password Storage (models/security_manager.py):**
- Two passwords: admin (for exit) and privacy (for screenshot toggle)
- Stored encrypted in `.dll` file (disguised vault)
- Uses machine-specific encryption key derived from hardware
- Fernet symmetric encryption
- Vault created on first run via setup wizard

**Admin Requirements:**
- Application must run with administrator privileges
- Required for raw ICMP socket operations
- Self-elevates on startup if not running as admin

### Network Monitoring

**Ping Implementation:**
- Uses raw ICMP sockets via network_tools.py
- Scans three targets: router, server, internet gateway
- Verification logic checks secondary DNS (1.1.1.1) before declaring internet outage
- Hysteresis filtering: requires minimum incident duration before logging
- Cascading failure detection: distinguishes router failure from internet outage

**PC Occupancy Tracking:**
- Generates IP range based on subnet/start/count settings
- Pings all PCs in range each cycle
- Tracks online/offline transitions via SessionManager
- Applies stability period before confirming state change

### Screenshot System

**Capture Process:**
- Captures primary monitor using mss library
- Converts to PIL Image, resizes based on ratio setting
- Saves as WebP format (better compression than JPEG)
- Stored in memory buffer, not disk
- Sent directly to Discord webhook as file attachment

**Triggers:**
- Scheduled: every N minutes (configurable)
- Incident: automatically captured when outage resolves
- Privacy mode: can be toggled via password to disable capture

### Discord Integration

**Webhook Types:**
- Alerts: network outages and restorations
- Occupancy: session starts/ends and hourly snapshots
- Screenshots: routine captures and incident evidence

**Notification Format:**
- Rich embeds with color coding
- Timestamps and duration information
- Screenshots attached as WebP files
- Shop name included in footer

### Build System

**Compilation (build.py):**
- Uses Nuitka to compile Python to native executable
- Two build modes: Fast (no LTO, console visible) and Production (LTO, no console)
- Compiles resources.qrc to resources_rc.py
- Builds two separate executables: CafeSentinel.exe and SentinelService.exe
- Creates nested folder structure for deployment
- Output: dist/CafeSentinelDeploy/CafeSentinel/

**Deployment Structure:**
```
CafeSentinel/
├── CafeSentinel.exe
├── config.json
├── install_monitor.bat
└── SentinelService/
    └── SentinelService.exe
```

### Startup Registration

**install_monitor.bat:**
- Registers SentinelService.exe in Windows Task Scheduler
- Configured to run at user logon with highest privileges
- Watchdog then automatically launches main application

**Alternative startup methods:**
- Registry Run key (optional)
- Manual execution of SentinelService.exe

### API Server

**Flask REST API (api_server.py):**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/status` | GET | Health check, returns service status |
| `/api/config` | GET | Returns current config.json contents |
| `/api/config` | POST | Updates config.json, creates backup |
| `/api/config/backups` | GET | Lists available backup files |

**Backup System:**
- Automatic backup before each config update
- Timestamped filenames: config_backup_YYYYMMDD_HHMMSS.json
- Stored in config_backups/ directory
- Keeps last 10 backups, deletes older ones

**Thread Safety:**
- Uses threading.Lock for config file access
- Prevents race conditions during concurrent reads/writes

### Dependencies

**Python Packages (requirements.txt):**
- PySide6: GUI framework
- mss: screenshot capture
- Pillow: image processing
- requests: HTTP client for Discord webhooks
- Flask: REST API server
- flask-cors: CORS support for API

**Build Dependencies:**
- Nuitka: Python to executable compiler
- zstandard: compression for Nuitka
- ordered-set: Nuitka dependency

**System Requirements:**
- Windows operating system
- Administrator privileges
- Python 3.10 or higher (for development)

### File Paths and Resource Management

**ResourceManager (utils/resource_manager.py):**
- Handles path resolution for both script and compiled modes
- Detects if running from Nuitka executable
- Returns correct base directory for resource access
- Used by config_manager and other modules for file operations

### Logging

**AppLogger (models/app_logger.py):**
- Centralized logging system
- Logs to console during development
- Can be extended for file logging
- Used throughout application for debugging and monitoring

### Known Behaviors

- Config file must exist or will be created with defaults
- Screenshot capture requires at least one monitor connected
- Network monitoring requires raw socket permissions (admin rights)
- Watchdog process remains running even if main app exits normally
- Hot-reload preserves runtime state (doesn't restart worker thread)
- API server binds to 0.0.0.0:5000 (accessible from network)

### Configuration Field Name Requirements

**Critical for SessionManager:**
- Must use `min_session_minutes` (not session_stability_seconds)
- Must use `batch_delay_seconds`
- Must use `hourly_snapshot_enabled` (not hourly_snapshot)

Incorrect field names will cause SessionManager to use hardcoded defaults.