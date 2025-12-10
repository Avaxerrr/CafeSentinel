Alright, here's the **COMPLETE UPDATED DOCUMENTATION** with all the new features properly integrated:

***

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

## Core Components

### SentinelWorker (models/sentinel_worker.py)

Main monitoring thread that performs continuous network surveillance.

**Responsibilities:**
- Runs in separate QThread to avoid blocking GUI
- Performs network scans every N seconds (configurable, default 2 seconds)
- Manages screenshot scheduling based on interval settings
- Coordinates with SessionManager for PC occupancy tracking
- Emits Qt signals to update system tray icons and GUI
- Implements hot-reload configuration updates without restart

**Hot-Reload Mechanism:**
- Worker polls ConfigManager's dirty flag each monitoring cycle
- When flag is set (config updated via API or local settings), worker reloads configuration
- Updates internal state variables and reinitializes submodules
- Changes take effect within 2 seconds without application restart
- Uses thread-safe polling to avoid cross-thread signal issues

**Monitoring Loop:**
1. Check config dirty flag and reload if needed
2. Scan network targets (router, server, internet)
3. Scan PC range for occupancy tracking
4. Process state changes and trigger notifications
5. Handle routine screenshot capture if interval elapsed
6. Sleep for configured interval and repeat

#### Startup Configuration Snapshot

On monitoring start, the worker logs a concise snapshot of its active configuration, including the monitoring interval in seconds and the number of PC targets in the current scan range. This `[SYSTEM]` log entry appears once per process start and helps correlate historical logs with the exact runtime settings that were in effect at the time (for example, changes to scan interval or PC count).

**Example Log:**
```
[2025-12-09 19:27:28] [SYSTEM] Settings Loaded: Interval=2s, Targets=100 PCs
```

### SentinelService.exe (Watchdog)

Monitors the main CafeSentinel application and ensures continuous operation.

**Core Responsibilities:**
- Detects when CafeSentinel.exe terminates
- Automatically restarts the main application on unexpected termination
- Runs with elevated admin privileges
- Operates independently of the main application

#### Process Lifecycle Logging

The watchdog now writes lightweight lifecycle events directly to the main `info.log` file using a raw append strategy instead of the primary logging class. Each time the main application is started, stopped, or restarted, a `[WATCHDOG]` log line is emitted with a timestamp and description of the event.

Exit codes are interpreted to distinguish user‑initiated shutdowns from abnormal terminations. A clean exit (`code 0`) and setup cancellation (`code 100`) are logged as intentional stops, and the watchdog terminates itself without relaunching the main app. Any other non‑zero exit code is treated as an unexpected termination, logged with the code value, and triggers an automatic restart after a short delay.

**Exit Code Behavior:**
- **Code 0 (Clean Exit):** User closed the app intentionally with admin password → Watchdog stops, no restart
- **Code 100 (Setup Cancelled):** User cancelled first-run setup → Watchdog stops, no restart
- **Other Codes:** Application crashed or was forcibly terminated → Watchdog logs the exit code and restarts the app after 2 seconds

**Example Logs:**
```
[2025-12-09 19:00:01] [WATCHDOG] Starting CafeSentinel process (spawn mode).
[2025-12-09 19:00:03] [WATCHDOG] CafeSentinel exited cleanly (Code 0). Stopping watchdog.
[2025-12-09 19:15:22] [WATCHDOG] CafeSentinel terminated unexpectedly (Exit Code -1073741819). Restarting...
```

### SystemTrayController (controllers/system_tray_app.py)

Application controller that initializes and coordinates all services.

**Responsibilities:**
- Creates 4 system tray icons: router, server, internet, active clients
- Starts SentinelWorker in background QThread
- Starts Flask API server in daemon thread (port 5000)
- Monitors watchdog process health via 5-second timer
- Handles password-protected exit via SecurityManager
- Manages system tray context menu including settings dialog access
- Initializes logging system and executes retention cleanup on startup

**Stealth Mode (Headless Operation):**
- **Implementation:** Configurable via `env_state` boolean in `system_settings`.
- **Behavior:**
  - **Enabled (`True`):** Application runs normally but hides all system tray icons.
  - **Disabled (`False`):** Standard system tray icons are visible.
- **Persistence:** App is configured with `setQuitOnLastWindowClosed(False)` to ensure the process continues running even without visible UI elements.
- **Toggle Mechanism:** Can be toggled remotely via API (Manager App) or locally via Settings Dialog (if accessible). Updates apply immediately via hot-reload.

**System Tray Icons:**
- Router: green (online) / red (offline)
- Server: green (online) / red (offline)  
- Internet: green (online) / red (offline)
- Clients: displays active PC count with dynamic icon generation

### ConfigManager (models/config_manager.py)

