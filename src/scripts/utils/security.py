# scripts/utils/security.py
"""
Handles password hashing, strength checking, app lock logic (lockout, attempts),
and data encryption/decryption (AES for theme export).
"""

import re
import hashlib
import binascii
import os
import time
import sys
import hmac
import json
import base64
from Crypto.Cipher import AES

# PySide6 imports for GUI messages and input
from PySide6.QtWidgets import QMessageBox, QInputDialog, QLineEdit
from ..managers.settings_manager import settings, save_settings

# ---------- Password Hashing ----------
def hash_password(password, salt=None):
    """Hash a password using PBKDF2-SHA256 with a random salt."""
    if not salt:
        salt = os.urandom(16)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 200_000)
    return f"{binascii.hexlify(salt).decode()}:{binascii.hexlify(pwdhash).decode()}"

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided using timing-safe comparison."""
    if not stored_password:
        return False
    try:
        salt_hex, pwdhash_hex = stored_password.split(":")
        salt = binascii.unhexlify(salt_hex)
        new_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt, 200_000)
        return hmac.compare_digest(binascii.hexlify(new_hash).decode(), pwdhash_hex)
    except Exception:
        return False

# ---------- Password Strength ----------
def password_strength(pwd: str):
    """Rates password strength and returns a score."""
    if not pwd:
        return "Empty", 0
    score = 0
    if pwd.isdigit():
        if len(pwd) == 4:
            return "Fair (PIN)", 2
        elif len(pwd) >= 6:
            return "Good (PIN)", 3

    if len(pwd) >= 4:
        score += 1
    if re.search(r'\d', pwd):
        score += 1
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', pwd):
        score += 1
    sequences = ['0123','1234','2345','3456','4567','5678','6789','7890',
                 '9876','8765','7654','6543','5432','4321','3210','0987']
    if any(seq in pwd for seq in sequences):
        return "Weak (sequence)", score

    if score <= 1:
        return "Weak", score
    elif score == 2:
        return "Fair", score
    elif score == 3:
        return "Good", score
    elif score == 4:
        return "Strong", score
    else:
        return "Stronger", score

# ---------- Encryption/Decryption ----------
def encrypt_json(data: dict, password: str) -> str:
    """Encrypt JSON dict using AES with password."""
    raw = json.dumps(data).encode('utf-8')
    key = password.encode('utf-8').ljust(32, b'\0')[:32]  # 32-byte key
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(raw)
    return base64.b64encode(cipher.nonce + tag + ciphertext).decode('utf-8')

def decrypt_json(enc_text: str, password: str) -> dict:
    """Decrypt AES-encrypted JSON string."""
    data = base64.b64decode(enc_text)
    key = password.encode('utf-8').ljust(32, b'\0')[:32]
    nonce, tag, ciphertext = data[:16], data[16:32], data[32:]
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    raw = cipher.decrypt_and_verify(ciphertext, tag)
    return json.loads(raw)

# ---------- Lockout Logic ----------
def check_lockout():
    """Check if the app is currently locked and show remaining lockout time."""
    now = int(time.time())
    lock_until = settings.get('lockout_until', 0)
    if lock_until > now:
        remaining = lock_until - now
        QMessageBox.warning(None, "Locked Out",
                            f"Too many wrong attempts! Try again in {remaining} seconds.")
        return True
    return False

def handle_failed_attempt():
    """Handle a failed password attempt with exponential lockout."""
    now = int(time.time())
    max_attempts = settings.get('max_attempts', 5)
    base_lockout = settings.get('lockout_duration', 60)

    settings['failed_attempts'] = settings.get('failed_attempts', 0) + 1
    remaining_tries = max_attempts - settings['failed_attempts']

    if remaining_tries <= 0:
        settings['lockout_until'] = now + base_lockout
        settings['failed_attempts'] = 0
        QMessageBox.warning(None, "Locked Out",
                            f"Too many wrong attempts! Locked for {base_lockout} seconds.")
    else:
        QMessageBox.critical(None, 'Access Denied',
                             f"Wrong password! {remaining_tries} tries left.")
    save_settings()

# ---------- Main App Lock ----------
def app_lock(exit_on_cancel=True):
    """Main function to lock the app until correct password is entered."""
    stored_hash = settings.get('lock_password')
    if not stored_hash or not settings.get('lock_on_startup', False):
        return

    if check_lockout():
        if exit_on_cancel:
            sys.exit(1)
        return

    while True:
        text, ok = QInputDialog.getText(None, 'App Lock', 'Enter password/pin:', QLineEdit.Password)
        if not ok:
            if exit_on_cancel:
                sys.exit(1)
            return

        if verify_password(stored_hash, text):
            settings['failed_attempts'] = 0
            settings['lockout_until'] = 0
            save_settings()
            return
        else:
            handle_failed_attempt()
            if check_lockout() and exit_on_cancel:
                sys.exit(1)