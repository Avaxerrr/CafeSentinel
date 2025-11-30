import json
import time
import os
from datetime import datetime
from PySide6.QtCore import QObject, Signal, Slot

# PRESREVED YOUR EXACT IMPORTS
from models.network_tools import NetworkTools
from models.event_logger import EventLogger
from models.discord_notifier import DiscordNotifier
from models.screen_capture import ScreenCapture
from models.app_logger import AppLogger
from models.session_manager import SessionManager
from models.config_manager import ConfigManager  # SINGLETON IMPORT


class SentinelWorker(QObject):
    sig_status_update = Signal(str, bool, bool, bool)
    sig_pc_update = Signal(list)

    def __init__(self):
        super().__init__()
        self.running = True
        self.privacy_mode = False

        AppLogger.log("SYS_INIT: Kernel thread attached (Singleton Mode).")

        # GET SINGLETON INSTANCE (Phase 1 Change)
        self.cfg_mgr = ConfigManager.instance()

        # LOAD INITIAL CONFIG FROM MEMORY
        self.config = self.cfg_mgr.get_config()

        # CONNECT SIGNAL for Hot-Reload
        # This replaces the old "check file timestamp" logic
        self.cfg_mgr.sig_config_changed.connect(self.on_config_updated)

        # Init Variables
        self.current_client_count = 0

        # Incidents
        self.router_down_start = None
        self.server_down_start = None
        self.isp_down_start = None

        # Submodules
        self.notifier = DiscordNotifier(self.config)
        self.camera = ScreenCapture(self.config)
        self.session_manager = SessionManager(self.config, self.notifier)

        # Settings
        self.last_screenshot_time = datetime.now()
        self._update_settings()
        self.pc_list = self.generate_pc_list()

    @Slot(dict)
    def on_config_updated(self, new_config):
        """Triggered automatically when ConfigManager emits change signal."""
        AppLogger.log("CFG_WATCH: Signal received. Updating Sentinel...")

        # Update Config Object
        self.config = new_config

        # Update Modules
        self.notifier.update_config(self.config)
        self.session_manager.update_config(self.config)
        self.camera = ScreenCapture(self.config)  # Re-init camera

        # Update Locals
        self._update_settings()
        self.pc_list = self.generate_pc_list()

        AppLogger.log("CFG_WATCH: Hot Reload Complete.")

    def _update_settings(self):
        """Central place to update local vars from config."""
        # Screenshot
        self.screenshot_interval = self.config.get('screenshot_settings', {}).get('interval_minutes', 60)

        # Verification
        verify = self.config.get('verification_settings', {})
        self.retry_delay = verify.get('retry_delay_seconds', 1.0)
        self.secondary_dns = verify.get('secondary_target', '1.1.1.1')

        # Load minimum duration
        self.min_incident_duration = verify.get('min_incident_duration_seconds', 0)

        # Targets
        targets = self.config.get('targets', {})
        self.target_router = targets.get('router')
        self.target_server = targets.get('server')
        self.target_internet = targets.get('internet')

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
            duration_seconds = duration.total_seconds()
            duration_str = str(duration).split('.')[0]

            # Hysteresis Check
            if duration_seconds < self.min_incident_duration:
                AppLogger.log(f"IGNORE: {name} glitch detected ({duration_seconds:.1f}s) - Suppressed.")
                return None

            # Real incident recovery
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

        while self.running:
            loop_start = time.time()
            timestamp = datetime.now().strftime("%H:%M:%S")

            try:

                # FG_WATCH: Dirty flag checking
                dirty_status = self.cfg_mgr.check_and_clear_dirty()
                if dirty_status:
                    AppLogger.log("CFG_WATCH: Dirty flag detected! Reloading...")
                    new_config = self.cfg_mgr.get_config()
                    self.on_config_updated(new_config)

                # 1. Get Targets (Clean, no hardcoding)
                targets = self.config.get('targets', {})
                router_ip = targets.get('router')
                server_ip = targets.get('server')
                internet_ip = targets.get('internet')

                # SAFETY CHECK
                if not router_ip or not server_ip or not internet_ip:
                    AppLogger.log("WARN: Targets missing in config. Check Settings.")
                    time.sleep(5)
                    continue

                # 2. Infrastructure Scan
                infra_status = NetworkTools.scan_hosts([router_ip, server_ip, internet_ip])
                router_ok = router_ip in infra_status
                server_ok = server_ip in infra_status
                internet_raw_ok = internet_ip in infra_status

                # 3. Verification
                if not router_ok:
                    if not self._verify_component(router_ip, "ROUTER"): router_ok = True
                if not server_ok:
                    if not self._verify_component(server_ip, "SERVER"): server_ok = True

                internet_ok = False
                if not router_ok:
                    internet_ok = False  # Cascade
                else:
                    if not internet_raw_ok:
                        if not self._verify_component(internet_ip, "INTERNET"): internet_ok = True
                    else:
                        internet_ok = True

                # 4. Client Scan
                if router_ok:
                    online_clients = NetworkTools.scan_hosts(self.pc_list)
                    self.current_client_count = len(online_clients)

                    gui_client_data = []
                    for i, ip in enumerate(self.pc_list):
                        is_alive = ip in online_clients
                        gui_client_data.append({"name": f"PC-{i + 1}", "ip": ip, "is_alive": is_alive})
                    self.sig_pc_update.emit(gui_client_data)

                    self.session_manager.process_scan(online_clients, self.pc_list)
                else:
                    # Router Down = Freeze Client State
                    pass

                # 5. Incident Logic
                self.router_down_start = self._process_component("ROUTER", router_ok, self.router_down_start)
                self.server_down_start = self._process_component("SERVER", server_ok, self.server_down_start)
                if router_ok:
                    self.isp_down_start = self._process_component("ISP", internet_ok, self.isp_down_start)

                # 6. Update GUI
                self.sig_status_update.emit(timestamp, router_ok, server_ok, internet_ok)

                # 7. Routine Task
                self.handle_routine_screenshot()

            except Exception as e:
                AppLogger.log(f"EXCEPT: {e}")

            elapsed = time.time() - loop_start
            interval = self.config.get('monitor_settings', {}).get('interval_seconds', 2)
            sleep_time = max(0.1, interval - elapsed)
            time.sleep(sleep_time)