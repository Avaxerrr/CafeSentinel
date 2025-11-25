import os
import sys
from datetime import datetime


class AppLogger:
    _current_log_path = None

    @staticmethod
    def get_log_path():
        # Determine folder (Exe vs Script)
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        log_dir = os.path.join(base_dir, "sentinel_logs")

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        date_str = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(log_dir, f"log_{date_str}.txt")

    @staticmethod
    def log(message):
        """
        Explicitly writes a message to the log file and console.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {message}"

        # 1. Print to Console
        print(full_msg)

        # 2. Append to File (Open/Close immediately to ensure save)
        path = AppLogger.get_log_path()
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(full_msg + "\n")
        except Exception as e:
            print(f"LOGGING ERROR: {e}")
