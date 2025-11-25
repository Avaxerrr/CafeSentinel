import subprocess
import sys
import time
import os
import ctypes

from PySide6.QtWidgets import QApplication

from controllers.system_tray_app import SystemTrayController
from models.startup_manager import StartupManager

# CONFIGURATION
TARGET_SCRIPT = "interface.py"


def is_admin():
    """Check if the Watchdog itself has Admin rights"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_watchdog():
    # 1. Determine what to launch
    if getattr(sys, 'frozen', False):
        # If we are an EXE, we launch ourselves with a special flag OR
        # if you packaged interface.py separately, we launch that.
        # simplest for now: Assume you will compile 'interface.py' as the main EXE?
        # NO, main.py is the entry.

        # For now, let's assume we are running the script logic.
        # If you make an EXE, you should point PyInstaller to 'interface.py' directly
        # AND use a --uac-admin flag, and rely on the Restart logic inside interface.py
        # But you wanted the Watchdog...

        # Let's stick to script logic for safety until you clarify your build process.
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    script_path = os.path.join(base_path, TARGET_SCRIPT)

    print(f"🛡️ WATCHDOG STARTED: Protecting {TARGET_SCRIPT}...")
    print("If you kill the app, I will resurrect it.")

    while True:
        # 2. Launch the GUI as a subprocess
        try:
            if getattr(sys, 'frozen', False):
                # If frozen, we can't easily call 'python interface.py'.
                # You might need to build TWO exes: 'Watchdog.exe' and 'CafeSentinel.exe'.
                # For now, let's print a warning if frozen.
                print("⚠️ WARNING: Watchdog logic in single-file EXE requires specialized build.")
                # Fallback: Just run the script logic if files exist
                p = subprocess.Popen([sys.executable, script_path])
            else:
                p = subprocess.Popen([sys.executable, script_path])

            # 3. Wait for the GUI to close
            exit_code = p.wait()

            # 4. DECIDE: Restart or Quit?
            if exit_code == 0:
                print("✅ CLEAN EXIT DETECTED. Watchdog ending.")
                break
            else:
                print(f"⚠️ ABNORMAL TERMINATION (Code {exit_code}).")
                print("Resurrecting app in 1 second...")
                time.sleep(1)

        except Exception as e:
            print(f"❌ Watchdog Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    # 1. Check Admin Rights (Elevate if needed, but usually Watchdog handles this)
    if not is_admin():
        print("Requesting Admin Privileges...")
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{os.path.abspath(__file__)}"', None, 1
            )
        except:
            print("Failed to elevate.")
        sys.exit()

    # 2. Register Startup (Safe to do here)
    StartupManager.ensure_startup()

    # 3. Run App
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    controller = SystemTrayController(app)

    sys.exit(app.exec())
