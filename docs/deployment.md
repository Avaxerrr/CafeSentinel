# Deployment & Build

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
```
config_path = ResourceManager.get_resource_path("cscf.dll")
log_path = ResourceManager.get_resource_path("info.log")
```

All file operations in application use ResourceManager for path resolution.
