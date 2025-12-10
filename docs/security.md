# Security System

## Encryption Architecture

All sensitive data encrypted using Fernet symmetric encryption from cryptography library.

**Machine-Specific Key Generation:**
- SecurityManager generates key from hardware fingerprint
- Uses motherboard serial number and processor ID (Windows WMI)
- SHA-256 hash converted to base64 for Fernet compatibility
- Key never stored on disk, regenerated on each application start
- Config encrypted on one machine cannot be decrypted on another

**File Disguising Strategy:**
- Configuration: `cscf.dll` (not `config.json`)
- Password vault: `cron.dll` (not `passwords.json`)
- Backups: `backup_TIMESTAMP.cscf.dll` 
- Appears as system library files to casual inspection
- Prevents easy identification of sensitive data

## Password Management

### SecurityManager (models/security_manager.py)

Manages two password types stored in encrypted vault file `cron.dll`.

**Password Types:**
- Admin Password: Required for application exit and settings access
- Privacy Password: Required to toggle screenshot capture mode

**Vault Structure:**
- Single encrypted file containing both passwords
- Fernet encryption with machine-specific key
- Created during first-run setup wizard
- Passwords stored as bcrypt hashes (not plaintext)

**First-Run Setup:**
- Application detects missing `cron.dll` vault file
- Displays setup wizard requiring both passwords
- Validates password strength (minimum length, confirmation match)
- Creates encrypted vault with hashed passwords
- Application cannot start without completing setup

**Password Verification Flow:**
1. User enters password in dialog
2. SecurityManager loads and decrypts vault
3. Compares input against stored bcrypt hash
4. Returns boolean verification result
5. Application grants or denies access

## Log Sanitization

All log messages sanitized to prevent information disclosure.

**Sanitization Rules:**
- Never log file paths or filenames
- Use generic category labels: SYSTEM, CONFIG, NETWORK, etc.
- Error messages omit exception details that reveal structure
- Success messages confirm action without specifics
- Example: "[CONFIG] Updated successfully" not "[CONFIG] Saved to cscf.dll"

**Purpose:**
- Prevents attackers from identifying critical files
- Obscures application architecture from log analysis
- Reduces attack surface by limiting exposed information

## Admin Requirements

- Application requires administrator privileges to run
- Required for raw ICMP socket creation (network monitoring)
- Self-elevates on startup if not running as admin
- Watchdog service also runs with elevated privileges
- API server inherits admin privileges from main process
