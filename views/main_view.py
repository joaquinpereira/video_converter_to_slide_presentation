import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFileDialog, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal

class DropArea(QFrame):
    file_dropped = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setObjectName("dropArea")
        layout = QVBoxLayout()
        self.label = QLabel("Arrastra y suelta tu video aquí\no haz clic para explorar")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setObjectName("lblSubtitle")
        layout.addWidget(self.label)
        self.setLayout(layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                self.file_dropped.emit(file_path)
            else:
                self.label.setText("Formato no soportado. Usa MP4, AVI, MOV, MKV.")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar Video", "", "Archivos de Video (*.mp4 *.avi *.mov *.mkv)"
            )
            if file_path:
                self.file_dropped.emit(file_path)

class MainView(QWidget):
    # Señal para comunicar al Controlador que queremos ir a la fase 2
    next_requested = pyqtSignal()
    open_project_requested = pyqtSignal()
    
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Título
        title = QLabel("Configuración Inicial")
        title.setObjectName("lblTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Área de Drop
        self.drop_area = DropArea()
        self.drop_area.file_dropped.connect(self.on_file_selected)
        layout.addWidget(self.drop_area, stretch=1)

        self.lbl_video_path = QLabel("Video: Ninguno seleccionado")
        self.lbl_video_path.setObjectName("lblStatus")
        layout.addWidget(self.lbl_video_path)

        # Nombre del Proyecto
        pn_layout = QHBoxLayout()
        pn_label = QLabel("Nombre del Proyecto:")
        pn_label.setFixedWidth(140)
        self.txt_project_name = QLineEdit()
        self.txt_project_name.setPlaceholderText("Ej: Mi Presentación")
        self.txt_project_name.textChanged.connect(self.validate_form)
        pn_layout.addWidget(pn_label)
        pn_layout.addWidget(self.txt_project_name)
        layout.addLayout(pn_layout)

        # Ubicación de guardado
        sl_layout = QHBoxLayout()
        sl_label = QLabel("Carpeta de guardado:")
        sl_label.setFixedWidth(140)
        self.txt_save_location = QLineEdit()
        self.txt_save_location.setReadOnly(True)
        self.txt_save_location.setPlaceholderText("Selecciona dónde guardar...")
        btn_browse = QPushButton("Explorar...")
        btn_browse.setObjectName("btnSecondary")
        btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_browse.clicked.connect(self.browse_save_location)
        sl_layout.addWidget(sl_label)
        sl_layout.addWidget(self.txt_save_location)
        sl_layout.addWidget(btn_browse)
        layout.addLayout(sl_layout)

        # Botones de Acción Principales
        action_layout = QHBoxLayout()
        action_layout.setSpacing(15)
        
        self.btn_open = QPushButton("📂 Abrir Proyecto")
        self.btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open.setObjectName("btnInfo")
        self.btn_open.clicked.connect(self.open_project_requested.emit)
        
        self.btn_next = QPushButton("🚀 Crear Proyecto")
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setObjectName("btnPrimary")
        self.btn_next.clicked.connect(self.on_next_clicked)
        self.btn_next.setEnabled(False)
        
        action_layout.addWidget(self.btn_open)
        action_layout.addWidget(self.btn_next)
        
        layout.addLayout(action_layout)
        self.setLayout(layout)

    def on_file_selected(self, file_path):
        self.model.video_path = file_path
        self.lbl_video_path.setText(f"Video: {file_path}")
        self.drop_area.label.setText(f"🎥 Video Cargado:\n{os.path.basename(file_path)}")
        self.validate_form()

    def browse_save_location(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar ubicación de guardado")
        if folder:
            self.model.save_location = folder
            self.txt_save_location.setText(folder)
            self.validate_form()

    def validate_form(self):
        self.model.project_name = self.txt_project_name.text().strip()
        is_valid = bool(self.model.video_path and self.model.project_name and self.model.save_location)
        self.btn_next.setEnabled(is_valid)

    def on_next_clicked(self):
        self.next_requested.emit()
