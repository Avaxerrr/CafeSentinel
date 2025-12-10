# Logging System

## Architecture

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

## Log Rotation

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

## Log Retention & Cleanup

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

## Log Format

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

## Smart API Log Serving

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
```
{
  "status": "success",
  "lines": 2000,
  "source": "disk",
  "logs": ["..."]
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
