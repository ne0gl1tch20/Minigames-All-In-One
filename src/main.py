"""
Multi-platform entry point for the MGAIO Launcher application.
Uses psutil + system checks to detect Android (Pydroid 3) or Windows,
then loads the correct launcher UI. Supports FORCED_OS_SELECTION override.
"""

import sys
import traceback
import os
import platform
import psutil

# PySide6
from PySide6.QtWidgets import QApplication, QMessageBox

# Project imports
from scripts.managers.settings_manager import settings
from scripts.utils.security import app_lock


# ------------------------------------------------------------
# FORCED OS SELECTION
# ------------------------------------------------------------
# 0 = AUTO (detect automatically)
# 1 = ANDROID
# 2 = PC
FORCED_OS_SELECTION = 0  # <-- Change this to 1 or 2 to force OS


# ------------------------------------------------------------
# DEVICE / PLATFORM DETECTION (USING PSUTIL)
# ------------------------------------------------------------
def is_android_device():
    """
    Detects Android/Pydroid 3 using psutil + environment checks.
    More accurate than relying on sys.platform alone.
    """
    try:
        # 1. Pydroid 3 signature
        if "PYDROID3" in os.environ.get("PATH", ""):
            return True

        # 2. CPU Architecture (Android = ARM or AArch64)
        cpu_arch = platform.machine().lower()
        if "arm" in cpu_arch or "aarch64" in cpu_arch:
            # Confirm with battery API (Android always has battery)
            battery = psutil.sensors_battery()
            if battery is not None:
                return True

        # 3. Process path check (Android apps run within /data or /storage)
        for proc in psutil.process_iter(['exe', 'cmdline']):
            try:
                exe = proc.info.get("exe") or ""
                if exe.startswith("/data") or exe.startswith("/storage"):
                    return True
            except:
                pass

    except Exception:
        pass

    return False


def is_windows_device():
    """
    Detect Windows reliably.
    """
    return sys.platform.startswith("win")


# ------------------------------------------------------------
# IMPORT CORRECT LAUNCHER WITH FORCED_OS_SELECTION
# ------------------------------------------------------------
try:
    if FORCED_OS_SELECTION == 1:
        print("📱 Forced to Android → Loading Mobile Launcher")
        from scripts.gui.launcher_windowMobile import Launcher

    elif FORCED_OS_SELECTION == 2:
        print("🖥️ Forced to PC → Loading Desktop Launcher")
        from scripts.gui.launcher_window import Launcher

    else:  # AUTO
        if is_android_device():
            print("📱 Android device detected → Loading Mobile Launcher")
            from scripts.gui.launcher_windowMobile import Launcher

        elif is_windows_device():
            print("🖥️ Windows PC detected → Loading Desktop Launcher")
            from scripts.gui.launcher_window import Launcher

        else:
            print("🟦 Unknown device → Defaulting to Desktop Launcher")
            from scripts.gui.launcher_window import Launcher

except Exception as e:
    print("Error selecting launcher:", e)
    traceback.print_exc()
    sys.exit(1)


# ------------------------------------------------------------
# APP STARTUP
# ------------------------------------------------------------
if __name__ == '__main__':
    print(f"--- MGAIO Launcher Starting --- PID: {os.getpid()} ---")

    # 1. Init QApplication
    try:
        app = QApplication(sys.argv)
        app.setApplicationName('MGAIO Launcher')
    except Exception as e:
        print("Error initializing QApplication:", e)
        sys.exit(1)

    # 2. App Lock
    try:
        if settings.get('lock_on_startup', False):
            app_lock(exit_on_cancel=True)
        print("App Lock passed.")
    except Exception as e:
        print("Error during app lock:", e)
        traceback.print_exc()
        sys.exit(1)

    # 3. Initialize Launcher
    try:
        launcher = Launcher()
        print("Launcher loaded:", launcher.__class__.__name__)

        launcher.show()
        print("Entering QApplication event loop...")

        sys.exit(app.exec())

    except Exception as e:
        print("Fatal error:", e)
        traceback.print_exc()
        try:
            QMessageBox.critical(None, 'Fatal Error', f'Launcher crashed: {e}')
        except Exception:
            pass
        sys.exit(1)