Singleton class that manages all configuration access with encryption and thread-safety.

**Architecture:**
- Singleton pattern ensures single config instance across application
- Thread-safe operations using threading.Lock
- Emits Qt signal when config changes for same-thread listeners
- Uses dirty flag for cross-thread polling (worker thread compatibility)

**File Handling:**
- Primary config: `cscf.dll` (encrypted with Fernet)
- Legacy support: migrates old `config.json` to encrypted format on first detection
- Backup system: creates timestamped encrypted backups before updates
- Keeps last 10 backups, auto-deletes older files

**Encryption:**
- Uses machine-specific key generated from hardware fingerprint
- Fernet symmetric encryption (AES-128 in CBC mode with timestamp)
- Config stored as encrypted JSON string
- Decryption happens in-memory only, never written as plaintext

**Hot-Reload Support:**
- Exposes `check_and_clear_dirty()` method for worker thread polling
- Emits `sig_config_changed` signal for same-thread GUI updates
- Updates take effect immediately without file system monitoring

### SessionManager (models/session_manager.py)

Tracks PC occupancy state changes and manages Discord notifications.

**State Tracking:**
- Maintains online/offline status for each PC in monitored range
- Applies stability period before confirming state changes (prevents flicker)
- Freezes state during network outages to avoid false notifications
- Tracks session start time for minimum duration enforcement

**Notification Logic:**
- Batches multiple state changes to avoid notification spam
- Sends individual notifications for session start/end events
- Generates hourly occupancy snapshots if enabled
- Includes session duration in end notifications

**Configuration:**
- Minimum session duration filter (ignore very short sessions)
- Batch delay between grouped notifications
- Hourly snapshot enable/disable toggle
- Mode setting (currently only 'session' mode implemented)

### Flask API Server (api_server.py)

REST API server for remote configuration management and log access.

**Server Configuration:**
- Runs in daemon thread (terminates with main application)
- Binds to 0.0.0.0:5000 (accessible from network)
- CORS enabled for cross-origin requests
- Thread-safe config access via ConfigManager singleton

