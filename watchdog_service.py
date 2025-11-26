"""
CafeSentinel Watchdog Service - DEBUG VERSION
"""
import subprocess
import sys
import time
import os
import ctypes

# ==============================================================================
# --- DIAGNOSTIC BLOCK ---
# This will run at the very start to see what's happening inside the EXE
# ==============================================================================
print("="*60)
print("--- WATCHDOG DIAGNOSTIC START ---")
print(f"sys.executable: {sys.executable}")
print(f"os.path.abspath(sys.executable): {os.path.abspath(sys.executable)}")

# Check for sys.frozen (PyInstaller)
has_frozen = getattr(sys, 'frozen', False)
print(f"getattr(sys, 'frozen', False): {has_frozen}")

# Check for __compiled__ (Nuitka)
try:
    # Nuitka creates this object
    from __main__ import __compiled__
    has_compiled = True
    print(f"__main__.__compiled__ exists: True")
except ImportError:
    has_compiled = False
    print(f"__main__.__compiled__ exists: False")

print("--- WATCHDOG DIAGNOSTIC END ---")
print("="*60)
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
    """
    Robust check to see if we're running as a compiled executable.
    """
    return has_frozen or has_compiled


def get_target_path():
    """Get the path to CafeSentinel.exe."""
    if is_compiled():
        # Running as compiled EXE
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        deploy_root = os.path.dirname(exe_dir)
        target_dir = os.path.join(deploy_root, "CafeSentinel")
        target_path = os.path.join(target_dir, TARGET_EXE)

        print(f"📍 Running in EXE mode")
        print(f"🎯 Target Path: {target_path}")

        if not os.path.exists(target_path):
            print(f"\n❌ ERROR: {TARGET_EXE} not found!")
            print(f"Expected location: {target_path}")
            input("\nPress Enter to exit...")
            sys.exit(1)

        return target_path
    else:
        # Running as Python script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        target_path = os.path.join(script_dir, TARGET_SCRIPT)

        print(f"📍 Running in Script mode")
        print(f"🎯 Target: {target_path}")

        if not os.path.exists(target_path):
            print(f"\n❌ ERROR: {TARGET_SCRIPT} not found!")
            input("\nPress Enter to exit...")
            sys.exit(1)

        return target_path


def run_watchdog():
    """Main watchdog loop."""
    target_path = get_target_path()
    target_name = os.path.basename(target_path)

    print("\n" + "=" * 60)
    print("🛡️  CAFSENTINEL WATCHDOG SERVICE")
    print("=" * 60)

    while True:
        try:
            print(f"[{time.strftime('%H:%M:%S')}] Starting {target_name}...")

            if is_compiled():
                p = subprocess.Popen([target_path])
            else:
                p = subprocess.Popen([sys.executable, target_path])

            exit_code = p.wait()

            if exit_code == 0:
                print(f"\n[{time.strftime('%H:%M:%S')}] ✅ CLEAN EXIT (Code 0)")
                break
            else:
                print(f"\n[{time.strftime('%H:%M:%S')}] ⚠️  ABNORMAL EXIT (Code {exit_code})")
                time.sleep(2)

        except Exception as e:
            print(f"\n❌ WATCHDOG ERROR: {e}")
            time.sleep(5)


def main():
    """Entry point."""
    if not is_admin():
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
        except Exception:
            pass
        sys.exit(0)

    run_watchdog()


if __name__ == "__main__":
    main()
