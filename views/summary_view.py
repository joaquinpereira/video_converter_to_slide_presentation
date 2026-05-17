import os
import sys
import subprocess
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QCheckBox, QProgressBar, QMessageBox, QFrame, QComboBox)
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
        lbl_title.setObjectName("lblTitle")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)

        # Contenedor de resumen
        summary_frame = QFrame()
        summary_frame.setObjectName("summaryFrame")
        summary_layout = QVBoxLayout()
        
        self.lbl_info = QLabel("")
        self.lbl_info.setObjectName("lblSubtitle")
        summary_layout.addWidget(self.lbl_info)
        
        summary_frame.setLayout(summary_layout)
        layout.addWidget(summary_frame)
        
        # Ajustes de Calidad
        quality_layout = QHBoxLayout()
        quality_layout.setSpacing(15)
        
        lbl_res = QLabel("Resolución:")
        lbl_res.setObjectName("lblSubtitle")
        self.combo_res = QComboBox()
        self.combo_res.addItems(["Original", "1920x1080 (FHD)", "1280x720 (HD)", "854x480 (SD)"])
        self.combo_res.currentIndexChanged.connect(self.update_model_options)
        self.combo_res.setCursor(Qt.CursorShape.PointingHandCursor)
        
        lbl_fps = QLabel("Fotogramas (FPS):")
        lbl_fps.setObjectName("lblSubtitle")
        self.combo_fps = QComboBox()
        self.combo_fps.addItems(["15", "24", "30", "60"])
        self.combo_fps.setCurrentText("30")
        self.combo_fps.currentIndexChanged.connect(self.update_model_options)
        self.combo_fps.setCursor(Qt.CursorShape.PointingHandCursor)
        
        quality_layout.addWidget(lbl_res)
        quality_layout.addWidget(self.combo_res)
        quality_layout.addWidget(lbl_fps)
        quality_layout.addWidget(self.combo_fps)
        quality_layout.addStretch()
        layout.addLayout(quality_layout)

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
        self.lbl_status.setObjectName("lblStatus")
        layout.addWidget(self.lbl_status)

        layout.addStretch()

        # Botones
        btn_layout = QHBoxLayout()
        
        self.btn_back = QPushButton("⬅️ Regresar")
        self.btn_back.setObjectName("btnSecondary")
        self.btn_back.clicked.connect(self.back_requested.emit)
        
        self.btn_process = QPushButton("🚀 Procesar Slideshow")
        self.btn_process.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_process.setObjectName("btnPrimary")
        self.btn_process.clicked.connect(self.start_processing)
        
        self.btn_open_folder = QPushButton("📂 Abrir Carpeta")
        self.btn_open_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_folder.setObjectName("btnInfo")
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
        
        self.combo_res.blockSignals(True)
        self.combo_res.setCurrentText(getattr(self.model, 'export_resolution', 'Original'))
        self.combo_res.blockSignals(False)
        
        self.combo_fps.blockSignals(True)
        self.combo_fps.setCurrentText(str(getattr(self.model, 'export_fps', 30)))
        self.combo_fps.blockSignals(False)
        
        self.progress_bar.hide()
        self.progress_bar.setValue(0)
        self.lbl_status.setText("Listo para procesar.")
        self.btn_process.setEnabled(True)
        self.btn_process.setText("🚀 Procesar Slideshow")

    def update_model_options(self):
        self.model.export_gif = self.chk_gif.isChecked()
        self.model.export_mp4 = self.chk_mp4.isChecked()
        self.model.export_resolution = self.combo_res.currentText()
        self.model.export_fps = int(self.combo_fps.currentText())
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