**Endpoint Reference:**

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/api/status` | GET | Health check | Service status and timestamp |
| `/api/config` | GET | Retrieve configuration | Complete config object |
| `/api/config` | POST | Update configuration | Success/error with validation message |
| `/api/config/backups` | GET | List backup files | Array of backup filenames |
| `/api/logs` | GET | Today's logs (smart RAM/Disk) | Array of log strings (max 5000 lines, query: ?lines=N) |
| `/api/logs/archive` | GET | List archived logs | Array of archived log filenames |
| `/api/logs/archive/<filename>` | GET | Retrieve specific archive | Complete archived log content |
| `/api/logs/archive/<filename>` | DELETE | Permanently delete archive | Success/error confirmation |

**Request/Response Flow:**
- All responses use JSON format
- Config updates validated before applying (required keys, value ranges)
- Automatic backup created before each config modification
- Errors return appropriate HTTP status codes (400, 403, 404, 500)

**Security Considerations:**
- No authentication currently implemented (relies on network isolation)
- Path traversal protection in archive access endpoints
- Filename validation to prevent arbitrary file access
- Permanent deletion bypasses Windows recycle bin

## Configuration System

### File Structure

Configuration stored as encrypted file `cscf.dll` in application directory.

**Encryption Details:**
- Format: Fernet encrypted JSON string
- Key: Derived from machine-specific hardware fingerprint via SecurityManager
- Migration: Automatically converts legacy `config.json` to encrypted format
- Backup: Encrypted backups stored in `config_backups/` subdirectory

### Configuration Schema

```json
{
  "targets": {
    "router": "192.168.1.1",
    "server": "192.168.1.200",
    "internet": "8.8.8.8"
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
    "shop_name": "My Internet Cafe",
    "webhook_alerts": "",
    "webhook_occupancy": "",
    "webhook_screenshots": ""
  },
  "system_settings": {
    "env_state": false,
    "log_retention_days": 30
  }
}
```

### Configuration Access Methods

**Remote Configuration (via API):**
- CafeSentinel-Manager application connects to Flask API
- Sends POST request to `/api/config` with complete config object
- ConfigManager validates, backs up, encrypts, and saves
- Hot-reload mechanism detects change and applies within 2 seconds

**Local Configuration (via Settings Dialog):**
- Accessible from system tray context menu
- Requires admin password for access
- Four-tab interface: Network, Monitoring, Discord, System
- Saves via same ConfigManager.update_config() method as API
- Changes apply immediately via hot-reload

### Validation Rules

- Screenshot interval: 1-1440 minutes
- Screenshot quality: 1-100
- Monitor interval: 1-60 seconds
- Log retention: 1-365 days
- All required sections must be present
- Invalid configurations rejected with error message

### Backup System

- Automatic backup before each configuration update
- Filename format: `backup_YYYYMMDD_HHMMSS.cscf.dll`
- Stored in `config_backups/` subdirectory
- Backups are encrypted with same method as main config
- Automatic cleanup: keeps last 10 backups, deletes older

### Hot-Reload Implementation

Configuration changes apply without application restart through two mechanisms:

**Mechanism 1: Qt Signals (Same-Thread)**
- ConfigManager emits `sig_config_changed` signal when config updates
- GUI components connected to this signal update immediately
- Used for components running in main Qt thread (e.g., SystemTrayController for Stealth Mode updates)

**Mechanism 2: Dirty Flag Polling (Cross-Thread)**
- Worker thread polls ConfigManager.check_and_clear_dirty() each cycle
- When flag is True, worker fetches fresh config and reinitializes
- Thread-safe operation using internal lock
- Used because Qt signals don't work reliably across threads

**Update Propagation:**
1. Config update arrives (API or local settings)
2. ConfigManager validates and saves encrypted config
3. Sets internal dirty flag to True
4. Emits Qt signal to same-thread listeners
5. Worker thread detects dirty flag on next cycle
6. Worker reloads config and updates submodules
7. Changes take effect within 2 seconds

## Security System

### Encryption Architecture

All sensitive data encrypted using Fernet symmetric encryption from cryptography library.

**Machine-Specific Key Generation:**
- SecurityManager generates key from hardware fingerprint
- Uses motherboard serial number and processor ID (Windows WMI)
- SHA-256 hash converted to base64 for Fernet compatibility
- Key never stored on disk, regenerated on each application start
- Config encrypted on one machine cannot be decrypted on another

**File Disguising Strategy:**
- Configuration: `cscf.dll` (not `config.json`)
- Password vault: `cron.dll` (not `passwords.json`)
- Backups: `backup_TIMESTAMP.cscf.dll` 
- Appears as system library files to casual inspection
- Prevents easy identification of sensitive data

### Password Management

**SecurityManager (models/security_manager.py):**

Manages two password types stored in encrypted vault file `cron.dll`.

**Password Types:**
- Admin Password: Required for application exit and settings access
- Privacy Password: Required to toggle screenshot capture mode

**Vault Structure:**
- Single encrypted file containing both passwords
- Fernet encryption with machine-specific key
- Created during first-run setup wizard
- Passwords stored as bcrypt hashes (not plaintext)

**First-Run Setup:**
- Application detects missing `cron.dll` vault file
- Displays setup wizard requiring both passwords
- Validates password strength (minimum length, confirmation match)
- Creates encrypted vault with hashed passwords
- Application cannot start without completing setup

**Password Verification Flow:**
1. User enters password in dialog
2. SecurityManager loads and decrypts vault
3. Compares input against stored bcrypt hash
4. Returns boolean verification result
5. Application grants or denies access

### Log Sanitization

All log messages sanitized to prevent information disclosure.

**Sanitization Rules:**
- Never log file paths or filenames
- Use generic category labels: SYSTEM, CONFIG, NETWORK, etc.
- Error messages omit exception details that reveal structure
- Success messages confirm action without specifics
- Example: "[CONFIG] Updated successfully" not "[CONFIG] Saved to cscf.dll"

**Purpose:**
- Prevents attackers from identifying critical files
- Obscures application architecture from log analysis
- Reduces attack surface by limiting exposed information

### Admin Requirements

- Application requires administrator privileges to run
- Required for raw ICMP socket creation (network monitoring)
- Self-elevates on startup if not running as admin
- Watchdog service also runs with elevated privileges
- API server inherits admin privileges from main process

## Logging System

### Architecture

Professional 4-phase logging system with rotation, retention, and structured categorization.

**Active Log:**
- File: `info.log` (current day only)
- Updated continuously during application runtime
- Contains only today's activity
- Automatically rotated at midnight or when size exceeds 5MB
- Served via API for real-time monitoring

**Archive:**
- Directory: `probes/` subdirectory
- Contains historical logs from previous days
- Files automatically deleted based on retention policy
- Organized by date: `info-YYYY-MM-DD.log`
- Manual deletion also available via API

**Memory Buffer:**
- In-memory circular buffer of last 500 log lines
- Used for fast API serving without disk I/O
- Populated as logs are written
- Provides real-time log access to Manager application

### Log Rotation

**Daily Rotation:**
- Occurs at midnight when date changes
- On application startup if date changed while offline
- Current `info.log` renamed to `probes/info-YYYY-MM-DD.log`
- Fresh `info.log` created for new day
- No data loss during rotation process

**Size-Based Rotation:**
- Triggered when `info.log` exceeds 5MB
- File moved to `probes/info-YYYY-MM-DD-HHMMSS.log`
- Fresh `info.log` created immediately
- Part number appended if multiple rotations same day
- Prevents runaway log growth from error loops

**Rotation Process:**
1. AppLogger detects rotation condition (date change or size limit)
2. Current `info.log` renamed with timestamp
3. Moved to `probes/` archive directory
4. New empty `info.log` created
5. Logging continues without interruption
6. Rotation event logged in new file

### Log Retention & Cleanup

**Automatic Cleanup:**
- Configurable retention period via `log_retention_days` setting (default: 30 days)
- Cleanup executes automatically on application startup
- Files in `probes/` folder older than retention period permanently deleted
- Deletion bypasses Windows recycle bin (immediate destruction)
- Cleanup event logged with count of deleted files

**Retention Configuration:**
- Located in `system_settings.log_retention_days`
- Range: 1-365 days recommended
- Default: 30 days
- Configurable via Settings Dialog (System tab) or API
- Changes take effect on next application restart

**Cleanup Process:**
1. Application starts, reads `log_retention_days` from config
2. AppLogger.initialize() called by SystemTrayController
3. AppLogger.cleanup_old_logs() executes
4. Scans `probes/` directory for .log files
5. Checks file modification timestamp against cutoff date
6. Deletes files older than retention period
7. Logs cleanup summary to current day log

**Example Cleanup Log:**
```
[2025-12-09 17:00:00] [LOGGER] Cleaned up 15 old log files (Retention: 30 days)
```

### Log Format

Each log line follows structured categorized format:

```
[YYYY-MM-DD HH:MM:SS] [CATEGORY] Message text
```

**Components:**
- **Timestamp:** Full date and time in 24-hour format, local timezone
- **Category:** Structured tag for filtering and color-coding
- **Message:** Sanitized text without sensitive file paths or internal structure details

**Standard Categories:**

| Category | Usage |
|----------|-------|
| `SYSTEM` | Application startup, shutdown, initialization, API server events, configuration snapshots |
| `CONFIG` | Configuration loading, saving, validation, hot-reload events |
| `NETWORK` | Network scanning, connectivity checks, target validation, jitter detection |
| `ALERT` | Network outages, failures, incidents started |
| `RECOVERY` | Network restoration, incident resolution |
| `DISCORD` | Discord webhook notifications, delivery status |
| `DAEMON` | Monitoring loop lifecycle events |
| `TASK` | Scheduled tasks (screenshots, snapshots) |
| `SETTINGS` | Settings dialog operations, local configuration changes |
| `STEALTH` | Stealth mode toggle events |
| `LOGGER` | Log rotation, retention cleanup, archive operations |
| `WATCHDOG` | Watchdog process lifecycle events, exit code interpretation, restart operations |
| `ERROR` | Exceptions, failures, error conditions |
| `ARCHIVE` | Archive file operations (API deletion, retrieval) |

**Example Log Lines:**
```
[2025-12-09 05:23:15] [SYSTEM] Kernel thread attached (Singleton Mode)
[2025-12-09 05:23:15] [SYSTEM] Settings Loaded: Interval=2s, Targets=100 PCs
[2025-12-09 05:23:16] [CONFIG] Updated successfully
[2025-12-09 05:23:45] [ALERT] Router DOWN | Timer Started
[2025-12-09 05:23:50] [NETWORK] Router jitter detected (4.2s) - Below threshold (10s).
[2025-12-09 05:24:12] [RECOVERY] Router Restored | Duration: 0:00:27
[2025-12-09 05:25:00] [TASK] Capturing Routine Screenshot (60m)
[2025-12-09 05:25:01] [ERROR] Screenshot Capture Failed: No image data returned (Monitor off?)
[2025-12-09 06:00:00] [LOGGER] Cleaned up 5 old log files (Retention: 30 days)
[2025-12-09 08:30:15] [STEALTH] Entering Stealth Mode. Tray icons hidden.
[2025-12-09 19:00:01] [WATCHDOG] Starting CafeSentinel process (spawn mode).
[2025-12-09 19:00:03] [WATCHDOG] CafeSentinel exited cleanly (Code 0). Stopping watchdog.
```

### Smart API Log Serving

**Intelligent Serving Strategy:**
- API endpoint `/api/logs` uses smart switching based on request size
- Requests ≤500 lines: Served from memory buffer (fast, no disk I/O)
- Requests >500 lines: Read from disk `info.log` (complete history)
- Provides optimal balance between speed and visibility

**Memory Buffer Serving (Fast Path):**
- Query: `GET /api/logs?lines=200`
- Source: In-memory circular buffer (last 500 lines)
- Response time: <10ms
- Use case: Real-time monitoring, live log tail

**Disk Serving (Deep History):**
- Query: `GET /api/logs?lines=2000`
- Source: Current day `info.log` file on disk
- Response time: 50-200ms depending on file size
- Use case: Complete daily history, incident investigation

**Query Parameters:**
- `?lines=N`: Request N lines (default: 500, min: 10, max: 5000)
- Clamped to safe range to prevent excessive memory usage
- Returns actual line count in response (may be less than requested)

**Response Format:**
```json
{
  "status": "success",
  "lines": 2000,
  "source": "disk",
  "logs": ["[2025-12-09 00:00:15] [SYSTEM] ...", "..."]
}
```

**Fallback Behavior:**
- If disk read fails, automatically falls back to memory buffer
- Errors logged but service continues
- Manager application always receives some data

### API Access

**Real-Time Logs (GET /api/logs):**
- Returns today's log lines with smart RAM/Disk switching
- Query parameter: `?lines=500` (default 500, max 5000)
- Fast response for small requests (<500 lines)
- Complete history for large requests (>500 lines)
- Used by Manager for live monitoring and history review

**Archive List (GET /api/logs/archive):**
- Returns array of archived log filenames
- Sorted newest first
- Filenames only (content not included)
- Used by Manager for archive browser

**Archive Retrieval (GET /api/logs/archive/<filename>):**
- Returns complete content of specific archived log
- Filename from archive list
- Path traversal protection enforced
- Used by Manager to view historical logs

**Archive Deletion (DELETE /api/logs/archive/<filename>):**
- Permanently deletes archived log file
- No recycle bin, immediate destruction
- Requires exact filename from archive list
- Returns error if file in use or not found
- Security: Only allows deletion of files matching `info-*.log` pattern

## Network Monitoring

### Ping Implementation

Uses raw ICMP sockets implemented in `network_tools.py`.

**Technical Details:**
- Creates raw ICMP Echo Request packets
- Requires administrator privileges (raw socket access)
- Concurrent scanning using multithreading
- Default timeout: 1 second per host
- Returns list of responsive IP addresses

**Scan Targets:**
- Router: Local network gateway
- Server: Internet cafe server or critical infrastructure
- Internet: Public DNS (default 8.8.8.8)
- PC Range: All client computers in configured subnet

### Verification Logic

Multi-stage verification prevents false positive alerts.

**Internet Verification:**
1. Primary target fails (e.g., 8.8.8.8)
2. Wait configured retry delay (default 1 second)
3. Test secondary target (default 1.1.1.1)
4. If both fail, declare internet outage
5. If either succeeds, no alert generated

**Incident Duration Filter:**
- Initial failure starts incident timer
- Continuous monitoring during incident
- Alert generated only if outage exceeds minimum duration
- Default minimum: 10 seconds
- Prevents alerts for momentary network glitches

**Cascading Failure Detection:**
- If router fails, expect server and internet to also fail
- If only internet fails, router/server failures ignored
- Distinguishes local network issues from ISP problems
- Reduces notification spam during major outages

#### Jitter Visibility Below Incident Threshold

Short‑lived connectivity drops that recover before the configured `min_incident_duration_seconds` are now explicitly logged as jitter events instead of being silently ignored. When a component such as the router, server, or ISP target goes down and then recovers within this threshold, the system records a `[NETWORK]` log entry indicating the affected component and the exact outage duration, while still suppressing full incident creation and Discord alerts. This provides visibility into unstable links without generating alert noise.

**Example Jitter Logs:**
```
[2025-12-09 14:22:10] [ALERT] ISP DOWN | Timer Started
[2025-12-09 14:22:14] [NETWORK] ISP jitter detected (3.8s) - Below threshold (10s).
[2025-12-09 15:45:30] [ALERT] Router DOWN | Timer Started
[2025-12-09 15:45:36] [NETWORK] Router jitter detected (5.2s) - Below threshold (10s).
```

**Benefits:**
- Reveals intermittent network instability that doesn't trigger full outages
- Helps identify degraded ISP service quality
- Provides data for troubleshooting connectivity issues
- Logs can be used as evidence when reporting issues to ISPs

### PC Occupancy Tracking

Monitors range of client PCs for online/offline state.

**IP Range Generation:**
- Base subnet: `pc_subnet` setting (e.g., "192.168.1")
- Start IP: `pc_start_range` setting (e.g., 110)
- Count: `pc_count` setting (e.g., 20)
- Generates: 192.168.1.110 through 192.168.1.129

**State Change Detection:**
1. Ping all IPs in range each monitoring cycle
2. Compare results to previous cycle state
3. Detect transitions: offline→online (session start), online→offline (session end)
4. Pass changes to SessionManager for processing

**SessionManager Processing:**
- Applies stability period to confirm state change
- Filters out sessions shorter than minimum duration
- Batches multiple changes to avoid notification spam
- Freezes state during network outages
- Triggers Discord notifications for confirmed changes

## Screenshot System

### Capture Process

Captures primary monitor using mss library with post-processing.

**Capture Pipeline:**
1. Identify primary monitor via mss.mss()
2. Capture raw pixels to memory
3. Convert to PIL Image object
4. Resize according to `resize_ratio` setting (1.0 = original, 0.5 = half size)
5. Compress to WebP format with configured quality (1-100)
6. Store in memory buffer (not saved to disk)
7. Send directly to Discord webhook as file attachment

**WebP Format Benefits:**
- Better compression than JPEG at equivalent quality
- Smaller file sizes reduce upload time and Discord storage
- Maintains transparency support (though not used currently)

#### Asynchronous Uploads

Routine and incident screenshots are now uploaded asynchronously using background threads so that the main monitoring loop never blocks on HTTP network operations. The worker captures the image in the main thread (fast, <100ms), then hands the in‑memory WebP bytes to a dedicated upload thread that sends the data to Discord webhooks (slow, 2-5 seconds). If capture fails and no image data is produced, an error log entry is written instead of silently skipping the upload.

**Benefits:**
- Prevents monitoring delays during Discord uploads
- Eliminates "Slow Scan Loop" warnings caused by screenshot uploads
- Maintains consistent 2-second monitoring interval even during network congestion
- Failed captures are now logged for troubleshooting (e.g., monitor turned off)

**Example Logs:**
```
[2025-12-09 19:28:28] [TASK] Capturing Routine Screenshot (1m)
[2025-12-09 19:29:29] [TASK] Capturing Routine Screenshot (1m)
[2025-12-09 19:30:15] [ERROR] Screenshot Capture Failed: No image data returned (Monitor off?)
[2025-12-09 19:35:00] [ERROR] Incident Screenshot Failed: No image data returned
```

### Capture Triggers

**Routine Scheduled Capture:**
- Interval set via `screenshot_settings.interval_minutes`
- Timer tracks time since last capture
- Triggers when interval elapsed
- Continues until disabled or privacy mode enabled

**Incident Documentation:**
- Automatically captured when network outage resolves
- Provides visual evidence of recovery time
- Includes network status in Discord embed
- Helps diagnose issues visible on client screens

**Privacy Mode:**
- Toggle via privacy password from system tray
- Disables all screenshot capture when active
- Routine and incident captures both blocked
- Visual indicator in system tray when enabled

### Settings

- **Enabled:** Master toggle for screenshot system
- **Interval:** Minutes between routine captures (1-1440)
- **Quality:** WebP compression quality (1-100, higher = better quality/larger file)
- **Resize Ratio:** Scale factor (1.0 = full size, 0.5 = half dimensions, 0.25 = quarter)

### Discord Upload

Screenshots sent to Discord via webhook with rich embed.

**Upload Process:**
1. Image data in memory buffer
2. Background thread performs HTTP POST to webhook URL with multipart/form-data
3. Embed includes: timestamp, shop name, trigger type
4. File attachment: `screenshot.webp`
5. Color coding: blue (routine), green (incident recovery)

## Discord Integration

### Webhook Configuration

Three separate webhook URLs for different notification types.

**Webhook Types:**
- **Alerts:** Network outages and restorations
- **Occupancy:** PC session starts/ends, hourly snapshots
- **Screenshots:** Routine and incident captures

**Configuration:**
- URLs stored encrypted in `cscf.dll`
- Each webhook can point to different channel or same channel
- Webhooks optional (system works without Discord notifications)
- Invalid/missing webhooks logged but do not crash application

### Notification Format

All Discord messages use rich embeds with structured data.

**Embed Components:**
- **Title:** Event description (e.g., "Router Outage Resolved")
- **Description:** Detailed information and timestamps
- **Color:** Visual coding (red = outage, green = recovery, blue = routine)
- **Footer:** Shop name and system identifier
- **Timestamp:** ISO 8601 format for accurate timing
- **Fields:** Structured key-value pairs for duration, affected systems, etc.

**Alert Examples:**

Router Outage:
```
Title: Router Connection Lost
Color: Red
Description: Connectivity to router lost at [timestamp]
Fields: Duration (when resolved), Verification attempts
```

PC Session Start:
```
Title: Client PC Online
Color: Green  
Description: PC [IP] came online
Fields: Timestamp, Total active PCs
```

Hourly Snapshot:
```
Title: Occupancy Report
Color: Blue
Description: Current occupancy status
Fields: Active PCs, Percentage occupied, Peak today
```

### Notification Batching

SessionManager batches occupancy notifications to avoid spam.

**Batching Rules:**
- Multiple state changes within batch delay window grouped together
- Single notification sent after delay expires
- Includes count of affected PCs
- Reduces notification volume during busy periods (e.g., opening/closing time)

**Configuration:**
- `batch_delay_seconds`: Time window for batching (default 30)
- Balance between responsiveness and notification volume
- Set to 1 for immediate individual notifications
- Set to 300 (5 minutes) for heavily batched reports

## Local Settings Dialog

### Overview

Password-protected GUI for on-site configuration without Manager application.

**Access Method:**
- Right-click any system tray icon
- Select "Settings" from context menu
- Enter admin password
- Settings dialog opens

**Purpose:**
- Emergency configuration changes when Manager unavailable
- On-site adjustments by authorized personnel
- No remote network connection required
- Uses same ConfigManager as API (changes synchronized)

### Interface Structure

Four-tab layout covering all configuration sections.

**Network Tab:**
- Network Targets: Router IP, Server IP, Internet test IP
- Verification Settings: Retry delay, Secondary DNS, Min incident duration

**Monitoring Tab:**
- Scan Settings: Check interval, PC subnet, PC start range, PC count
- Screenshots: Enable toggle, Interval, Quality, Resize ratio
- Occupancy: Enable toggle, Hourly snapshots, Min session duration, Batch delay

**Discord Tab:**
- Enable toggle for notifications
- Shop name for embed footers
- Three webhook URLs: Alerts, Occupancy, Screenshots

**System Tab:**
- Stealth Mode: Enable/disable system tray icons
- Log Retention: Days to keep archived logs (1-365)

### Save Process

1. User modifies settings in form fields
2. Clicks "Save Changes" button
3. Form data collected into config dictionary
4. ConfigManager validates configuration
5. If valid: Encrypt, save to `cscf.dll`, trigger hot-reload
6. If invalid: Display error message, prevent save
7. Success dialog confirms changes applied
8. Changes take effect within 2 seconds

### Security

- Admin password required for access
- Password verified via SecurityManager before opening dialog
- Incorrect password displays "Access Denied" message
- Dialog remains open until user closes (no timeout)
- Changes logged but no sensitive data included in logs

## Build System

### Compilation Process

Uses Nuitka to compile Python source to native Windows executable.

**Build Script:** `build.py`

**Build Modes:**

**Fast Mode:**
- No LTO (Link Time Optimization)
- Console window visible for debugging
- Faster compilation (minutes vs hours)
- Larger executable size
- Used during development

**Production Mode:**
- Enables LTO for optimization
- Console window hidden
- Slower compilation (1-2 hours)
- Smaller executable, faster runtime
- Used for deployment

**Build Process:**
1. Compile Qt resource file (`resources.qrc`) to `resources_rc.py`
2. Run Nuitka on `interface.py` to create CafeSentinel.exe
3. Run Nuitka on `watchdog_service.py` to create SentinelService.exe
4. Create nested folder structure for deployment
5. Copy both executables and support files to output directory

### Deployment Structure

```
dist/CafeSentinelDeploy/CafeSentinel/
├── CafeSentinel.exe              # Main application
├── install_monitor.bat           # Startup registration script
└── SentinelService/
    └── SentinelService.exe       # Watchdog process
