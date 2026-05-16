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
        self.resize(800, 600)
        self.setMinimumSize(600, 400)
        
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
        
        # Estilos globales (Modernos y limpios)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QLabel {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #fafafa;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
            QPushButton {
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
                background-color: #2196F3;
                color: white;
            }
            QPushButton:hover {
                background-color: #1976D2;
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
