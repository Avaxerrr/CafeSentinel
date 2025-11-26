import json
import time
import os
from datetime import datetime
from PySide6.QtCore import QObject, Signal

from models.network_tools import NetworkTools
from models.event_logger import EventLogger
from models.discord_notifier import DiscordNotifier
from models.screen_capture import ScreenCapture
from models.app_logger import AppLogger


class SentinelWorker(QObject):
    sig_status_update = Signal(str, str, str, bool)
    sig_pc_update = Signal(list)

    def __init__(self, config_path="config.json"):
        super().__init__()
        self.running = True

        # If True, routine screenshots are skipped. Incidents still capture.
        self.privacy_mode = False

        AppLogger.log("SYS_INIT: Kernel thread attached.")

        self.config = self.load_config(config_path)
        self.pc_list = self.generate_pc_list()

        self.last_status = "ONLINE"
        self.incident_start_time = None
        self.current_client_count = 0

        self.notifier = DiscordNotifier(self.config)
        self.camera = ScreenCapture(self.config)

        # --- TIMERS (Only Screenshot remains) ---
        self.last_routine_check = datetime.now()
        self.routine_interval_minutes = self.config.get('screenshot_settings', {}).get('interval_minutes', 60)

        AppLogger.log(f"CFG_LOAD: Interval_T1={self.routine_interval_minutes}m | Buffer_Mode=LOCAL")

    def load_config(self, config_path):
        """Load configuration from JSON file."""
        try:
            # Use ResourceManager to get the correct path
            from utils.resource_manager import ResourceManager
            full_path = ResourceManager.get_resource_path(config_path)

            with open(full_path, 'r') as f:
                config = json.load(f)

            interval_minutes = config.get('screenshot_settings', {}).get('interval_minutes', 60)
            AppLogger.log(f"CFG_LOAD: Interval_T1={interval_minutes}m | Buffer_Mode=LOCAL")
            return config
        except Exception as e:
            AppLogger.log(f"CFG_ERROR: {e}")
            return {}

    def generate_pc_list(self):
        settings = self.config.get('monitor_settings', {})
        subnet = settings.get('pc_subnet', '192.168.1')
        start = settings.get('pc_start_range', 110)
        count = settings.get('pc_count', 20)
        return [f"{subnet}.{start + i}" for i in range(count)]

    def handle_routine_check(self):
        now = datetime.now()
        elapsed = now - self.last_routine_check

        if elapsed.total_seconds() > (self.routine_interval_minutes * 60):
            self.last_routine_check = now

            # "Routine Screenshot" -> "Visual telemetry sync"
            AppLogger.log(f"TASK_SCHED: Executing V-Telemetry Sync ({self.routine_interval_minutes}m)")
            img_data, _ = self.camera.capture_to_memory()

            self.notifier.send_hourly_occupancy(
                self.current_client_count,
                len(self.pc_list),
                screenshot_data=img_data
            )

    def handle_state_change(self, new_status):
        current_time = datetime.now()

        if self.last_status == "ONLINE" and new_status != "ONLINE":
            self.incident_start_time = current_time
            AppLogger.log(f"STATE_CHANGE: [ONLINE] -> [{new_status}] | FLAG: CRITICAL")

        elif self.last_status != "ONLINE" and new_status == "ONLINE":
            if self.incident_start_time:
                AppLogger.log(f"STATE_CHANGE: [{self.last_status}] -> [ONLINE] | RECOVERY_ACK")

                EventLogger.log_resolution(self.incident_start_time, current_time, self.last_status)
                img_data, _ = self.camera.capture_to_memory()
                duration = current_time - self.incident_start_time
                duration_str = str(duration).split('.')[0]

                self.notifier.send_outage_report(
                    duration_str, self.last_status, self.current_client_count,
                    self.incident_start_time, current_time, screenshot_data=img_data
                )
                self.incident_start_time = None

        self.last_status = new_status

    def stop(self):
        self.running = False

    def start_monitoring(self):
        AppLogger.log("DAEMON: Main loop sequence initiated [PID: ACTIVE]")

        targets = self.config.get('targets', {})
        monitor_settings = self.config.get('monitor_settings', {})
        interval = monitor_settings.get('interval_seconds', 2)

        router_ip = targets.get('router', '192.168.1.1')
        server_ip = targets.get('server', '192.168.1.200')
        internet_ip = targets.get('internet', '8.8.8.8')

        while self.running:
            loop_start = time.time()
            timestamp = datetime.now().strftime("%H:%M:%S")

            try:
                # 1. Scan Clients
                online_clients = NetworkTools.scan_hosts(self.pc_list)
                self.current_client_count = len(online_clients)

                gui_client_data = []
                for i, ip in enumerate(self.pc_list):
                    is_alive = ip in online_clients
                    gui_client_data.append({"name": f"PC-{i + 1}", "ip": ip, "is_alive": is_alive})
                self.sig_pc_update.emit(gui_client_data)

                # 2. Scan Infra
                infra_status = NetworkTools.scan_hosts([router_ip, server_ip, internet_ip])
                router_ok = router_ip in infra_status
                server_ok = server_ip in infra_status
                internet_ok = internet_ip in infra_status

                # 3. Logic
                current_status = "ONLINE"
                gui_comp = "SYSTEM"
                gui_msg = "ONLINE"
                gui_err = False

                if not router_ok:
                    current_status = "ROUTER_DOWN"
                    gui_comp = "ROUTER"
                    gui_msg = "GATEWAY LOST"
                    gui_err = True
                elif not server_ok:
                    current_status = "SERVER_DOWN"
                    gui_comp = "SERVER"
                    gui_msg = "SERVER LOST"
                    gui_err = True
                elif not internet_ok:
                    current_status = "ISP_DOWN"
                    gui_comp = "ISP"
                    gui_msg = "NO INTERNET"
                    gui_err = True

                self.handle_state_change(current_status)
                self.handle_routine_check()

                # No handle_log_upload() call here anymore!

                self.sig_status_update.emit(timestamp, gui_comp, gui_msg, gui_err)

            except Exception as e:
                AppLogger.log(f"EXCEPT_THROW: Loop Runtime Fault: {e}")

            elapsed = time.time() - loop_start
            sleep_time = max(0.1, interval - elapsed)
            time.sleep(sleep_time)
