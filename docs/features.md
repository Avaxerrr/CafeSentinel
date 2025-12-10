# Features & UI

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
- Webhooks optional (system works without Discord notifications)\
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

## System Tray Controller

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
