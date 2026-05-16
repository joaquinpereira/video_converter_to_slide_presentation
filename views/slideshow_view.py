import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, 
                             QComboBox, QDoubleSpinBox, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QPixmap

class SlideshowView(QWidget):
    next_requested = pyqtSignal()

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.selected_index = -1
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # --- Panel izquierdo: Galería de imágenes ---
        left_panel = QVBoxLayout()
        
        lbl_title = QLabel("Configuración de Slideshow")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        left_panel.addWidget(lbl_title)

        # Selector de Efecto Global
        effect_layout = QHBoxLayout()
        lbl_effect = QLabel("Efecto de Transición Global:")
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
        effect_layout.addWidget(lbl_effect)
        effect_layout.addWidget(self.combo_effect)
        effect_layout.addStretch()
        left_panel.addLayout(effect_layout)

        # Galería (QListWidget en modo Icono)
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setIconSize(QSize(160, 90)) # Aspect ratio 16:9
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setSpacing(15)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
            }
            QListWidget::item:selected {
                background-color: #bbdefb;
                border: 2px solid #2196F3;
                border-radius: 5px;
                color: black;
            }
        """)
        self.list_widget.itemSelectionChanged.connect(self.on_item_selected)
        left_panel.addWidget(self.list_widget)

        main_layout.addLayout(left_panel, stretch=2)

        # --- Panel derecho: Propiedades de la imagen seleccionada ---
        right_panel = QVBoxLayout()
        right_panel.setSpacing(20)
        
        lbl_props = QLabel("Propiedades del Slide")
        lbl_props.setStyleSheet("font-size: 16px; font-weight: bold;")
        right_panel.addWidget(lbl_props)

        # Preview Label
        self.preview_label = QLabel("Selecciona un slide")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #eaeaea; border: 1px dashed #aaa; border-radius: 5px;")
        self.preview_label.setFixedSize(240, 135) # Aspect ratio 16:9
        right_panel.addWidget(self.preview_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Tiempo del slide
        time_layout = QHBoxLayout()
        lbl_time = QLabel("Duración (segundos):")
        self.spin_duration = QDoubleSpinBox()
        self.spin_duration.setRange(0.1, 60.0)
        self.spin_duration.setSingleStep(0.5)
        self.spin_duration.setValue(2.0)
        self.spin_duration.setEnabled(False)
        self.spin_duration.valueChanged.connect(self.on_duration_changed)
        
        time_layout.addWidget(lbl_time)
        time_layout.addWidget(self.spin_duration)
        right_panel.addLayout(time_layout)

        right_panel.addStretch()

        # Botón Continuar
        self.btn_next = QPushButton("Continuar a Resumen ➡️")
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; color: white; font-weight: bold; padding: 12px; border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.btn_next.clicked.connect(self.on_next_clicked)
        right_panel.addWidget(self.btn_next)

        main_layout.addLayout(right_panel, stretch=1)

    def load_images(self):
        """Se llama al entrar a la Fase 3, para recargar la galería"""
        self.list_widget.clear()
        self.preview_label.clear()
        self.preview_label.setText("Selecciona un slide")
        self.spin_duration.setEnabled(False)
        self.selected_index = -1

        # Cargar preferencia global si existe
        if hasattr(self.model, 'transition_effect'):
            idx = self.combo_effect.findText(self.model.transition_effect)
            if idx >= 0:
                self.combo_effect.setCurrentIndex(idx)

        for idx, slide in enumerate(self.model.images):
            # Crear item
            item = QListWidgetItem(f"Slide {idx+1}\n[{slide.timestamp}]")
            
            # Cargar imagen y escalarla para el icono
            if os.path.exists(slide.file_path):
                pixmap = QPixmap(slide.file_path)
                item.setIcon(QIcon(pixmap))
            
            # Guardar el índice en el item para recuperarlo
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self.list_widget.addItem(item)

    def on_item_selected(self):
        items = self.list_widget.selectedItems()
        if not items:
            self.selected_index = -1
            self.preview_label.setText("Selecciona un slide")
            self.spin_duration.setEnabled(False)
            return

        item = items[0]
        idx = item.data(Qt.ItemDataRole.UserRole)
        self.selected_index = idx
        slide = self.model.images[idx]

        # Mostrar preview
        if os.path.exists(slide.file_path):
            pixmap = QPixmap(slide.file_path)
            self.preview_label.setPixmap(pixmap.scaled(
                self.preview_label.width(), self.preview_label.height(),
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))

        # Actualizar spinbox sin disparar el signal de valueChanged
        self.spin_duration.blockSignals(True)
        self.spin_duration.setValue(slide.duration_custom)
        self.spin_duration.setEnabled(True)
        self.spin_duration.blockSignals(False)

    def on_duration_changed(self, value):
        if self.selected_index >= 0:
            self.model.images[self.selected_index].duration_custom = value

    def on_next_clicked(self):
        if len(self.model.images) == 0:
            QMessageBox.warning(self, "Sin Imágenes", "Debes volver y tomar al menos un snapshot del video.")
            return
            
        # Guardar configuración global en el modelo
        self.model.transition_effect = self.combo_effect.currentText()
        self.next_requested.emit()
