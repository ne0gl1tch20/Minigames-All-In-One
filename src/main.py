# main.py
"""
The minimal entry point for the MGAIO Launcher application.
Initializes the QApplication, performs app lock check, and runs the main window.
"""

import sys
import traceback
import os

# PySide6 imports
from PySide6.QtWidgets import QApplication, QMessageBox

# Project imports
from scripts.managers.settings_manager import settings
from scripts.utils.security import app_lock
from scripts.gui.launcher_window import Launcher


if __name__ == '__main__':
    
    print(f"--- MGAIO Launcher Starting --- PID: {os.getpid()}")
    
    # 1. Initialize QApplication
    try:
        app = QApplication(sys.argv)
        app.setApplicationName('MGAIO Launcher')
    except Exception as e:
        print("Error initializing QApplication:", e)
        sys.exit(1)

    # 2. Apply App Lock if enabled
    try:
        if settings.get('lock_on_startup', False):
            # Pass exit_on_cancel=True so closing the lock dialog exits the app
            app_lock(exit_on_cancel=True)
        print("App Lock passed.")
    except Exception as e:
        print("Error during app lock:", e)
        traceback.print_exc()
        sys.exit(1)


    # 3. Initialize and Run Launcher
    try:
        launcher = Launcher()
        print("Launcher made successfully.")
            
        launcher.show()
        
        print("Entering QApplication event loop...")
        sys.exit(app.exec())
        
    except Exception as e:
        print('Fatal error in main:', e)
        traceback.print_exc()
        try:
            QMessageBox.critical(None, 'Fatal Error', f'Launcher crashed: {e}')
        except Exception:
            pass
        sys.exit(1)