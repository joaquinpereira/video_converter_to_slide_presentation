import os
import json
from PyQt6.QtWidgets import QApplication

class ThemeManager:
    CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".video_slide_maker_config.json")
    THEMES_DIR = os.path.join(os.path.dirname(__file__), "themes")

    @classmethod
    def get_available_themes(cls):
        return {
            "Light Modern": "light_modern.qss",
            "Light +": "light_plus.qss",
            "Quiet Light": "quiet_light.qss",
            "Solarized Light": "solarized_light.qss",
            "Tokio Night Light": "tokyo_night_light.qss",
            "Dark Modern": "dark_modern.qss",
            "Dark +": "dark_plus.qss",
            "Kimbie Dark": "kimbie_dark.qss",
            "Monokai": "monokai.qss",
            "Solarized Dark": "solarized_dark.qss",
            "Tokio Night Dark": "tokyo_night_dark.qss",
            "Red": "red.qss"
        }

    @classmethod
    def get_current_theme_name(cls):
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("theme", "Dark Modern")
            except:
                pass
        return "Dark Modern"

    @classmethod
    def apply_theme(cls, app: QApplication, theme_name: str, save: bool = True):
        themes = cls.get_available_themes()
        if theme_name not in themes:
            theme_name = "Dark Modern"
            
        qss_file = os.path.join(cls.THEMES_DIR, themes[theme_name])
        
        if os.path.exists(qss_file):
            with open(qss_file, 'r', encoding='utf-8') as f:
                app.setStyleSheet(f.read())
                
        if save:
            cls.save_theme_preference(theme_name)

    @classmethod
    def save_theme_preference(cls, theme_name: str):
        try:
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump({"theme": theme_name}, f)
        except:
            pass