```

**Generated at Runtime:**
- `cscf.dll` (encrypted config)
- `cron.dll` (encrypted passwords)
- `info.log` (current day log)
- `probes/` (archived logs with retention cleanup)
- `config_backups/` (encrypted config backups)

### Nuitka Configuration

Key compilation flags:
- `--standalone`: Includes all dependencies
- `--onefile`: Single executable (or separate for two processes)
- `--windows-disable-console`: Hides console in production
- `--enable-plugin=pyside6`: Bundles PySide6 framework
- `--lto=yes`: Link Time Optimization (production only)

## Startup Registration

### Automatic Startup

**install_monitor.bat:**
- Registers SentinelService.exe in Windows Task Scheduler
- Configured to run at user logon
- Runs with highest privileges (admin)
- Persistent across reboots

**Task Scheduler Configuration:**
- Trigger: At logon of specific user
- Action: Start program (SentinelService.exe)
- Run with highest privileges: Enabled
- Run whether user is logged on or not: Enabled

**Startup Sequence:**
1. Windows boots
2. User logs in
3. Task Scheduler starts SentinelService.exe (watchdog)
4. Watchdog detects CafeSentinel.exe not running
5. Watchdog launches CafeSentinel.exe
6. Main application starts monitoring and initializes logging system
7. Log retention cleanup executes on startup
8. Both processes enter mutual monitoring loop

### Alternative Methods

**Registry Run Key (Optional):**
- Add SentinelService.exe to `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
- Starts at user logon without Task Scheduler
- Less reliable for admin privileges

