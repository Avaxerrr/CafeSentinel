import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from models.app_logger import AppLogger
from models.config_manager import ConfigManager

app = Flask(__name__)
CORS(app)

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
    Returns TODAY's logs from memory buffer (real-time).
    Query param: ?lines=500 (optional, default 500)
    """
    try:
        line_count = request.args.get('lines', default=500, type=int)
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


@app.route('/api/logs/archive', methods=['GET'])
def list_archived_logs():
    """
    ⭐ NEW: Lists all archived log files in probes/ folder.
    Returns filenames sorted newest first.
    """
    try:
        archives = AppLogger.get_archive_list()
        return jsonify({
            "status": "success",
            "count": len(archives),
            "archives": archives
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/logs/archive/<filename>', methods=['GET'])
def get_archived_log(filename):
    """
    ⭐ NEW: Returns the contents of a specific archived log.
    Example: GET /api/logs/archive/info-2025-11-30.log
    """
    try:
        logs = AppLogger.get_archived_log(filename)

        if logs is None:
            return jsonify({
                "status": "error",
                "message": "Archive file not found"
            }), 404

        return jsonify({
            "status": "success",
            "filename": filename,
            "lines": len(logs),
            "logs": logs
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/logs/archive/<filename>', methods=['DELETE'])
def delete_archived_log(filename):
    """
    Permanently deletes an archived log file.
    No recycle bin - file is destroyed immediately.
    Example: DELETE /api/logs/archive/info-2025-11-28.log
    """
    try:
        # Security: Only allow deletion of archive files, not other system files
        if not filename.startswith("info-") or not filename.endswith(".log"):
            return jsonify({
                "status": "error",
                "message": "Invalid filename format"
            }), 400

        archive_path = AppLogger._get_archive_path()
        file_path = os.path.join(archive_path, filename)

        # Security: Prevent path traversal attacks
        if not os.path.abspath(file_path).startswith(os.path.abspath(archive_path)):
            return jsonify({
                "status": "error",
                "message": "Access denied"
            }), 403

        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({
                "status": "error",
                "message": "Archive file not found"
            }), 404

        # PERMANENT DELETION (no recycle bin)
        os.remove(file_path)

        AppLogger.log(f"ARCHIVE: Purged log file via API")  # Don't log filename (security)

        return jsonify({
            "status": "success",
            "message": "Archive deleted permanently"
        })

    except PermissionError:
        return jsonify({
            "status": "error",
            "message": "Permission denied - file may be in use"
        }), 403
    except Exception as e:
        AppLogger.log(f"ARCHIVE: Deletion failed - {type(e).__name__}")  # Log error type, not details
        return jsonify({
            "status": "error",
            "message": "Deletion failed"
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