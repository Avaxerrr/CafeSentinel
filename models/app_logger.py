import os
import threading
from datetime import datetime
from collections import deque
from utils.resource_manager import ResourceManager


class AppLogger:
    """
    Centralized logging with daily rotation and archive.
    - Active log: 'info.log' (current day only)
    - Archive: 'probes/' folder (historical logs, never auto-deleted)
    - Memory buffer: Last 500 lines for real-time API serving
    """
    _log_file = "info.log"
    _archive_dir = "probes"
    _max_file_size = 5 * 1024 * 1024  # 5MB per file
    _memory_buffer = deque(maxlen=500)
    _lock = threading.Lock()
    _log_path = None
    _archive_path = None
    _current_date = None

    @staticmethod
    def _get_log_path():
        """Get the path to the active info.log file."""
        if AppLogger._log_path is None:
            AppLogger._log_path = ResourceManager.get_resource_path(AppLogger._log_file)
        return AppLogger._log_path

    @staticmethod
    def _get_archive_path():
        """Get the path to the probes/ archive folder."""
        if AppLogger._archive_path is None:
            AppLogger._archive_path = ResourceManager.get_resource_path(AppLogger._archive_dir)
            if not os.path.exists(AppLogger._archive_path):
                os.makedirs(AppLogger._archive_path)
        return AppLogger._archive_path

    @staticmethod
    def _check_rotation():
        """
        Check if we need to rotate the log:
        1. Date changed (midnight rollover or app restart after date change)
        2. File size exceeds limit
        """
        today = datetime.now().strftime("%Y-%m-%d")
        log_path = AppLogger._get_log_path()

        # Date-based rotation
        if AppLogger._current_date is None:
            AppLogger._current_date = today

        if AppLogger._current_date != today and os.path.exists(log_path):
            AppLogger._rotate_log(AppLogger._current_date)
            AppLogger._current_date = today

        # Size-based rotation
        if os.path.exists(log_path):
            file_size = os.path.getsize(log_path)
            if file_size >= AppLogger._max_file_size:
                timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
                AppLogger._rotate_log(timestamp)

    @staticmethod
    def _rotate_log(date_label: str):
        """Move current info.log to probes/ folder with date stamp."""
        try:
            log_path = AppLogger._get_log_path()
            archive_path = AppLogger._get_archive_path()

            if not os.path.exists(log_path):
                return

            # Move to archive
            archived_name = f"info-{date_label}.log"
            archived_full_path = os.path.join(archive_path, archived_name)

            # If file already exists (size rotation), append counter
            counter = 1
            while os.path.exists(archived_full_path):
                archived_name = f"info-{date_label}-part{counter}.log"
                archived_full_path = os.path.join(archive_path, archived_name)
                counter += 1

            os.rename(log_path, archived_full_path)
            print(f"[LOGGER] Rotated log to {archived_name}")

        except Exception as e:
            print(f"⚠️ Log Rotation Failed: {e}")

    @staticmethod
    def log(message: str):
        """
        Log a message to console, file, and memory buffer.
        Automatically handles rotation.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {message}\n"

        # 1. Console Output
        print(full_msg.strip())

        with AppLogger._lock:
            # 2. Memory Buffer (for real-time API)
            AppLogger._memory_buffer.append(full_msg.strip())

            # 3. Check if rotation needed
            AppLogger._check_rotation()

            # 4. File Output
            try:
                log_path = AppLogger._get_log_path()
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(full_msg)

            except Exception as e:
                print(f"⚠️ Log Write Failed: {e}")

    @staticmethod
    def get_recent_logs(count: int = 500):
        """
        Returns the last N lines from TODAY's log (memory buffer).
        Used by the API for real-time monitoring.
        """
        with AppLogger._lock:
            buffer_list = list(AppLogger._memory_buffer)
            return buffer_list[-count:] if len(buffer_list) > count else buffer_list

    @staticmethod
    def get_archive_list():
        """
        Returns a list of archived log filenames in probes/.
        Sorted newest first.
        """
        try:
            archive_path = AppLogger._get_archive_path()
            files = [f for f in os.listdir(archive_path) if f.startswith("info-") and f.endswith(".log")]
            return sorted(files, reverse=True)
        except Exception:
            return []

    @staticmethod
    def get_archived_log(filename: str):
        """
        Returns the contents of a specific archived log file.
        Returns None if file doesn't exist or error occurs.
        """
        try:
            archive_path = AppLogger._get_archive_path()
            file_path = os.path.join(archive_path, filename)

            # Security: Prevent path traversal
            if not os.path.abspath(file_path).startswith(os.path.abspath(archive_path)):
                return None

            if not os.path.exists(file_path):
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            return [line.strip() for line in lines]

        except Exception as e:
            print(f"⚠️ Archive Read Failed: {e}")
            return None

    @staticmethod
    def sanitize_path(message: str) -> str:
        """
        ⚠️ SECURITY: Remove file paths/extensions from error messages.
        Not currently used (kept for future if needed).
        """
        import re
        sanitized = re.sub(r'[A-Za-z]:\\[^\s]+', '[PATH]', message)
        sanitized = re.sub(r'/[^\s]+\.(dll|json|log|txt)', '[FILE]', sanitized)
        return sanitized