**Manual Execution:**
- User double-clicks SentinelService.exe
- Watchdog starts and launches main application
- Requires manual intervention after each reboot

## Dependencies

### Python Packages

**Core Framework:**
- `PySide6` (6.x): Qt framework for GUI, threading, signals
- `requests` (2.x): HTTP client for Discord webhooks and API client

**Monitoring:**
- `mss` (9.x): Multi-monitor screenshot capture library
- `Pillow` (10.x): Image processing for screenshot resizing and format conversion

**Server:**
- `Flask` (3.x): REST API web framework
- `flask-cors` (4.x): Cross-Origin Resource Sharing support

**Security:**
- `cryptography` (41.x): Fernet encryption for config and password vault

### Build Dependencies

- `Nuitka` (1.8.x): Python to C compiler
- `zstandard`: Compression library for Nuitka
- `ordered-set`: Nuitka internal dependency

### System Requirements

**Operating System:**
- Windows 10 or Windows 11
- 64-bit architecture required

**Privileges:**
- Administrator rights mandatory
- Required for raw ICMP sockets
- Auto-elevation on startup if not running as admin

**Runtime:**
- Python 3.10+ (for development)
- Compiled executable requires no Python installation

**Network:**
- Local network connectivity for PC monitoring
- Internet access for Discord notifications (optional)
- Open port 5000 for API server (for Manager connectivity)

