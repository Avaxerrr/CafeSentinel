import json
import requests
from datetime import datetime


class DiscordNotifier:
    def __init__(self, config):
        self.config = config.get('discord_settings', {})
        self.enabled = self.config.get('enabled', False)

        # Load all 3 Webhooks
        self.alerts_url = self.config.get('webhook_alerts', '')
        self.occupancy_url = self.config.get('webhook_occupancy', '')
        self.screenshots_url = self.config.get('webhook_screenshots', '')  # <--- NEW

        self.shop_name = self.config.get('shop_name', 'Internet Cafe')

    def _send_payload(self, url, payload, file_buffer=None, filename=None):
        """Generic sender"""
        if not self.enabled or not url or "YOUR_" in url:
            return

        try:
            data = {'payload_json': json.dumps(payload)}
            files = None
            if file_buffer:
                files = {'file': (filename, file_buffer, 'image/webp')}

            requests.post(url, data=data, files=files, timeout=10)
        except Exception as e:
            print(f"❌ Discord Send Error: {e}")

    def send_screenshot_log(self, title, description, color, image_data):
        """Sends ONLY the image to the #screenshots channel"""
        if not image_data or not self.screenshots_url:
            return

        embed = {
            "title": f"📸 {title}",
            "description": description,
            "color": color,
            "image": {"url": "attachment://screenshot.webp"},
            "footer": {"text": "Visual Log • " + self.shop_name}
        }

        # Unpack image data
        buffer = image_data[0]
        fname = image_data[1]

        self._send_payload(self.screenshots_url, {"embeds": [embed]}, buffer, fname)

    def send_outage_report(self, duration_str, cause, client_count, start_time, end_time, screenshot_data=None):
        color = 15158332  # Red

        # 1. Send Text Report to #ALERTS
        embed = {
            "title": "🚨 SERVICE RESTORED",
            "description": f"**{self.shop_name}** is back online.",
            "color": color,
            "fields": [
                {"name": "Duration", "value": duration_str, "inline": True},
                {"name": "Cause", "value": cause, "inline": True},
                {"name": "Impact", "value": f"**{client_count} Active Clients** affected", "inline": False},
                {"name": "Timeframe", "value": f"{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}",
                 "inline": False}
            ],
            "footer": {"text": "Cafe Sentinel • Automated Report"}
        }

        # Note: No image passed here
        self._send_payload(self.alerts_url, {"embeds": [embed]})

        # 2. Send Image to #SCREENSHOTS (if available)
        if screenshot_data:
            desc = f"Context for Outage: {start_time.strftime('%I:%M %p')}"
            self.send_screenshot_log("Outage Context", desc, color, screenshot_data)

    def send_hourly_occupancy(self, active_count, total_count, screenshot_data=None):
        color = 3066993  # Green
        percent = int((active_count / total_count) * 100) if total_count > 0 else 0

        # 1. Send Text Report to #OCCUPANCY
        embed = {
            "title": "📊 Hourly Occupancy Report",
            "color": color,
            "fields": [
                {"name": "Active Clients", "value": f"{active_count} / {total_count}", "inline": True},
                {"name": "Utilization", "value": f"{percent}%", "inline": True}
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "Cafe Sentinel • Hourly Check"}
        }

        # Note: No image passed here
        self._send_payload(self.occupancy_url, {"embeds": [embed]})

        # 2. Send Image to #SCREENSHOTS (if available)
        if screenshot_data:
            desc = f"Routine Check: {active_count}/{total_count} Clients Active"
            self.send_screenshot_log("Hourly Visual Check", desc, color, screenshot_data)
