import subprocess
import sys
import time
import os
import ctypes

# CONFIGURATION
TARGET_SCRIPT = "interface.py"


def is_admin():
    """Check if the Watchdog itself has Admin rights"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_watchdog():
    # 1. Get absolute path to the GUI script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, TARGET_SCRIPT)

    print(f"🛡️ WATCHDOG STARTED: Protecting {TARGET_SCRIPT}...")
    print("If you kill the app, I will resurrect it.")

    while True:
        # 2. Launch the GUI as a subprocess
        # We use sys.executable to ensure it uses the same Python environment
        p = subprocess.Popen([sys.executable, script_path])

        # 3. Wait for the GUI to close
        exit_code = p.wait()

        # 4. DECIDE: Restart or Quit?
        if exit_code == 0:
            print("✅ CLEAN EXIT DETECTED (Password Used).")
            print("Watchdog shutting down.")
            break  # Break the loop, allowing the script to end
        else:
            print(f"⚠️ ABNORMAL TERMINATION (Code {exit_code}).")
            print("Resurrecting app in 1 second...")
            time.sleep(1)


if __name__ == "__main__":
    # A. Ensure Watchdog is Admin (so it can launch GUI as Admin)
    if not is_admin():
        print("Requesting Admin Privileges for Watchdog...")
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit()  # Close this non-admin instance
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    # B. Run the protection loop
    run_watchdog()
