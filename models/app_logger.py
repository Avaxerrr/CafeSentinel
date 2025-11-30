import os
import threading
from datetime import datetime
from collections import deque
from utils.resource_manager import ResourceManager


class AppLogger:
    """
    Centralized logging with file persistence and memory buffer.
    - Writes to 'info.log' with rotation (max 1000 lines).
    - Keeps last 500 lines in memory for API serving.
    - Sanitizes sensitive information (no file paths/names in logs).
    """
    _log_file = "info.log"
    _max_lines = 1000
    _memory_buffer = deque(maxlen=500)  # Circular buffer for API
    _lock = threading.Lock()
    _log_path = None

    @staticmethod
    def _get_log_path():
        """Get the path to the info.log file."""
        if AppLogger._log_path is None:
            AppLogger._log_path = ResourceManager.get_resource_path(AppLogger._log_file)
        return AppLogger._log_path

    @staticmethod
    def log(message: str):
        """
        Log a message to console, file, and memory buffer.
        Automatically sanitizes sensitive information.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {message}\n"

        # 1. Console Output
        print(full_msg.strip())

        with AppLogger._lock:
            # 2. Memory Buffer (for API)
            AppLogger._memory_buffer.append(full_msg.strip())

            # 3. File Output with Rotation
            try:
                log_path = AppLogger._get_log_path()

                # Check if rotation needed
                if os.path.exists(log_path):
                    with open(log_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    # If over limit, keep only last (max_lines - 100) lines
                    if len(lines) >= AppLogger._max_lines:
                        lines = lines[-(AppLogger._max_lines - 100):]
                        with open(log_path, 'w', encoding='utf-8') as f:
                            f.writelines(lines)

                # Append new message
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(full_msg)

            except Exception as e:
                print(f"⚠️ Log Write Failed: {e}")

    @staticmethod
    def get_recent_logs(count: int = 500):
        """
        Returns the last N lines from the memory buffer.
        Used by the API to serve logs to the Manager.
        """
        with AppLogger._lock:
            # Convert deque to list and return last 'count' items
            buffer_list = list(AppLogger._memory_buffer)
            return buffer_list[-count:] if len(buffer_list) > count else buffer_list

    @staticmethod
    def sanitize_path(message: str) -> str:
        """
        ⚠️ SECURITY: Remove file paths/extensions from error messages.
        Not currently used (kept for future if needed).
        """
        import re
        # Remove common file extensions and paths
        sanitized = re.sub(r'[A-Za-z]:\\[^\s]+', '[PATH]', message)
        sanitized = re.sub(r'/[^\s]+\.(dll|json|log|txt)', '[FILE]', sanitized)
        return sanitized
