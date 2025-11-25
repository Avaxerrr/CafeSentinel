import sys
import os
import ctypes
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox
from controllers.system_tray_app import SystemTrayController

# Import the guard
try:
    from admin_guard import AdminGuard
except ImportError:
    AdminGuard = None
    print("⚠️ WARNING: admin_guard.py not found.")


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


if __name__ == "__main__":
    # 1. Check Admin Rights
    if AdminGuard and not is_admin():
        print("Requesting Admin Privileges...")

        # Get the absolute path to the python executable and the script
        # This fixes the issue where the new instance can't find the file
        python_exe = sys.executable
        script_path = os.path.abspath(__file__)

        try:
            # Relaunch with specific paths
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", python_exe, f'"{script_path}"', None, 1
            )
            # SUCCESS: The new window should open now.
            # We exit this "User Mode" instance.
            sys.exit()
        except Exception as e:
            print(f"Admin request failed: {e}")
            # If user clicked 'No', we just stay open in User Mode (Unprotected)
            pass

    # 2. Start Application (ADMIN MODE or Fallback)
    try:
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        # 3. Enable Protection
        if AdminGuard and is_admin():
            print("Admin rights confirmed. Locking process...")
            success = AdminGuard.protect_process()
            if not success:
                print("Failed to lock process.")
        else:
            print("Running in Unprotected Mode (No Admin)")

        # 4. Launch Controller
        controller = SystemTrayController(app)

        print("App Started Successfully.")
        sys.exit(app.exec())

    except Exception as e:
        # Crash Handler
        with open("crash_log.txt", "w") as f:
            f.write(traceback.format_exc())
        QMessageBox.critical(None, "Startup Error", f"App Crashed:\n{e}\n\nCheck crash_log.txt")
