import subprocess
import sys
import os
import logging
import winreg


class StartupManager:
    TASK_NAME = "CafeSentinelMonitor"
    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    REG_NAME = "CafeSentinel"

    @staticmethod
    def ensure_startup():
        if not getattr(sys, 'frozen', False):
            return  # Skip in dev mode

        # Locate the Watchdog Executable
        # Sys.executable is CafeSentinel.exe in .../CafeSentinel/
        # Watchdog is in .../CafeSentinel/SentinelService/SentinelService.exe

        base_dir = os.path.dirname(sys.executable)  # .../CafeSentinel
        watchdog_exe = os.path.join(base_dir, "SentinelService", "SentinelService.exe")

        if not os.path.exists(watchdog_exe):
            logging.error(f"❌ Startup Error: Could not find {watchdog_exe}")
            return

        exe_path = f'"{watchdog_exe}"'

        # --- METHOD 1: Registry Run Key ---
        try:
            # Open the Run key
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, StartupManager.REG_PATH, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, StartupManager.REG_NAME, 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
            logging.info("✅ Registry Startup Key Set")
        except Exception as e:
            logging.error(f"❌ Registry Set Failed: {e}")

        # --- METHOD 2: Task Scheduler (Force Update) ---
        create_cmd = (
            f'schtasks /create /tn "{StartupManager.TASK_NAME}" '
            f'/tr "{exe_path}" '
            f'/sc ONLOGON '
            f'/rl HIGHEST '
            f'/f'
        )
        subprocess.call(create_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logging.info("✅ Task Scheduler Entry Updated")
