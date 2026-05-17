import os
import cv2
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QSlider, QFrame, QApplication, QListWidget, QListWidgetItem, QMessageBox, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QVariantAnimation, QSize
from PyQt6.QtGui import QImage, QPixmap, QIcon
from model import SlideImage

from PyQt6.QtWidgets import QStyle

class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            val = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.position().toPoint().x(), self.width())
            self.setValue(val)
            self.sliderMoved.emit(val)
        super().mousePressEvent(event)

class VideoLabel(QLabel):
    double_clicked = pyqtSignal()
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()

class ExtractorView(QWidget):
    next_requested = pyqtSignal()
    data_changed = pyqtSignal()

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame_slot)
        
        self.total_frames = 0
        self.fps = 30
        self.is_playing = False
        
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # --- Panel Izquierdo: Reproductor ---
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)
        
        self.video_label = VideoLabel("Cargando video...")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; color: white; border-radius: 8px;")
        self.video_label.setMinimumSize(1, 1)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_label.double_clicked.connect(self.toggle_play)
        left_panel.addWidget(self.video_label, stretch=1)
        
        timeline_layout = QHBoxLayout()
        self.slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.sliderMoved.connect(self.set_position)
        self.slider.sliderPressed.connect(self.pause_video)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal { border: 1px solid #bbb; background: #e0e0e0; height: 12px; border-radius: 6px; }
            QSlider::handle:horizontal { background: #2196F3; border: 1px solid #1976D2; width: 24px; margin: -6px 0; border-radius: 12px; }
            QSlider::handle:horizontal:hover { background: #4CAF50; }
        """)
        self.slider.setCursor(Qt.CursorShape.PointingHandCursor)
        timeline_layout.addWidget(self.slider)
        
        self.lbl_time = QLabel("00:00 / 00:00")
        self.lbl_time.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 14px; min-width: 90px;")
        self.lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timeline_layout.addWidget(self.lbl_time)
        left_panel.addLayout(timeline_layout)
        
        controls_layout = QHBoxLayout()
        self.btn_play_pause = QPushButton("▶️ Play")
        self.btn_play_pause.clicked.connect(self.toggle_play)
        self.btn_play_pause.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_play_pause.setStyleSheet("""
            QPushButton { background-color: #2196F3; color: white; padding: 10px 20px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background-color: #1976D2; }
        """)
        
        self.btn_snapshot = QPushButton("📸 Tomar Snapshot")
        self.btn_snapshot.setStyleSheet("""
            QPushButton { background-color: #ff9800; color: white; font-weight: bold; padding: 10px 20px; font-size: 14px; }
            QPushButton:hover { background-color: #fb8c00; }
        """)
        self.btn_snapshot.clicked.connect(self.take_snapshot)
        self.btn_snapshot.setCursor(Qt.CursorShape.PointingHandCursor)
        
        controls_layout.addWidget(self.btn_play_pause)
        controls_layout.addWidget(self.btn_snapshot)
        controls_layout.addStretch()
        left_panel.addLayout(controls_layout)
        
        main_layout.addLayout(left_panel, stretch=3)

        # --- Panel Derecho: Galería de Snapshots ---
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)

        lbl_snapshots = QLabel("Snapshots Tomados")
        lbl_snapshots.setStyleSheet("font-weight: bold; font-size: 18px; color: #2c3e50;")
        right_panel.addWidget(lbl_snapshots)

        self.list_snapshots = QListWidget()
        self.list_snapshots.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_snapshots.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_snapshots.setMinimumWidth(280)
        self.list_snapshots.setIconSize(QSize(120, 67))
        self.list_snapshots.setSpacing(10)
        self.list_snapshots.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #cfd8dc; padding: 8px;")
        self.list_snapshots.itemSelectionChanged.connect(self.on_snapshot_selected)
        right_panel.addWidget(self.list_snapshots, stretch=1)

        self.btn_delete_snap = QPushButton("🗑️ Eliminar Snapshot")
        self.btn_delete_snap.setEnabled(False)
        self.btn_delete_snap.setStyleSheet("""
            QPushButton { background-color: #f44336; padding: 10px; font-weight: bold; color: white; }
            QPushButton:hover:!disabled { background-color: #d32f2f; }
        """)
        self.btn_delete_snap.clicked.connect(self.delete_snapshot)
        right_panel.addWidget(self.btn_delete_snap)

        self.btn_next = QPushButton("Configurar Slides ➡️")
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 12px 20px; font-size: 14px; }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.btn_next.clicked.connect(self.on_next_clicked)
        right_panel.addWidget(self.btn_next)

        main_layout.addLayout(right_panel, stretch=1)

    def load_video(self):
        if self.model.video_path:
            self.cap = cv2.VideoCapture(self.model.video_path)
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
            self.slider.setRange(0, max(0, self.total_frames - 1))
            self.timer.setInterval(int(1000 / self.fps))
            self.set_position(0)
            self.refresh_snapshots()
            self.setFocus()

    def refresh_snapshots(self):
        self.list_snapshots.clear()
        for idx, slide in enumerate(self.model.images):
            item = QListWidgetItem(f"[{slide.timestamp}]")
            if os.path.exists(slide.file_path):
                item.setIcon(QIcon(QPixmap(slide.file_path)))
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self.list_snapshots.addItem(item)
        self.btn_delete_snap.setEnabled(False)

    def on_snapshot_selected(self):
        self.btn_delete_snap.setEnabled(len(self.list_snapshots.selectedItems()) > 0)

    def delete_snapshot(self):
        items = self.list_snapshots.selectedItems()
        if items:
            idx = items[0].data(Qt.ItemDataRole.UserRole)
            resp = QMessageBox.question(self, "Eliminar", "¿Eliminar este snapshot?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if resp == QMessageBox.StandardButton.Yes:
                del self.model.images[idx]
                self.refresh_snapshots()
                self.data_changed.emit()

    def next_frame_slot(self):
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.display_frame(frame)
                current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                self.update_ui_state(current_frame)
            else:
                self.pause_video()

    def update_ui_state(self, current_frame):
        self.slider.blockSignals(True)
        self.slider.setValue(current_frame)
        self.slider.blockSignals(False)
        
        current_sec = int(current_frame / self.fps)
        total_sec = int(self.total_frames / self.fps)
        self.lbl_time.setText(f"{current_sec // 60:02d}:{current_sec % 60:02d} / {total_sec // 60:02d}:{total_sec % 60:02d}")

    def display_frame(self, frame):
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
        if self.cap is not None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, position)
            ret, frame = self.cap.read()
            if ret:
                self.display_frame(frame)
                self.update_ui_state(position)
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
        self.pause_video()
        if self.cap is not None:
            current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            ret, frame = self.cap.read()
            if ret:
                total_seconds = int(current_frame / self.fps)
                mins = total_seconds // 60
                secs = total_seconds % 60
                timestamp_str = f"{mins:02d}:{secs:02d}"
                
                import tempfile
                temp_dir = os.path.join(tempfile.gettempdir(), "video_slides_app", self.model.project_name.replace(' ', '_'))
                os.makedirs(temp_dir, exist_ok=True)
                
                filename = f"slide_{len(self.model.images)+1}_{mins:02d}-{secs:02d}.jpg"
                filepath = os.path.join(temp_dir, filename)
                
                cv2.imwrite(filepath, frame)
                
                slide = SlideImage(timestamp=timestamp_str, duration_custom=2.0, file_path=filepath)
                self.model.images.append(slide)
                self.refresh_snapshots()
                self.shutter_flash()
                self.data_changed.emit()
                
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)

    def shutter_flash(self):
        import subprocess
        try:
            subprocess.Popen(["paplay", "/usr/share/sounds/freedesktop/stereo/camera-shutter.oga"], 
                             stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        except Exception:
            pass
        
        self.shutter_top = QWidget(self.video_label)
        self.shutter_top.setStyleSheet("background-color: black;")
        self.shutter_bottom = QWidget(self.video_label)
        self.shutter_bottom.setStyleSheet("background-color: black;")
        
        w, h = self.video_label.width(), self.video_label.height()
        self.shutter_top.setGeometry(0, 0, w, 0)
        self.shutter_bottom.setGeometry(0, h, w, 0)
        self.shutter_top.show()
        self.shutter_bottom.show()
        
        self.anim = QVariantAnimation()
        self.anim.setDuration(120)
        self.anim.setStartValue(0)
        self.anim.setEndValue(h // 2 + 5)
        
        def update_shutters(val):
            self.shutter_top.setGeometry(0, 0, w, val)
            self.shutter_bottom.setGeometry(0, h - val, w, val)
            
        def reverse_shutters():
            self.anim2 = QVariantAnimation()
            self.anim2.setDuration(150)
            self.anim2.setStartValue(h // 2 + 5)
            self.anim2.setEndValue(0)
            self.anim2.valueChanged.connect(update_shutters)
            self.anim2.finished.connect(self.shutter_top.deleteLater)
            self.anim2.finished.connect(self.shutter_bottom.deleteLater)
            self.anim2.start()
            
        self.anim.valueChanged.connect(update_shutters)
        self.anim.finished.connect(reverse_shutters)
        self.anim.start()

    def keyPressEvent(self, event):
        if self.cap is None: return
        if event.key() == Qt.Key.Key_Right:
            self.pause_video()
            current = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.set_position(min(self.total_frames - 1, current + 1))
        elif event.key() == Qt.Key.Key_Left:
            self.pause_video()
            current = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.set_position(max(0, current - 1))
        elif event.key() == Qt.Key.Key_Space:
            self.toggle_play()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.is_playing and self.cap is not None:
            current = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.set_position(current)

    def on_next_clicked(self):
        self.pause_video()
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.next_requested.emit()
