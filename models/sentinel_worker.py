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
    # Updated Signal: timestamp, router_ok, server_ok, isp_ok
    sig_status_update = Signal(str, bool, bool, bool)
    sig_pc_update = Signal(list)

    def __init__(self, config_path="config.json"):
        super().__init__()
        self.running = True
        self.privacy_mode = False

        AppLogger.log("SYS_INIT: Kernel thread attached (Independent Mode).")

        self.config = self.load_config(config_path)
        self.pc_list = self.generate_pc_list()

        # --- Independent Incident Timers ---
        self.router_down_start = None
        self.server_down_start = None
        self.isp_down_start = None

        self.current_client_count = 0

        self.notifier = DiscordNotifier(self.config)
        self.camera = ScreenCapture(self.config)

        # Routine Screenshot Timer
        self.last_routine_check = datetime.now()
        self.routine_interval_minutes = self.config.get('screenshot_settings', {}).get('interval_minutes', 60)

    def load_config(self, config_path):
        try:
            from utils.resource_manager import ResourceManager
            full_path = ResourceManager.get_resource_path(config_path)
            with open(full_path, 'r') as f:
                return json.load(f)
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
            AppLogger.log(f"TASK_SCHED: Executing V-Telemetry Sync ({self.routine_interval_minutes}m)")
            img_data, _ = self.camera.capture_to_memory()

            self.notifier.send_hourly_occupancy(
                self.current_client_count,
                len(self.pc_list),
                screenshot_data=img_data
            )

    def _process_component(self, name, is_online, down_start_time):
        # Generic logic to handle an incident for a component.
        # Returns: The new down_start_time (None if online/resolved, datetime if down)
        now = datetime.now()

        # CASE 1: Component Just Died
        if not is_online and down_start_time is None:
            AppLogger.log(f"ALERT: {name} DOWN | Timer Started")
            return now  # Start the timer

        # CASE 2: Component Just Recovered
        elif is_online and down_start_time is not None:
            duration = now - down_start_time
            duration_str = str(duration).split('.')[0]

            AppLogger.log(f"RECOVERY: {name} Restored | Duration: {duration_str}")

            # Log to CSV
            EventLogger.log_resolution(down_start_time, now, f"{name}_DOWN")

            # Capture evidence
            img_data, _ = self.camera.capture_to_memory()

            # Send Discord Alert
            self.notifier.send_outage_report(
                duration_str, f"{name}_DOWN", self.current_client_count,
                down_start_time, now, screenshot_data=img_data
            )
            return None  # Reset timer

        # CASE 3: No Change (Still Down or Still Up)
        return down_start_time

    def start_monitoring(self):
        AppLogger.log("DAEMON: Independent Monitoring Active")

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
                # 1. Scan Clients (Background)
                online_clients = NetworkTools.scan_hosts(self.pc_list)
                self.current_client_count = len(online_clients)

                gui_client_data = []
                for i, ip in enumerate(self.pc_list):
                    is_alive = ip in online_clients
                    gui_client_data.append({"name": f"PC-{i + 1}", "ip": ip, "is_alive": is_alive})
                self.sig_pc_update.emit(gui_client_data)

                # 2. Independent Infrastructure Scans
                # We ping them individually or in a batch, but process results independently
                infra_status = NetworkTools.scan_hosts([router_ip, server_ip, internet_ip])

                router_ok = router_ip in infra_status
                server_ok = server_ip in infra_status

                # Logic: If Router is DOWN, we physically cannot ping Internet.
                # We force internet_ok to False, but we manage the alert logic separately.
                actual_internet_ping = internet_ip in infra_status

                if not router_ok:
                    # If router is down, internet is effectively down.
                    internet_ok = False
                else:
                    # If router is up, trust the ping
                    internet_ok = actual_internet_ping

                # 3. Incident Processing

                # Router
                self.router_down_start = self._process_component("ROUTER", router_ok, self.router_down_start)

                # Server (Independent)
                self.server_down_start = self._process_component("SERVER", server_ok, self.server_down_start)

                # ISP (Dependent Logic)
                # Only trigger ISP Alert if Router is UP but Internet is DOWN
                if router_ok:
                    self.isp_down_start = self._process_component("ISP", internet_ok, self.isp_down_start)
                else:
                    # If Router is down, we don't blame the ISP yet.
                    pass

                # 4. Emit GUI Update (Raw Status)
                self.sig_status_update.emit(timestamp, router_ok, server_ok, internet_ok)

                # 5. Routine Checks
                self.handle_routine_check()

            except Exception as e:
                AppLogger.log(f"EXCEPT: {e}")

            elapsed = time.time() - loop_start
            sleep_time = max(0.1, interval - elapsed)
            time.sleep(sleep_time)