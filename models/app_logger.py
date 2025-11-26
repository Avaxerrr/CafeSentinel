import os
import sys
from datetime import datetime
from utils.resource_manager import ResourceManager


class AppLogger:
    _current_log_path = None

    @staticmethod
    def get_log_path():
        """Get the path to today's log file."""
        base_dir = ResourceManager.get_base_dir()
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

        # 2. Append to File
        try:
            log_path = AppLogger.get_log_path()
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(full_msg + '\n')
        except Exception as e:
            print(f"⚠️ Log Write Failed: {e}")
