# scripts/core/achievements.py
"""
Logic for checking and unlocking achievements, and awarding coins.
"""

import time

# PySide6 imports for notification
from PySide6.QtWidgets import QMessageBox

from ..utils.constants import ACHIEVEMENTS_DEF
from ..managers.settings_manager import settings, save_settings

def check_unlock_achievement(aid: str, custom_coins: int = 0):
    """
    Checks if an achievement should be unlocked.
    Unlocks it, awards coins, and notifies the user if successful.
    """
    if aid not in ACHIEVEMENTS_DEF:
        return

    ach = settings.setdefault('achievements', {})
    if aid in ach:
        return  # already unlocked

    # unlock
    ach[aid] = int(time.time())
    settings['achievements'] = ach

    # award coins if defined
    coin_award = ACHIEVEMENTS_DEF.get(aid, {}).get('coins', 0)
    if custom_coins > 0:
        coin_award = custom_coins

    if coin_award and settings.get('mini_rewards', True):
        settings['coins'] = settings.get('coins', 0) + coin_award
        
    save_settings()

    # notify user
    if settings.get('notifications', True):
        try:
            QMessageBox.information(None, 'Achievement Unlocked!',
                                    f"{ACHIEVEMENTS_DEF[aid]['name']}\n{ACHIEVEMENTS_DEF[aid]['desc']}\n+{coin_award} coins")
        except Exception as e:
            print(f'Failed to show achievement notification: {e}')