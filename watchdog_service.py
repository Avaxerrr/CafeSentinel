"""
CafeSentinel Watchdog Service
"""
import subprocess
import sys
import time
import os
import ctypes

# ==============================================================================
# --- CONFIG ---
# ==============================================================================
TARGET_SCRIPT = "interface.py"
TARGET_EXE = "CafeSentinel.exe"


def is_admin():
    """Check if the Watchdog has Admin rights."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def is_compiled():
    """Robust check to see if we're running as a compiled executable."""
    has_frozen = getattr(sys, 'frozen', False)
    try:
        from __main__ import __compiled__
        has_compiled = True
    except ImportError:
        has_compiled = False
    return has_frozen or has_compiled


def get_target_path():
    """Get the path to CafeSentinel.exe."""
    if is_compiled():
        # Running as compiled EXE: .../CafeSentinel/SentinelService/SentinelService.exe
        # Target: .../CafeSentinel/CafeSentinel.exe
        exe_path = os.path.abspath(sys.executable)
        service_dir = os.path.dirname(exe_path)
        main_app_dir = os.path.dirname(service_dir)
        target_path = os.path.join(main_app_dir, TARGET_EXE)
    else:
        # Script mode
        script_dir = os.path.dirname(os.path.abspath(__file__))
        target_path = os.path.join(script_dir, TARGET_SCRIPT)

    if not os.path.exists(target_path):
        print(f"\n❌ ERROR: Target not found at {target_path}")
        sys.exit(1)

    return target_path


def process_exists(process_name):
    """Check if a process is running using tasklist."""
    try:
        # /NH = No Header, /FI = Filter
        cmd = f'tasklist /FI "IMAGENAME eq {process_name}" /NH'
        output = subprocess.check_output(cmd, shell=True).decode()
        # If found, output contains the process name. If not, it says "No tasks..."
        return process_name.lower() in output.lower()
    except:
        return False


def run_watchdog():
    """Main watchdog loop."""
    target_path = get_target_path()
    target_name = os.path.basename(target_path)

    # For script mode, target name is python.exe usually, so we rely on simple logic
    # or just assume we only really care about this in EXE mode.
    if not is_compiled():
        print("⚠️ Running in script mode - Process detection might be inaccurate.")

    print("\n" + "=" * 60)
    print("🛡️  CAFSENTINEL WATCHDOG SERVICE")
    print("=" * 60)

    while True:
        try:
            # 1. Check if ALREADY running (Attach Mode)
            # Only reliable in EXE mode where name matches CafeSentinel.exe
            if is_compiled() and process_exists(target_name):
                print(f"[{time.strftime('%H:%M:%S')}] 📎 Target '{target_name}' is running. Attaching...")

                # Poll until it dies
                while process_exists(target_name):
                    time.sleep(3)

                print(f"[{time.strftime('%H:%M:%S')}] ⚠️ Target process disappeared.")

                # NEW CHECK: Setup Cancel / Clean Exit detection
                # Since we can't get exit code in attach mode, we check for the Vault file.
                # If no vault exists, assume it was a Setup Cancel -> Do not restart.
                base_dir = os.path.dirname(target_path)
                vault_path = os.path.join(base_dir, "cron.dll") # Security Vault

                if not os.path.exists(vault_path):
                    print(f"[{time.strftime('%H:%M:%S')}] 🛑 No Vault found. Assuming Setup Cancelled. Exiting.")
                    break

                print("🔄 Restarting...")
                # Loop continues to spawn logic below

            # 2. Start Process (Spawn Mode)
            print(f"[{time.strftime('%H:%M:%S')}] 🚀 Starting {target_name}...")

            if is_compiled():
                p = subprocess.Popen([target_path])
            else:
                p = subprocess.Popen([sys.executable, target_path])

            exit_code = p.wait()

            if exit_code == 0:
                print(f"\n[{time.strftime('%H:%M:%S')}] ✅ CLEAN EXIT (Code 0)")
                break
            elif exit_code == 100:
                print(f"\n[{time.strftime('%H:%M:%S')}] 🛑 SETUP CANCELLED (Code 100) - Stopping Watchdog.")
                break
            else:
                print(f"\n[{time.strftime('%H:%M:%S')}] ⚠️  ABNORMAL EXIT (Code {exit_code})")
                time.sleep(2)

        except Exception as e:
            print(f"\n❌ WATCHDOG ERROR: {e}")
            time.sleep(5)


def main():
    if not is_admin():
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
        except:
            pass
        sys.exit(0)

    run_watchdog()


if __name__ == "__main__":
    main()