## Resource Management

### Path Resolution

**ResourceManager (utils/resource_manager.py):**

Handles path differences between script mode and compiled executable.

**Detection Logic:**
- Checks for `sys.frozen` attribute (PyInstaller)
- Checks for `__compiled__` module (Nuitka)
- Returns appropriate base directory based on mode

**Path Resolution:**
- Script mode: Returns script file directory
- Compiled mode: Returns executable directory
- Ensures config, logs, and other files written to correct location

**Usage Pattern:**
```python
config_path = ResourceManager.get_resource_path("cscf.dll")
log_path = ResourceManager.get_resource_path("info.log")
```

All file operations in application use ResourceManager for path resolution.

## Known Behaviors

### Application Behavior

- First run displays setup wizard requiring admin and privacy passwords
- Config file auto-created with defaults if missing
- Log retention cleanup executes automatically on startup
- Screenshot capture requires at least one monitor connected
- Network monitoring requires raw socket permissions (admin rights)
- Watchdog process remains running even if main app exits normally
- API server binds to all interfaces (0.0.0.0) for network accessibility

### Hot-Reload Behavior

- Changes take effect within 2 seconds of config update
- Worker thread state preserved (no restart)
- Monitoring continues without interruption during reload
- Invalid config rejected with error, previous config retained
- Screenshot timer resets on interval change
- Log retention changes apply on next application restart

