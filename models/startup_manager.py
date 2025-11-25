import subprocess
import sys
import os
import logging


class StartupManager:
    TASK_NAME = "CafeSentinelMonitor"

    @staticmethod
    def ensure_startup():
        """
        Registers the application in Windows Task Scheduler to run
        with HIGHEST privileges on user logon.
        Handles both .py script and frozen .exe execution.
        """
        # 1. Determine the correct execution command
        if getattr(sys, 'frozen', False):
            # Running as compiled EXE
            exe_path = sys.executable
            action = f'"{exe_path}"'
            logging.info(f"⚙️ Startup Mode: EXE Detected ({exe_path})")
        else:
            # Running as Python Script
            # We want to launch 'main.py' (The Watchdog), not the current script if it's different
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            target_script = os.path.join(current_dir, "main.py")
            python_exe = sys.executable
            action = f'"{python_exe}" "{target_script}"'
            logging.info(f"⚙️ Startup Mode: Script Detected ({target_script})")

        # 2. Check if task already exists
        check_cmd = f'schtasks /query /tn "{StartupManager.TASK_NAME}"'
        try:
            subprocess.check_output(check_cmd, stderr=subprocess.STDOUT)
            logging.info(f"✅ Startup task '{StartupManager.TASK_NAME}' is already active.")
            return
        except subprocess.CalledProcessError:
            pass  # Task not found, proceed to create

        logging.info(f"⚙️ Creating startup task '{StartupManager.TASK_NAME}'...")

        # 3. Create Task
        # /sc ONLOGON = Run when user logs in
        # /rl HIGHEST = Run as Admin
        # /f = Force overwrite
        create_cmd = [
            "schtasks", "/create",
            "/tn", StartupManager.TASK_NAME,
            "/tr", action,
            "/sc", "ONLOGON",
            "/rl", "HIGHEST",
            "/f"
        ]

        try:
            # Hide the console window for the command
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            subprocess.check_call(create_cmd, startupinfo=startupinfo, stdout=subprocess.DEVNULL)
            logging.info("✅ Successfully added application to Windows Startup.")
        except subprocess.CalledProcessError as e:
            logging.error(f"❌ Failed to create startup task: {e}")
