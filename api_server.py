import json
import os
import shutil
from datetime import datetime
from threading import Lock
from flask import Flask, request, jsonify
from flask_cors import CORS
from models.app_logger import AppLogger

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Thread-safe file access
config_lock = Lock()


class ConfigAPI:
    """Handles config.json operations via REST API"""

    def __init__(self, config_path='config.json'):
        self.config_path = config_path
        self.backup_dir = 'config_backups'
        self._ensure_backup_dir()

    def _ensure_backup_dir(self):
        """Create backup directory if it doesn't exist"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def _backup_config(self):
        """Create timestamped backup before making changes"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f'config_backup_{timestamp}.json')
            shutil.copy(self.config_path, backup_path)
            AppLogger.log(f"Config backed up to {backup_path}")

            # Keep only last 10 backups
            self._cleanup_old_backups()
        except Exception as e:
            AppLogger.log(f"Backup failed: {e}")

    def _cleanup_old_backups(self):
        """Keep only the 10 most recent backups"""
        try:
            backups = sorted([
                os.path.join(self.backup_dir, f)
                for f in os.listdir(self.backup_dir)
                if f.startswith('config_backup_')
            ])

            # Remove oldest backups if more than 10
            while len(backups) > 10:
                os.remove(backups[0])
                backups.pop(0)
        except Exception as e:
            AppLogger.log(f"Backup cleanup failed: {e}")

    def get_config(self):
        """Read and return current config.json"""
        with config_lock:
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                AppLogger.log(f"Failed to read config: {e}")
                return None

    def update_config(self, new_config):
        """Update config.json with validation"""
        with config_lock:
            try:
                # Validate config structure
                if not self._validate_config(new_config):
                    return False, "Invalid config structure"

                # Backup current config
                self._backup_config()

                # Write new config
                with open(self.config_path, 'w') as f:
                    json.dump(new_config, f, indent=4)

                AppLogger.log("Config updated via API")
                return True, "Config updated successfully"

            except Exception as e:
                AppLogger.log(f"Failed to update config: {e}")
                return False, str(e)

    def _validate_config(self, config):
        """Validate config has required structure"""
        required_keys = [
            'targets',
            'monitor_settings',
            'screenshot_settings',
            'discord_settings',
            'verification_settings',
            'occupancy_settings'
        ]

        # Check all required keys exist
        for key in required_keys:
            if key not in config:
                AppLogger.log(f"Validation failed: Missing key '{key}'")
                return False

        # Validate screenshot_settings
        screenshot = config.get('screenshot_settings', {})
        if 'interval_minutes' in screenshot:
            if not (1 <= screenshot['interval_minutes'] <= 1440):  # 1 min to 24 hours
                AppLogger.log("Validation failed: Invalid screenshot interval")
                return False

        if 'quality' in screenshot:
            if not (1 <= screenshot['quality'] <= 100):
                AppLogger.log("Validation failed: Invalid screenshot quality")
                return False

        # Validate monitor_settings
        monitor = config.get('monitor_settings', {})
        if 'interval_seconds' in monitor:
            if not (1 <= monitor['interval_seconds'] <= 60):
                AppLogger.log("Validation failed: Invalid monitor interval")
                return False

        return True


# Initialize API handler
config_api = ConfigAPI()


# ============= API ENDPOINTS =============

@app.route('/api/status', methods=['GET'])
def api_status():
    """Check if API is alive"""
    return jsonify({
        "status": "online",
        "service": "CafeSentinel Config API",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    config = config_api.get_config()
    if config:
        return jsonify({
            "status": "success",
            "config": config
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Failed to read config"
        }), 500


@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration"""
    try:
        new_config = request.json

        if not new_config:
            return jsonify({
                "status": "error",
                "message": "No config data provided"
            }), 400

        success, message = config_api.update_config(new_config)

        if success:
            return jsonify({
                "status": "success",
                "message": message
            })
        else:
            return jsonify({
                "status": "error",
                "message": message
            }), 400

    except Exception as e:
        AppLogger.log(f"API error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/config/backups', methods=['GET'])
def list_backups():
    """List available config backups"""
    try:
        backups = sorted([
            f for f in os.listdir(config_api.backup_dir)
            if f.startswith('config_backup_')
        ], reverse=True)

        return jsonify({
            "status": "success",
            "backups": backups
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500


def run_api_server(host='0.0.0.0', port=5000):
    """Start Flask API server"""
    try:
        AppLogger.log(f"Starting Config API on {host}:{port}")
        app.run(host=host, port=port, debug=False, threaded=True)
    except Exception as e:
        AppLogger.log(f"API server failed: {e}")


if __name__ == '__main__':
    # For testing standalone
    run_api_server()