### Network Monitoring

- Ping failures under minimum incident duration ignored but logged as jitter
- Internet verification requires both primary and secondary target failure
- PC state changes require stability period before confirmation
- SessionManager freezes state during network outages to prevent false alerts
- Jitter events logged to provide visibility into transient connectivity issues

### File System

- Encrypted files (`cscf.dll`, `cron.dll`) not readable by text editors
- Config only decryptable on machine where created (hardware-specific key)
- Archived logs in `probes/` automatically deleted based on retention policy
- Archive deletion via API bypasses Windows recycle bin (permanent)
- Log rotation happens seamlessly without data loss

### Logging Behavior

- Memory buffer holds last 500 lines for fast API access
- Requests ≤500 lines served from RAM (fast)
- Requests >500 lines read from disk (complete history)
- Log format includes full timestamp and structured categories
- All log messages sanitized to prevent information disclosure
- Retention cleanup runs only on startup, not during runtime
- Watchdog lifecycle events written using raw append to avoid dependency conflicts
- Screenshot capture failures logged for troubleshooting

## Critical Configuration Requirements

### Field Name Exactness

SessionManager relies on exact field names in configuration.

**Required Field Names:**
- `min_session_minutes` (not `session_stability_seconds`)
- `batch_delay_seconds` (not `batch_delay`)
- `hourly_snapshot_enabled` (not `hourly_snapshot`)

**System Settings Field Names:**
- `env_state` (stealth mode toggle)
- `log_retention_days` (retention policy)

**Consequence of Incorrect Names:**
- SessionManager uses hardcoded default values
- Configured values ignored silently
- Unexpected behavior in occupancy tracking and notifications

**Validation:**
- ConfigManager validates structure but not field name variants
- Manager application must send exact field names
- Settings dialog uses exact field names in form submission

***

**Document Version:** 2.1  
**Last Updated:** December 10, 2025  
**Changes in 2.1:**
- Added asynchronous screenshot upload architecture with threading
- Added watchdog lifecycle logging with exit code interpretation
- Added network jitter visibility for sub-threshold outages
- Added startup configuration snapshot logging
- Updated log categories to include WATCHDOG events
- Documented screenshot capture failure logging

***

There you go! Complete updated documentation with all the new features properly integrated.