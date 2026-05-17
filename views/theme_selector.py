from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QLineEdit
from PyQt6.QtCore import Qt
from theme_manager import ThemeManager

class ThemeSelectorDialog(QDialog):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.original_theme = ThemeManager.get_current_theme_name()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Select Color Theme")
        self.resize(500, 300)
        # Forzamos estilo de VS Code en el selector, independientemente del tema de fondo
        self.setStyleSheet("""
            QDialog { background-color: #252526; border: 1px solid #454545; }
            QLineEdit { padding: 10px; font-size: 14px; background-color: #3c3c3c; color: #d4d4d4; border: 1px solid #007acc; }
            QListWidget { background-color: #252526; color: #d4d4d4; font-size: 14px; border: none; outline: none; }
            QListWidget::item { padding: 10px; }
            QListWidget::item:selected { background-color: #094771; color: white; }
        """)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Select Color Theme...")
        self.search_box.textChanged.connect(self.filter_themes)
        
        self.theme_list = QListWidget()
        themes = list(ThemeManager.get_available_themes().keys())
        self.theme_list.addItems(themes)
        self.theme_list.currentItemChanged.connect(self.preview_theme)
        self.theme_list.itemClicked.connect(self.accept_theme)
        
        items = self.theme_list.findItems(self.original_theme, Qt.MatchFlag.MatchExactly)
        if items:
            self.theme_list.setCurrentItem(items[0])
            
        layout.addWidget(self.search_box)
        layout.addWidget(self.theme_list)

    def filter_themes(self, text):
        for i in range(self.theme_list.count()):
            item = self.theme_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def preview_theme(self, current, previous):
        if current:
            ThemeManager.apply_theme(self.app, current.text(), save=False)

    def accept_theme(self, item):
        ThemeManager.apply_theme(self.app, item.text(), save=True)
        self.accept()

    def reject(self):
        ThemeManager.apply_theme(self.app, self.original_theme, save=False)
        super().reject()
