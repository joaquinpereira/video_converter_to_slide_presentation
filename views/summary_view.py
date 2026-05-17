import os
import sys
import subprocess
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QCheckBox, QProgressBar, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from processor import RenderThread

class SummaryView(QWidget):
    back_requested = pyqtSignal()
    data_changed = pyqtSignal()

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.thread = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Título
        lbl_title = QLabel("Sumario del Proyecto")
        lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2196F3;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)

        # Contenedor de resumen
        summary_frame = QFrame()
        summary_frame.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ccc; border-radius: 10px;")
        summary_layout = QVBoxLayout()
        
        self.lbl_info = QLabel("")
        self.lbl_info.setStyleSheet("font-size: 16px; color: #333; border: none;")
        summary_layout.addWidget(self.lbl_info)
        
        summary_frame.setLayout(summary_layout)
        layout.addWidget(summary_frame)

        # Opciones de exportación
        options_layout = QHBoxLayout()
        
        self.chk_gif = QCheckBox("Generar GIF Animado")
        self.chk_gif.setChecked(True)
        self.chk_gif.stateChanged.connect(self.update_model_options)
        
        self.chk_mp4 = QCheckBox("Generar Video MP4")
        self.chk_mp4.setChecked(False)
        self.chk_mp4.stateChanged.connect(self.update_model_options)
        
        options_layout.addWidget(self.chk_gif)
        options_layout.addWidget(self.chk_mp4)
        options_layout.addStretch()
        layout.addLayout(options_layout)

        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Listo para procesar.")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #666;")
        layout.addWidget(self.lbl_status)

        layout.addStretch()

        # Botones
        btn_layout = QHBoxLayout()
        
        self.btn_back = QPushButton("⬅️ Regresar")
        self.btn_back.setStyleSheet("background-color: #757575; color: white; font-weight: bold; padding: 15px; font-size: 16px; border-radius: 8px;")
        self.btn_back.clicked.connect(self.back_requested.emit)
        
        self.btn_process = QPushButton("🚀 Procesar Slideshow")
        self.btn_process.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_process.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white; font-weight: bold; padding: 15px; font-size: 16px; border-radius: 8px;
            }
            QPushButton:hover:!disabled { background-color: #45a049; }
            QPushButton:disabled { background-color: #a5d6a7; }
        """)
        self.btn_process.clicked.connect(self.start_processing)
        
        self.btn_open_folder = QPushButton("📂 Abrir Carpeta")
        self.btn_open_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_folder.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; color: white; font-weight: bold; padding: 15px; font-size: 16px; border-radius: 8px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.btn_open_folder.clicked.connect(self.open_output_folder)
        self.btn_open_folder.hide()
        
        btn_layout.addWidget(self.btn_back)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_process)
        btn_layout.addWidget(self.btn_open_folder)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_summary(self):
        """Se llama antes de mostrar la pantalla"""
        total_imgs = len(self.model.images)
        total_time = sum(s.duration_custom for s in self.model.images)
        
        info = (
            f"<b>Nombre del Proyecto:</b> {self.model.project_name}<br><br>"
            f"<b>Ruta de Guardado:</b> {self.model.save_location}<br><br>"
            f"<b>Total de Imágenes:</b> {total_imgs}<br><br>"
            f"<b>Duración Estimada:</b> {total_time:.1f} segundos<br><br>"
            f"<b>Efecto de Transición:</b> {self.model.transition_effect}"
        )
        self.lbl_info.setText(info)
        
        self.chk_gif.setChecked(self.model.export_gif)
        self.chk_mp4.setChecked(self.model.export_mp4)
        
        self.progress_bar.hide()
        self.progress_bar.setValue(0)
        self.lbl_status.setText("Listo para procesar.")
        self.btn_process.setEnabled(True)
        self.btn_process.setText("🚀 Procesar Slideshow")

    def update_model_options(self):
        self.model.export_gif = self.chk_gif.isChecked()
        self.model.export_mp4 = self.chk_mp4.isChecked()
        has_selection = self.model.export_gif or self.model.export_mp4
        
        self.data_changed.emit()
        
        self.btn_process.setEnabled(has_selection)
        if not has_selection:
            self.lbl_status.setText("⚠️ Selecciona al menos un formato para procesar.")
        else:
            self.lbl_status.setText("Listo para procesar.")

    def start_processing(self):
        if not self.model.export_gif and not self.model.export_mp4:
            QMessageBox.warning(self, "Atención", "Debes seleccionar al menos un formato de exportación (GIF o MP4).")
            return

        self.btn_process.setEnabled(False)
        self.chk_gif.setEnabled(False)
        self.chk_mp4.setEnabled(False)
        self.btn_back.setEnabled(False)
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.btn_open_folder.hide()
        
        # Iniciar el QThread
        self.thread = RenderThread(self.model)
        self.thread.progress.connect(self.on_progress)
        self.thread.finished.connect(self.on_finished)
        self.thread.start()

    def on_progress(self, percent, msg):
        self.progress_bar.setValue(percent)
        self.lbl_status.setText(msg)

    def on_finished(self, success, msg):
        self.progress_bar.setValue(100)
        self.chk_gif.setEnabled(True)
        self.chk_mp4.setEnabled(True)
        self.btn_back.setEnabled(True)
        
        if success:
            self.lbl_status.setText("¡Completado! " + msg.replace("\n", " "))
            self.btn_process.setText("🔄 Procesar de Nuevo")
            self.btn_process.setEnabled(True)
            self.btn_open_folder.show()
            QMessageBox.information(self, "Éxito", "¡Procesamiento completado con éxito!\n\n" + msg)
        else:
            self.lbl_status.setText("❌ Error en el procesamiento.")
            self.btn_process.setText("🚀 Reintentar")
            self.btn_process.setEnabled(True)
            QMessageBox.critical(self, "Error", msg)

    def open_output_folder(self):
        folder = self.model.save_location
        if os.name == 'nt':
            os.startfile(folder)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', folder])
        else:
            subprocess.Popen(['xdg-open', folder])
