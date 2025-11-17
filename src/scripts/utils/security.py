# scripts/utils/security.py
"""
Handles password hashing, strength checking, app lock logic (lockout, attempts),
and AES-based JSON encryption/decryption.
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
import secrets
from typing import Tuple, Union, Dict

from Crypto.Cipher import AES
from PySide6.QtWidgets import QMessageBox, QInputDialog, QLineEdit

from ..managers.settings_manager import settings, save_settings


# ---------- Password Hashing ----------
def hash_password(password: str, salt: bytes = None) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a random salt."""
    salt = salt or secrets.token_bytes(16)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 200_000)
    return f"{binascii.hexlify(salt).decode()}:{binascii.hexlify(pwdhash).decode()}"


def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a password using timing-safe comparison."""
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
def password_strength(password: str) -> Tuple[str, int]:
    """Assess password strength and return a rating and score (0-5)."""
    if not password:
        return "Empty", 0

    score = 0
    if len(password) >= 8:
        score += 1
    if re.search(r'\d', password):
        score += 1
    if re.search(r'[A-Z]', password):
        score += 1
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    if not re.search(r'(0123|1234|2345|3456|4567|5678|6789|7890|9876|8765|7654|6543|5432|4321|3210|0987)', password):
        score += 1  # bonus for no simple sequences

    if password.isdigit():
        if len(password) == 4:
            return "Fair (PIN)", 2
        elif len(password) >= 6:
            return "Good (PIN)", 3

    rating = ["Weak", "Fair", "Good", "Strong", "Very Strong", "Excellent"]
    return rating[min(score, 5)], score


# ---------- Encryption/Decryption ----------
def encrypt_json(data: Dict, password: str) -> str:
    """Encrypt a JSON object using AES-EAX mode."""
    try:
        raw = json.dumps(data).encode('utf-8')
        key = hashlib.sha256(password.encode('utf-8')).digest()  # stronger key derivation
        cipher = AES.new(key, AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(raw)
        return base64.b64encode(cipher.nonce + tag + ciphertext).decode('utf-8')
    except Exception as e:
        raise RuntimeError(f"Encryption failed: {e}")


def decrypt_json(enc_text: str, password: str) -> Dict:
    """Decrypt an AES-EAX encrypted JSON string."""
    try:
        data = base64.b64decode(enc_text)
        key = hashlib.sha256(password.encode('utf-8')).digest()
        nonce, tag, ciphertext = data[:16], data[16:32], data[32:]
        cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
        raw = cipher.decrypt_and_verify(ciphertext, tag)
        return json.loads(raw)
    except Exception as e:
        raise RuntimeError(f"Decryption failed: {e}")


# ---------- Lockout Logic ----------
def check_lockout() -> bool:
    """Return True if app is locked and display remaining lockout time."""
    now = int(time.time())
    lock_until = settings.get('lockout_until', 0)
    if lock_until > now:
        remaining = lock_until - now
        QMessageBox.warning(None, "Locked Out",
                            f"Too many wrong attempts! Try again in {remaining} seconds.")
        return True
    return False


def handle_failed_attempt():
    """Increment failed attempts and enforce lockout if needed."""
    now = int(time.time())
    max_attempts = settings.get('max_attempts', 5)
    base_lockout = settings.get('lockout_duration', 60)

    failed = settings.get('failed_attempts', 0) + 1
    settings['failed_attempts'] = failed

    remaining = max_attempts - failed
    if remaining <= 0:
        settings['lockout_until'] = now + base_lockout
        settings['failed_attempts'] = 0
        QMessageBox.warning(None, "Locked Out",
                            f"Too many wrong attempts! Locked for {base_lockout} seconds.")
    else:
        QMessageBox.critical(None, "Access Denied", f"Wrong password! {remaining} tries left.")

    save_settings()


# ---------- Main App Lock ----------
def app_lock(exit_on_cancel: bool = True):
    """Lock the app until correct password is entered."""
    stored_hash = settings.get('lock_password')
    if not stored_hash or not settings.get('lock_on_startup', False):
        return

    if check_lockout() and exit_on_cancel:
        sys.exit(1)

    while True:
        text, ok = QInputDialog.getText(None, "App Lock", "Enter password/pin:", QLineEdit.Password)
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
