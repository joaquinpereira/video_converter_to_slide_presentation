import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from model import AppModel
from views.main_view import MainView
from views.extractor_view import ExtractorView
from views.slideshow_view import SlideshowView
from views.summary_view import SummaryView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video to Slide Maker")
        self.setMinimumSize(900, 650)
        self.resize(1100, 750)
        
        # Modelo que almacena el estado de toda la app
        self.model = AppModel()
        
        # Gestor de pantallas (Vistas)
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Instanciar las vistas
        self.main_view = MainView(self.model)
        self.extractor_view = ExtractorView(self.model)
        self.slideshow_view = SlideshowView(self.model)
        self.summary_view = SummaryView(self.model)
        
        # Agregar al stack
        self.stacked_widget.addWidget(self.main_view)
        self.stacked_widget.addWidget(self.extractor_view)
        self.stacked_widget.addWidget(self.slideshow_view)
        self.stacked_widget.addWidget(self.summary_view)
        
        # Conectar señales (Navegación)
        self.main_view.next_requested.connect(self.go_to_extractor)
        self.extractor_view.next_requested.connect(self.go_to_slideshow)
        self.slideshow_view.next_requested.connect(self.go_to_summary)
        
        self.slideshow_view.back_requested.connect(self.go_to_extractor)
        self.summary_view.back_requested.connect(self.go_to_slideshow)
        
        # Estilos globales (Modernos y limpios)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5;
                color: #2c3e50;
            }
            QLabel, QCheckBox {
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #2c3e50;
            }
            QLineEdit, QDoubleSpinBox {
                padding: 10px;
                border: 1px solid #cfd8dc;
                border-radius: 6px;
                background-color: #ffffff;
                color: #2c3e50;
            }
            QLineEdit:focus, QDoubleSpinBox:focus {
                border: 1px solid #2196F3;
            }
            QPushButton {
                padding: 10px 15px;
                border: none;
                border-radius: 6px;
                background-color: #2196F3;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover:!disabled {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #b0bec5;
            }
            QComboBox {
                padding: 5px;
                border: 1px solid #cfd8dc;
                border-radius: 4px;
                color: #2c3e50;
                background-color: white;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #2c3e50;
                selection-background-color: #2196F3;
                selection-color: white;
            }
            QMessageBox {
                background-color: #ffffff;
            }
            QMessageBox QLabel {
                color: #2c3e50;
            }
            QMessageBox QPushButton {
                background-color: #2196F3;
                color: white;
                min-width: 80px;
                padding: 5px 15px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #90a4ae;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #2196F3;
                border: 2px solid #2196F3;
            }
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #cfd8dc;
                border-radius: 8px;
                color: #2c3e50;
                outline: none;
            }
            QListWidget::item {
                color: #2c3e50;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                border: 2px solid #2196F3;
                border-radius: 5px;
                color: #2c3e50;
            }
        """)

    def go_to_extractor(self):
        # Cargar video antes de cambiar de pantalla
        self.extractor_view.load_video()
        self.stacked_widget.setCurrentWidget(self.extractor_view)

    def go_to_slideshow(self):
        # Cargar imágenes capturadas en la galería
        self.slideshow_view.load_images()
        self.stacked_widget.setCurrentWidget(self.slideshow_view)

    def go_to_summary(self):
        self.summary_view.load_summary()
        self.stacked_widget.setCurrentWidget(self.summary_view)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
