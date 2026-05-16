import os
import numpy as np
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, 
                             QComboBox, QDoubleSpinBox, QMessageBox, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QImage

class SlideshowView(QWidget):
    next_requested = pyqtSignal()
    back_requested = pyqtSignal()

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.selected_index = -1
        self.preview_timer = None
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # --- Panel izquierdo: Visor Principal ---
        left_panel = QVBoxLayout()
        
        lbl_title_left = QLabel("Visor del Slide")
        lbl_title_left.setStyleSheet("font-size: 20px; font-weight: bold;")
        left_panel.addWidget(lbl_title_left)

        self.preview_label = QLabel("Selecciona un slide de la lista")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #000; color: white; border: 2px solid #cfd8dc; border-radius: 8px;")
        self.preview_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.preview_label.setMinimumSize(1, 1)
        left_panel.addWidget(self.preview_label, stretch=1)

        main_layout.addLayout(left_panel, stretch=3)

        # --- Panel derecho: Configuración y Galería ---
        right_panel = QVBoxLayout()
        right_panel.setSpacing(15)
        
        lbl_title_right = QLabel("Configuración")
        lbl_title_right.setStyleSheet("font-size: 20px; font-weight: bold;")
        right_panel.addWidget(lbl_title_right)

        # 1. Efecto Global
        effect_layout = QHBoxLayout()
        lbl_effect = QLabel("Efecto Global:")
        self.combo_effect = QComboBox()
        self.combo_effect.addItems([
            "Fade (Fundido)", 
            "Slide Horizontal", 
            "Slide Vertical", 
            "Zoom In",
            "Wipe (Barrido)",
            "Ninguno"
        ])
        self.combo_effect.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.btn_play_all = QPushButton("▶️ Play All")
        self.btn_play_all.setStyleSheet("background-color: #ff9800; font-weight: bold; padding: 6px;")
        self.btn_play_all.clicked.connect(self.play_all)
        
        effect_layout.addWidget(lbl_effect)
        effect_layout.addWidget(self.combo_effect, stretch=1)
        effect_layout.addWidget(self.btn_play_all)
        right_panel.addLayout(effect_layout)

        # 2. Propiedades del Slide Seleccionado
        props_frame = QFrame()
        props_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #cfd8dc; border-radius: 8px;")
        props_layout = QVBoxLayout(props_frame)
        
        time_layout = QHBoxLayout()
        lbl_time = QLabel("Duración (segundos):")
        self.spin_duration = QDoubleSpinBox()
        self.spin_duration.setRange(0.1, 60.0)
        self.spin_duration.setSingleStep(0.5)
        self.spin_duration.setValue(2.0)
        self.spin_duration.setEnabled(False)
        self.spin_duration.valueChanged.connect(self.on_duration_changed)
        time_layout.addWidget(lbl_time)
        time_layout.addWidget(self.spin_duration, stretch=1)
        props_layout.addLayout(time_layout)

        actions_layout = QHBoxLayout()
        self.btn_preview = QPushButton("👁️ Previsualizar")
        self.btn_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_preview.setStyleSheet("""
            QPushButton { background-color: #9C27B0; font-size: 13px; padding: 8px; }
            QPushButton:hover:!disabled { background-color: #7B1FA2; }
        """)
        self.btn_preview.clicked.connect(self.preview_transition)
        self.btn_preview.setEnabled(False)
        
        self.btn_delete = QPushButton("🗑️ Eliminar")
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.setStyleSheet("""
            QPushButton { background-color: #f44336; font-size: 13px; padding: 8px; }
            QPushButton:hover:!disabled { background-color: #d32f2f; }
        """)
        self.btn_delete.clicked.connect(self.delete_slide)
        self.btn_delete.setEnabled(False)
        
        actions_layout.addWidget(self.btn_preview)
        actions_layout.addWidget(self.btn_delete)
        props_layout.addLayout(actions_layout)
        
        right_panel.addWidget(props_frame)

        # 3. Galería (Lista)
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setIconSize(QSize(120, 67))
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setSpacing(10)
        self.list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.list_widget.itemSelectionChanged.connect(self.on_item_selected)
        self.list_widget.model().rowsMoved.connect(self.on_rows_moved)
        self.list_widget.setMinimumWidth(320)
        right_panel.addWidget(self.list_widget, stretch=1)

        # Botones de Navegación
        nav_layout = QHBoxLayout()
        self.btn_back = QPushButton("⬅️ Regresar")
        self.btn_back.setStyleSheet("background-color: #757575; color: white; font-weight: bold; padding: 12px; font-size: 14px;")
        self.btn_back.clicked.connect(self.back_requested.emit)
        
        self.btn_next = QPushButton("Continuar a Resumen ➡️")
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white; font-weight: bold; padding: 12px; font-size: 14px;
            }
            QPushButton:hover:!disabled { background-color: #45a049; }
        """)
        self.btn_next.clicked.connect(self.on_next_clicked)
        
        nav_layout.addWidget(self.btn_back)
        nav_layout.addWidget(self.btn_next)
        right_panel.addLayout(nav_layout)

        main_layout.addLayout(right_panel, stretch=2)

    def load_images(self):
        self.list_widget.clear()
        self.preview_label.clear()
        self.preview_label.setText("Selecciona un slide de la lista")
        self.spin_duration.setEnabled(False)
        self.btn_delete.setEnabled(False)
        self.btn_preview.setEnabled(False)
        self.selected_index = -1

        if hasattr(self.model, 'transition_effect'):
            idx = self.combo_effect.findText(self.model.transition_effect)
            if idx >= 0:
                self.combo_effect.setCurrentIndex(idx)

        for idx, slide in enumerate(self.model.images):
            item = QListWidgetItem(f"Slide {idx+1}\n[{slide.timestamp}]")
            if os.path.exists(slide.file_path):
                pixmap = QPixmap(slide.file_path)
                item.setIcon(QIcon(pixmap))
            
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self.list_widget.addItem(item)

    def on_rows_moved(self, parent, start, end, destination, row):
        new_images = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            idx = item.data(Qt.ItemDataRole.UserRole)
            new_images.append(self.model.images[idx])
            
        self.model.images = new_images
        
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setData(Qt.ItemDataRole.UserRole, i)
            slide = self.model.images[i]
            item.setText(f"Slide {i+1}\n[{slide.timestamp}]")
            
        self.on_item_selected()

    def on_item_selected(self):
        items = self.list_widget.selectedItems()
        if not items:
            self.selected_index = -1
            self.preview_label.setText("Selecciona un slide de la lista")
            self.spin_duration.setEnabled(False)
            self.btn_delete.setEnabled(False)
            self.btn_preview.setEnabled(False)
            return

        item = items[0]
        idx = item.data(Qt.ItemDataRole.UserRole)
        self.selected_index = idx
        slide = self.model.images[idx]

        if os.path.exists(slide.file_path):
            pixmap = QPixmap(slide.file_path)
            self.preview_label.setPixmap(pixmap.scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))

        self.spin_duration.blockSignals(True)
        self.spin_duration.setValue(slide.duration_custom)
        self.spin_duration.setEnabled(True)
        self.spin_duration.blockSignals(False)
        
        self.btn_delete.setEnabled(True)
        self.btn_preview.setEnabled(self.selected_index < len(self.model.images) - 1)

    def on_duration_changed(self, value):
        if self.selected_index >= 0:
            self.model.images[self.selected_index].duration_custom = value

    def delete_slide(self):
        if self.selected_index >= 0:
            resp = QMessageBox.question(self, "Eliminar", "¿Estás seguro de eliminar este slide?", 
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if resp == QMessageBox.StandardButton.Yes:
                del self.model.images[self.selected_index]
                self.load_images()

    def play_all(self):
        if not self.model.images: 
            return
            
        self.model.transition_effect = self.combo_effect.currentText()
        
        from processor import RenderThread
        self.preview_thread = RenderThread(self.model, preview_mode=True, preview_size=(self.preview_label.width(), self.preview_label.height()))
        self.preview_thread.preview_frame.connect(self.on_preview_frame)
        self.preview_thread.finished.connect(self.on_preview_finished)
        
        self.btn_play_all.setText("⏹️ Stop")
        self.btn_play_all.setStyleSheet("background-color: #f44336; font-weight: bold; padding: 6px;")
        self.btn_play_all.clicked.disconnect()
        self.btn_play_all.clicked.connect(self.stop_play_all)
        
        self.btn_next.setEnabled(False)
        self.btn_back.setEnabled(False)
        self.list_widget.setEnabled(False)
        
        self.preview_thread.start()

    def stop_play_all(self):
        if hasattr(self, 'preview_thread') and self.preview_thread.isRunning():
            self.preview_thread.requestInterruption()

    def on_preview_frame(self, qt_img):
        self.preview_label.setPixmap(QPixmap.fromImage(qt_img).scaled(
            self.preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        ))

    def on_preview_finished(self):
        self.btn_play_all.setText("▶️ Play All")
        self.btn_play_all.setStyleSheet("background-color: #ff9800; font-weight: bold; padding: 6px;")
        self.btn_play_all.clicked.disconnect()
        self.btn_play_all.clicked.connect(self.play_all)
        
        self.btn_next.setEnabled(True)
        self.btn_back.setEnabled(True)
        self.list_widget.setEnabled(True)
        self.on_item_selected()

    def preview_transition(self):
        if self.selected_index < 0 or self.selected_index >= len(self.model.images) - 1:
            return
            
        effect = self.combo_effect.currentText()
        if effect == "Ninguno":
            QMessageBox.information(self, "Preview", "No hay efecto de transición seleccionado.")
            return
            
        self.btn_preview.setEnabled(False)
        
        from processor import RenderThread
        from PIL import Image
        
        img1_path = self.model.images[self.selected_index].file_path
        img2_path = self.model.images[self.selected_index + 1].file_path
        
        pil1 = Image.open(img1_path).convert("RGB")
        pil2 = Image.open(img2_path).convert("RGB")
        
        w, h = pil1.size
        pil2 = pil2.resize((w, h), Image.Resampling.LANCZOS)
        
        self.preview_frames = []
        frames_count = 20
        processor = RenderThread(self.model)
        for f in range(frames_count):
            prog = f / float(frames_count)
            frame = processor.apply_transition(pil1, pil2, effect, prog, w, h)
            self.preview_frames.append(frame)
            
        self.preview_idx = 0
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.show_next_preview_frame)
        self.preview_timer.start(33)

    def show_next_preview_frame(self):
        if self.preview_idx < len(self.preview_frames):
            frame = self.preview_frames[self.preview_idx]
            frame_rgb = np.array(frame)
            h, w, ch = frame_rgb.shape
            qt_img = QImage(frame_rgb.data, w, h, ch * w, QImage.Format.Format_RGB888).copy()
            
            self.preview_label.setPixmap(QPixmap.fromImage(qt_img).scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
            self.preview_idx += 1
        else:
            self.preview_timer.stop()
            self.on_item_selected()
            self.btn_preview.setEnabled(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.selected_index >= 0:
            self.on_item_selected()

    def on_next_clicked(self):
        if len(self.model.images) == 0:
            QMessageBox.warning(self, "Sin Imágenes", "Debes volver y tomar al menos un snapshot del video.")
            return
            
        self.model.transition_effect = self.combo_effect.currentText()
        self.next_requested.emit()
