# Network Monitoring System

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
[2025-12-09 14:22:14] [NETWORK] ISP jitter detected (3.8s) - Below threshold (10s).\
[2025-12-09 15:45:30] [ALERT] Router DOWN | Timer Started\
[2025-12-09 15:45:36] [NETWORK] Router jitter detected (5.2s) - Below threshold (10s).\
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
