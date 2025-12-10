# Configuration System

## Core Components

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

## Configuration Structure

### File Structure

Configuration stored as encrypted file `cscf.dll` in application directory.

**Encryption Details:**
- Format: Fernet encrypted JSON string
- Key: Derived from machine-specific hardware fingerprint via SecurityManager
- Migration: Automatically converts legacy `config.json` to encrypted format
- Backup: Encrypted backups stored in `config_backups/` subdirectory

### Configuration Schema

```
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
