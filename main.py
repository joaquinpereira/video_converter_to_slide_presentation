import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction
from project_manager import ProjectManager

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
        
        # Auto-save timer
        self.autosave_timer = QTimer()
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.timeout.connect(self.perform_autosave)
        
        # Modelo global
        self.model = AppModel()
        
        self.setup_menu()

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Vistas
        self.main_view = MainView(self.model)
        self.extractor_view = ExtractorView(self.model)
        self.slideshow_view = SlideshowView(self.model)
        self.summary_view = SummaryView(self.model)
        
        self.stacked_widget.addWidget(self.main_view)
        self.stacked_widget.addWidget(self.extractor_view)
        self.stacked_widget.addWidget(self.slideshow_view)
        self.stacked_widget.addWidget(self.summary_view)
        
        # Conectar señales (Navegación)
        self.main_view.next_requested.connect(self.go_to_extractor)
        self.main_view.open_project_requested.connect(self.open_project)
        self.extractor_view.next_requested.connect(self.go_to_slideshow)
        self.slideshow_view.next_requested.connect(self.go_to_summary)
        
        self.slideshow_view.back_requested.connect(self.go_to_extractor)
        self.summary_view.back_requested.connect(self.go_to_slideshow)
        
        # Conectar señales de guardado
        self.extractor_view.data_changed.connect(self.trigger_autosave)
        self.slideshow_view.data_changed.connect(self.trigger_autosave)
        self.summary_view.data_changed.connect(self.trigger_autosave)
        
        # Estilos globales (Modernos y limpios)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5;
            }
            QLabel {
                color: #2c3e50;
            }
            QLineEdit {
                padding: 12px;
                border: 1px solid #cfd8dc;
                border-radius: 6px;
                background-color: white;
                color: #2c3e50;
                font-size: 14px;
            }
            QDoubleSpinBox {
                padding: 12px;
                border: 1px solid #cfd8dc;
                border-radius: 6px;
                background-color: white;
                color: #2c3e50;
                font-size: 14px;
            }
            QPushButton {
                border-radius: 6px;
                border: none;
                color: white;
            }
            QPushButton:disabled {
                background-color: #b0bec5;
            }
            QComboBox {
                padding: 12px;
                border: 1px solid #cfd8dc;
                border-radius: 6px;
                background-color: white;
                color: #2c3e50;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: 0px;
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
            QCheckBox {
                color: #2c3e50;
                font-size: 15px;
                font-weight: bold;
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
            }
            QListWidget::item {
                color: #2c3e50;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                border: 1px solid #2196F3;
                border-radius: 4px;
                color: #1565c0;
            }
        """)

    def setup_menu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Archivo")
        
        action_new = QAction("Nuevo Proyecto", self)
        action_new.triggered.connect(self.new_project)
        file_menu.addAction(action_new)
        
        action_open = QAction("Abrir Proyecto...", self)
        action_open.triggered.connect(self.open_project)
        file_menu.addAction(action_open)
        
        file_menu.addSeparator()
        
        action_save = QAction("Guardar", self)
        action_save.setShortcut("Ctrl+S")
        action_save.triggered.connect(self.save_project)
        file_menu.addAction(action_save)
        
        action_save_as = QAction("Guardar como...", self)
        action_save_as.triggered.connect(self.save_project_as)
        file_menu.addAction(action_save_as)

    def new_project(self):
        resp = QMessageBox.question(self, "Nuevo", "¿Crear nuevo proyecto? Los cambios no guardados se perderán.",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            self.model = AppModel()
            self.main_view.model = self.model
            self.extractor_view.model = self.model
            self.slideshow_view.model = self.model
            self.summary_view.model = self.model
            self.stacked_widget.setCurrentWidget(self.main_view)

    def open_project(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir Proyecto", "", "Video Slide Project (*.vsp)")
        if file_path:
            try:
                new_model = ProjectManager.load_project(file_path)
                self.model = new_model
                self.main_view.model = self.model
                self.extractor_view.model = self.model
                self.slideshow_view.model = self.model
                self.summary_view.model = self.model
                
                # Cargar el video en el extractor y las imagenes en el slideshow
                self.extractor_view.load_video()
                self.slideshow_view.load_images()
                
                self.update_title()
                if new_model.images:
                    self.stacked_widget.setCurrentWidget(self.slideshow_view)
                else:
                    self.stacked_widget.setCurrentWidget(self.extractor_view)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo abrir el proyecto:\\n{e}")

    def save_project(self):
        if not self.model.project_filepath:
            self.save_project_as()
        else:
            ProjectManager.save_project(self.model)

    def save_project_as(self):
        if not self.model.project_name:
            QMessageBox.warning(self, "Aviso", "Aún no hay un proyecto activo para guardar.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar Proyecto", f"{self.model.project_name}.vsp", "Video Slide Project (*.vsp)")
        if file_path:
            if not file_path.endswith('.vsp'):
                file_path += '.vsp'
            ProjectManager.save_project(self.model, file_path)

    def trigger_autosave(self):
        if self.model.project_name and self.model.save_location:
            self.autosave_timer.start(1500) # Auto save after 1.5s of no changes

    def perform_autosave(self):
        ProjectManager.save_project(self.model)

    def update_title(self):
        if self.model.project_name:
            self.setWindowTitle(f"Video to Slide Maker - {self.model.project_name}")
        else:
            self.setWindowTitle("Video to Slide Maker")

    def go_to_extractor(self):
        self.update_title()
        self.extractor_view.load_video()
        self.trigger_autosave()
        self.stacked_widget.setCurrentWidget(self.extractor_view)
        
    def go_to_slideshow(self):
        self.update_title()
        self.slideshow_view.load_images()
        self.stacked_widget.setCurrentWidget(self.slideshow_view)
        
    def go_to_summary(self):
        self.update_title()
        self.summary_view.load_summary()
        self.stacked_widget.setCurrentWidget(self.summary_view)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Fuentes más modernas
    font = app.font()
    font.setFamily("Segoe UI")
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
