import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from models.app_logger import AppLogger
from models.config_manager import ConfigManager

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Initialize Singleton Manager
cfg_mgr = ConfigManager.instance()

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
    config = cfg_mgr.get_config()
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

        # Hand off to Singleton Manager
        # NOTE: The validation logic (check required keys) is now handled
        # inside ConfigManager.update_config()
        success, message = cfg_mgr.update_config(new_config)

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
        # Helper from ConfigManager
        backups = cfg_mgr.get_backup_list()
        return jsonify({
            "status": "success",
            "backups": backups
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/logs', methods=['GET'])
def get_logs():
    """
    Returns recent logs from memory buffer.
    Query param: ?lines=500 (optional, default 500)
    """
    try:
        # Get optional line count from query param
        line_count = request.args.get('lines', default=500, type=int)

        # Clamp to reasonable range (prevent abuse)
        line_count = max(10, min(line_count, 1000))

        logs = AppLogger.get_recent_logs(line_count)

        return jsonify({
            "status": "success",
            "lines": len(logs),
            "logs": logs
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
    run_api_server()