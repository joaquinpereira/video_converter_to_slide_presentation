import cv2
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QSlider)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from model import SlideImage

class ExtractorView(QWidget):
    next_requested = pyqtSignal()

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame_slot)
        
        self.total_frames = 0
        self.fps = 30
        self.is_playing = False
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Etiqueta de Display del Video
        self.video_label = QLabel("Cargando video...")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; color: white;")
        self.video_label.setMinimumSize(640, 360)
        
        layout.addWidget(self.video_label, stretch=1)
        
        # Slider de Línea de Tiempo
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.sliderMoved.connect(self.set_position)
        self.slider.sliderPressed.connect(self.pause_video)
        layout.addWidget(self.slider)
        
        # Controles de Reproducción y Snapshot
        controls_layout = QHBoxLayout()
        
        self.btn_play_pause = QPushButton("▶️ Play")
        self.btn_play_pause.clicked.connect(self.toggle_play)
        self.btn_play_pause.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.btn_snapshot = QPushButton("📸 Tomar Snapshot")
        self.btn_snapshot.setStyleSheet("""
            QPushButton {
                background-color: #ff9800; color: white; font-weight: bold;
            }
            QPushButton:hover {
                background-color: #fb8c00;
            }
        """)
        self.btn_snapshot.clicked.connect(self.take_snapshot)
        self.btn_snapshot.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.lbl_snapshots = QLabel("Snapshots: 0")
        self.lbl_snapshots.setStyleSheet("font-weight: bold; color: #333; padding-left: 20px;")
        
        controls_layout.addWidget(self.btn_play_pause)
        controls_layout.addWidget(self.btn_snapshot)
        controls_layout.addStretch()
        controls_layout.addWidget(self.lbl_snapshots)
        
        layout.addLayout(controls_layout)
        
        # Botón para ir a la Fase 3
        self.btn_next = QPushButton("Ver Slides / Continuar ➡️")
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.btn_next.clicked.connect(self.on_next_clicked)
        
        layout.addWidget(self.btn_next, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.setLayout(layout)

    def load_video(self):
        """Se llama cuando el usuario avanza desde la Fase 1 a esta pantalla"""
        if self.model.video_path:
            self.cap = cv2.VideoCapture(self.model.video_path)
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
            self.slider.setRange(0, max(0, self.total_frames - 1))
            self.timer.setInterval(int(1000 / self.fps))
            
            # Mostrar primer frame
            self.set_position(0)
            
            # Actualizar contador
            self.lbl_snapshots.setText(f"Snapshots: {len(self.model.images)}")

    def next_frame_slot(self):
        """Slot llamado por el QTimer para reproducir el video"""
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.display_frame(frame)
                current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                self.slider.blockSignals(True)
                self.slider.setValue(current_frame)
                self.slider.blockSignals(False)
            else:
                self.pause_video()

    def display_frame(self, frame):
        """Convierte frame BGR de OpenCV a QPixmap y lo muestra"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        qt_img = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)
        
        self.video_label.setPixmap(pixmap.scaled(
            self.video_label.width(), self.video_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        ))

    def set_position(self, position):
        """Se busca el frame exacto en el video"""
        if self.cap is not None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, position)
            ret, frame = self.cap.read()
            if ret:
                self.display_frame(frame)
            
            # Restaurar el puntero de opencv para que siga desde acá
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, position)

    def toggle_play(self):
        if self.is_playing:
            self.pause_video()
        else:
            self.is_playing = True
            self.btn_play_pause.setText("⏸️ Pause")
            self.timer.start()

    def pause_video(self):
        self.is_playing = False
        self.btn_play_pause.setText("▶️ Play")
        self.timer.stop()

    def take_snapshot(self):
        """Pausa el video, guarda la imagen y añade al modelo"""
        self.pause_video()
        if self.cap is not None:
            current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            ret, frame = self.cap.read()
            if ret:
                # Calcular timestamp MM:SS
                total_seconds = int(current_frame / self.fps)
                mins = total_seconds // 60
                secs = total_seconds % 60
                timestamp_str = f"{mins:02d}:{secs:02d}"
                
                # Crear directorio temporal en la ubicación de guardado
                temp_dir = os.path.join(self.model.save_location, f"{self.model.project_name}_slides")
                os.makedirs(temp_dir, exist_ok=True)
                
                # Nombre del archivo
                filename = f"slide_{len(self.model.images)+1}_{mins:02d}-{secs:02d}.jpg"
                filepath = os.path.join(temp_dir, filename)
                
                # Guardar en disco
                cv2.imwrite(filepath, frame)
                
                # Añadir al modelo
                slide = SlideImage(timestamp=timestamp_str, duration_custom=2.0, file_path=filepath)
                self.model.images.append(slide)
                
                self.lbl_snapshots.setText(f"Snapshots: {len(self.model.images)}")
                
            # Retornar el puntero para que no avance al tomar snapshot
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Ajustar el frame cuando la ventana cambie de tamaño si está en pausa
        if not self.is_playing and self.cap is not None:
            current = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.set_position(current)

    def on_next_clicked(self):
        """Limpiar y avanzar"""
        self.pause_video()
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.next_requested.emit()
