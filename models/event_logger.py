import csv
import os
from datetime import datetime


class EventLogger:
    LOG_FILE = "incidents_log.csv"

    @staticmethod
    def log_resolution(start_time, end_time, cause):
        """
        Writes a resolved incident to the CSV.
        start_time: datetime object
        end_time: datetime object
        cause: str (e.g., "ISP_DOWN")
        """
        # Calculate duration
        duration = end_time - start_time
        duration_str = str(duration).split('.')[0]  # Format: H:M:S (remove microseconds)

        # Timestamps for CSV
        start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

        # Check if file exists to write headers
        file_exists = os.path.isfile(EventLogger.LOG_FILE)

        try:
            with open(EventLogger.LOG_FILE, mode='a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Start Time", "End Time", "Duration", "Cause", "Notes"])

                writer.writerow([start_str, end_str, duration_str, cause, "Auto-Resolved"])

            print(f"📝 LOG SAVED: {cause} for {duration_str}")
            return True
        except Exception as e:
            print(f"❌ LOG ERROR: {e}")
            return False
