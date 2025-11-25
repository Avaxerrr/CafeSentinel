import json
import time
from datetime import datetime, timedelta  # <--- Added timedelta
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import QObject, Signal
from models.network_tools import NetworkTools
from models.event_logger import EventLogger
from models.discord_notifier import DiscordNotifier
from models.screen_capture import ScreenCapture


class SentinelWorker(QObject):
    sig_status_update = Signal(str, str, str, bool)
    sig_pc_update = Signal(list)

    def __init__(self, config_path="config.json"):
        super().__init__()
        self.running = True
        self.config = self.load_config(config_path)
        self.pc_list = self.generate_pc_list()

        # --- MEMORY ---
        self.last_status = "ONLINE"
        self.incident_start_time = None
        self.current_client_count = 0

        # --- SUB-MODULES ---
        self.notifier = DiscordNotifier(self.config)
        self.camera = ScreenCapture(self.config)

        # --- TIMING LOGIC (CORRECTED) ---
        # Start the "Last Check" in the past so it triggers immediately on startup?
        # Or set to NOW so it waits for the first interval?
        # Let's set it to NOW so it doesn't spam you immediately on startup.
        self.last_routine_check = datetime.now()

        # Load the interval from config (default to 60 mins if missing)
        self.routine_interval_minutes = self.config.get('screenshot_settings', {}).get('interval_minutes', 60)
        print(f"⏰ Routine Check Interval set to: {self.routine_interval_minutes} minutes")

    def load_config(self, path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            return {}

    def generate_pc_list(self):
        settings = self.config.get('monitor_settings', {})
        subnet = settings.get('pc_subnet', '192.168.1')
        start = settings.get('pc_start_range', 110)
        count = settings.get('pc_count', 20)
        return [{"name": f"PC-{i + 1}", "ip": f"{subnet}.{start + i}"} for i in range(count)]

    def check_single_pc(self, pc_info):
        is_alive = NetworkTools.ping(pc_info['ip'])
        return {"name": pc_info['name'], "ip": pc_info['ip'], "is_alive": is_alive}

    def handle_routine_check(self):
        """Checks if enough time has passed for the routine screenshot/occupancy report"""
        now = datetime.now()
        elapsed = now - self.last_routine_check

        # Check if elapsed time is greater than the configured interval (in seconds)
        if elapsed.total_seconds() > (self.routine_interval_minutes * 60):
            self.last_routine_check = now

            # 1. Take Screenshot (Routine)
            print(f"📸 Time Delta reached ({self.routine_interval_minutes}m). Taking Routine Screenshot...")
            img_data = self.camera.capture_to_memory()

            # 2. Send Report
            print("📊 Sending Routine Discord Report...")
            self.notifier.send_hourly_occupancy(
                self.current_client_count,
                len(self.pc_list),
                screenshot_data=img_data
            )

    def handle_state_change(self, new_status):
        current_time = datetime.now()

        # 1. Incident Started
        if self.last_status == "ONLINE" and new_status != "ONLINE":
            self.incident_start_time = current_time
            print(f"⚠️ INCIDENT STARTED: {new_status}")

        # 2. Incident Resolved
        elif self.last_status != "ONLINE" and new_status == "ONLINE":
            if self.incident_start_time:
                # A. Local CSV Log
                EventLogger.log_resolution(
                    self.incident_start_time,
                    current_time,
                    self.last_status
                )

                # B. Capture Evidence Screenshot
                print("📸 Taking Evidence Screenshot...")
                img_data = self.camera.capture_to_memory()

                # C. Discord Alert
                duration = current_time - self.incident_start_time
                duration_str = str(duration).split('.')[0]

                print("🚀 Sending Discord Alert...")
                self.notifier.send_outage_report(
                    duration_str,
                    self.last_status,
                    self.current_client_count,
                    self.incident_start_time,
                    current_time,
                    screenshot_data=img_data
                )

                self.incident_start_time = None

        self.last_status = new_status

    def start_monitoring(self):
        targets = self.config.get('targets', {})
        interval = self.config.get('monitor_settings', {}).get('interval_seconds', 2)

        while self.running:
            timestamp = datetime.now().strftime("%H:%M:%S")

            # 1. Check PCs FIRST
            with ThreadPoolExecutor(max_workers=20) as executor:
                results = list(executor.map(self.check_single_pc, self.pc_list))

            self.current_client_count = sum(1 for pc in results if pc['is_alive'])
            self.sig_pc_update.emit(results)

            # 2. Check Infrastructure
            router_ok = NetworkTools.ping(targets['router'])
            server_ok = NetworkTools.ping(targets['server'])
            internet_ok = NetworkTools.ping(targets['internet'])

            # 3. Diagnose
            current_status = "ONLINE"
            gui_comp = "SYSTEM"
            gui_msg = "ONLINE"
            gui_err = False

            if not router_ok:
                current_status = "ROUTER_DOWN"
                gui_comp = "ROUTER"
                gui_msg = "GATEWAY UNREACHABLE"
                gui_err = True
            elif not server_ok:
                current_status = "SERVER_DOWN"
                gui_comp = "SERVER"
                gui_msg = "PXE SERVER LOST"
                gui_err = True
            elif not internet_ok:
                current_status = "ISP_DOWN"
                gui_comp = "ISP"
                gui_msg = "NO INTERNET ACCESS"
                gui_err = True

            # 4. Process Logic
            self.handle_state_change(current_status)
            self.handle_routine_check()  # <--- Updated Function Call

            # 5. Update GUI
            self.sig_status_update.emit(timestamp, gui_comp, gui_msg, gui_err)

            time.sleep(interval)

    def stop(self):
        self.running = False
