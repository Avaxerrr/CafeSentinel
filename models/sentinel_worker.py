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
from models.session_manager import SessionManager


class SentinelWorker(QObject):
    # Signal signature: timestamp, router_ok, server_ok, internet_ok
    sig_status_update = Signal(str, bool, bool, bool)
    # Signal signature: List of dicts [{'name': 'PC-1', 'ip': '...', 'is_alive': True}]
    sig_pc_update = Signal(list)

    def __init__(self, config_path="config.json"):
        super().__init__()
        self.running = True
        self.privacy_mode = False

        AppLogger.log("SYS_INIT: Kernel thread attached (Hot-Reload Active).")

        self.config_path_rel = config_path
        self.config_abs_path = None  # Set in load_config
        self.last_cfg_mtime = 0

        self.config = self.load_config(config_path)
        self.pc_list = self.generate_pc_list()

        # Incidents
        self.router_down_start = None
        self.server_down_start = None
        self.isp_down_start = None

        self.current_client_count = 0

        self.notifier = DiscordNotifier(self.config)
        self.camera = ScreenCapture(self.config)
        self.session_manager = SessionManager(self.config, self.notifier)

        # Routine Screenshot
        self.last_screenshot_time = datetime.now()
        self.screenshot_interval = self.config.get('screenshot_settings', {}).get('interval_minutes', 60)

        # Verification Settings
        self._update_verification_settings()

    def load_config(self, config_path):
        try:
            from utils.resource_manager import ResourceManager
            # Get absolute path once and store it
            if not self.config_abs_path:
                self.config_abs_path = ResourceManager.get_resource_path(config_path)

            if os.path.exists(self.config_abs_path):
                self.last_cfg_mtime = os.path.getmtime(self.config_abs_path)
                with open(self.config_abs_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            AppLogger.log(f"CFG_ERROR: {e}")
            return {}

    def check_hot_reload(self):
        """Checks if config file has changed and reloads it safely."""
        try:
            if not self.config_abs_path or not os.path.exists(self.config_abs_path):
                return

            current_mtime = os.path.getmtime(self.config_abs_path)
            if current_mtime > self.last_cfg_mtime:
                AppLogger.log("CFG_WATCH: Change detected. Reloading...")

                # Safe Load
                with open(self.config_abs_path, 'r') as f:
                    new_config = json.load(f)

                # If we get here, JSON is valid. Update everything.
                self.config = new_config
                self.last_cfg_mtime = current_mtime

                # 1. Update Sub-Modules
                self.notifier.update_config(self.config)
                self.session_manager.update_config(self.config)
                self.camera = ScreenCapture(self.config)  # Re-init camera with new settings

                # 2. Update Locals
                self.screenshot_interval = self.config.get('screenshot_settings', {}).get('interval_minutes', 60)
                self._update_verification_settings()

                # 3. Update PC List (In case range changed)
                self.pc_list = self.generate_pc_list()

                AppLogger.log("CFG_WATCH: Hot Reload Complete.")

        except json.JSONDecodeError:
            AppLogger.log("CFG_WATCH: ⚠️ JSON Syntax Error. Keep using old config.")
        except Exception as e:
            AppLogger.log(f"CFG_WATCH: Update Failed: {e}")

    def _update_verification_settings(self):
        self.verify_cfg = self.config.get('verification_settings', {})
        self.retry_delay = self.verify_cfg.get('retry_delay_seconds', 1.0)
        self.secondary_dns = self.verify_cfg.get('secondary_target', '1.1.1.1')

    def generate_pc_list(self):
        settings = self.config.get('monitor_settings', {})
        subnet = settings.get('pc_subnet', '192.168.1')
        start = settings.get('pc_start_range', 110)
        count = settings.get('pc_count', 20)
        return [f"{subnet}.{start + i}" for i in range(count)]

    def handle_routine_screenshot(self):
        if self.privacy_mode:
            return

        now = datetime.now()
        elapsed = now - self.last_screenshot_time

        if elapsed.total_seconds() > (self.screenshot_interval * 60):
            self.last_screenshot_time = now
            AppLogger.log(f"TASK: Capturing Routine Screenshot ({self.screenshot_interval}m)")

            img_data, _ = self.camera.capture_to_memory()
            if img_data:
                self.notifier.send_routine_screenshot(img_data)

    def _verify_component(self, target_ip, component_type):
        # 1. Wait Buffer
        time.sleep(self.retry_delay)

        # 2. Re-Ping
        if component_type == "INTERNET":
            results = NetworkTools.scan_hosts([target_ip, self.secondary_dns])
            primary_ok = target_ip in results
            secondary_ok = self.secondary_dns in results
            if not primary_ok and not secondary_ok:
                return True
            else:
                return False
        else:
            results = NetworkTools.scan_hosts([target_ip])
            if target_ip not in results:
                return True
            else:
                return False

    def _process_component(self, name, is_online, down_start_time):
        now = datetime.now()
        if not is_online and down_start_time is None:
            AppLogger.log(f"ALERT: {name} DOWN | Timer Started")
            return now
        elif is_online and down_start_time is not None:
            duration = now - down_start_time
            duration_str = str(duration).split('.')[0]
            AppLogger.log(f"RECOVERY: {name} Restored | Duration: {duration_str}")
            EventLogger.log_resolution(down_start_time, now, f"{name}_DOWN")
            img_data, _ = self.camera.capture_to_memory()
            self.notifier.send_outage_report(
                duration_str, f"{name}_DOWN", self.current_client_count,
                down_start_time, now, screenshot_data=img_data
            )
            return None
        return down_start_time

    def start_monitoring(self):
        AppLogger.log("DAEMON: Monitoring Active")

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
                # 0. Check for Config Changes
                self.check_hot_reload()

                # --- REORDERED: STEP 1 INFRASTRUCTURE SCAN ---
                # We must check Infrastructure FIRST to decide if we can trust the PC scan.

                # RE-READ targets in case config changed
                targets = self.config.get('targets', {})
                router_ip = targets.get('router', '192.168.1.1')
                server_ip = targets.get('server', '192.168.1.200')
                internet_ip = targets.get('internet', '8.8.8.8')

                infra_status = NetworkTools.scan_hosts([router_ip, server_ip, internet_ip])

                router_ok = router_ip in infra_status
                server_ok = server_ip in infra_status
                internet_raw_ok = internet_ip in infra_status

                # --- VERIFICATION LOGIC (Moved Up) ---
                if not router_ok:
                    if not self._verify_component(router_ip, "ROUTER"): router_ok = True

                if not server_ok:
                    if not self._verify_component(server_ip, "SERVER"): server_ok = True

                internet_ok = False
                if not router_ok:
                    # Cascading Logic: If Router is down, Internet is unreachable (but not necessarily down)
                    # We treat it as "False" for the GUI, but incident logic handles the alert.
                    internet_ok = False
                else:
                    if not internet_raw_ok:
                        if not self._verify_component(internet_ip, "INTERNET"): internet_ok = True
                    else:
                        internet_ok = True

                # --- STEP 2: CLIENT SCAN (With Freeze Logic) ---
                if router_ok:
                    # Safe to scan PCs
                    online_clients = NetworkTools.scan_hosts(self.pc_list)
                    self.current_client_count = len(online_clients)

                    # Update GUI Grid
                    gui_client_data = []
                    for i, ip in enumerate(self.pc_list):
                        is_alive = ip in online_clients
                        gui_client_data.append({"name": f"PC-{i + 1}", "ip": ip, "is_alive": is_alive})
                    self.sig_pc_update.emit(gui_client_data)

                    # Update Session Manager (Occupancy Report)
                    self.session_manager.process_scan(online_clients, self.pc_list)
                else:
                    # Router is DOWN.
                    # Freeze Logic: Do not scan PCs. Do not update Session Manager.
                    # This prevents "False Mass Log-offs" in the Occupancy Report.
                    # We do NOT emit sig_pc_update, so the GUI/Tray simply freezes at last state.
                    pass

                # --- STEP 3: INCIDENT LOGIC ---
                self.router_down_start = self._process_component("ROUTER", router_ok, self.router_down_start)
                self.server_down_start = self._process_component("SERVER", server_ok, self.server_down_start)

                if router_ok:
                    self.isp_down_start = self._process_component("ISP", internet_ok, self.isp_down_start)

                # --- STEP 4: UPDATE INFRA GUI ---
                self.sig_status_update.emit(timestamp, router_ok, server_ok, internet_ok)

                # --- STEP 5: ROUTINE SCREENSHOT ---
                self.handle_routine_screenshot()

            except Exception as e:
                AppLogger.log(f"EXCEPT: {e}")

            elapsed = time.time() - loop_start
            # Update interval dynamically too
            monitor_settings = self.config.get('monitor_settings', {})
            interval = monitor_settings.get('interval_seconds', 2)

            sleep_time = max(0.1, interval - elapsed)
            time.sleep(sleep_time)