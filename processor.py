import os
import cv2
import numpy as np
from PIL import Image
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage

class RenderThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    preview_frame = pyqtSignal(QImage)

    def __init__(self, model, preview_mode=False, preview_size=None):
        super().__init__()
        self.model = model
        self.fps = getattr(self.model, 'export_fps', 30)
        self.preview_mode = preview_mode
        self.preview_size = preview_size
        if self.preview_mode:
            self.fps = 15
        self.transition_time = 0.5

    def emit_preview(self, pil_img):
        frame_rgb = np.array(pil_img)
        h, w, ch = frame_rgb.shape
        qt_img = QImage(frame_rgb.data, w, h, ch * w, QImage.Format.Format_RGB888).copy()
        self.preview_frame.emit(qt_img)

    def run(self):
        try:
            if not self.preview_mode:
                self.progress.emit(0, "Preparando imágenes en memoria...")
                
            if not self.model.images:
                self.finished.emit(False, "No hay imágenes para procesar.")
                return

            res_str = getattr(self.model, 'export_resolution', 'Original')
            target_size = None
            if "1920x1080" in res_str: target_size = (1920, 1080)
            elif "1280x720" in res_str: target_size = (1280, 720)
            elif "854x480" in res_str: target_size = (854, 480)

            # Cargar imágenes
            pil_images = []
            for slide in self.model.images:
                if os.path.exists(slide.file_path):
                    img = Image.open(slide.file_path).convert("RGB")
                    if target_size and img.size != target_size:
                        img = img.resize(target_size, Image.Resampling.LANCZOS)
                    pil_images.append((img, slide.duration_custom))

            if not pil_images:
                self.finished.emit(False, "Las rutas de las imágenes no son válidas.")
                return

            if self.preview_mode and self.preview_size:
                base_width, base_height = self.preview_size
            else:
                base_width, base_height = pil_images[0][0].size
            
            sequence = []
            total_slides = len(pil_images)
            effect = self.model.transition_effect
            trans_frames_count = int(self.transition_time * self.fps) if effect != "Ninguno" else 0

            # --- GENERACIÓN DE FRAMES ---
            for i in range(total_slides):
                if self.isInterruptionRequested(): break
                
                if not self.preview_mode:
                    self.progress.emit(int((i / total_slides) * 40), f"Calculando frame {i+1} de {total_slides}...")
                current_img, duration = pil_images[i]
                
                if current_img.size != (base_width, base_height):
                    current_img = current_img.resize((base_width, base_height), Image.Resampling.LANCZOS)
                
                static_frames = int(duration * self.fps) - (trans_frames_count if i < total_slides - 1 else 0)
                if static_frames < 1: 
                    static_frames = 1
                
                for _ in range(static_frames):
                    if self.isInterruptionRequested(): break
                    if self.preview_mode:
                        self.emit_preview(current_img)
                        self.msleep(int(1000 / self.fps))
                    else:
                        sequence.append(current_img.copy())
                
                if self.isInterruptionRequested(): break
                
                if effect != "Ninguno" and i < total_slides - 1:
                    next_img, _ = pil_images[i+1]
                    if next_img.size != (base_width, base_height):
                        next_img = next_img.resize((base_width, base_height), Image.Resampling.LANCZOS)
                        
                    for f in range(trans_frames_count):
                        if self.isInterruptionRequested(): break
                        prog = f / float(trans_frames_count)
                        frame = self.apply_transition(current_img, next_img, effect, prog, base_width, base_height)
                        if self.preview_mode:
                            self.emit_preview(frame)
                            self.msleep(int(1000 / self.fps))
                        else:
                            sequence.append(frame)

            if self.preview_mode or self.isInterruptionRequested():
                self.finished.emit(True, "")
                return

            # --- EXPORTACIÓN ---
            output_dir = self.model.save_location
            proj_name = self.model.project_name.replace(' ', '_')
            
            import datetime
            now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            res_str_full = getattr(self.model, 'export_resolution', 'Original')
            if "1080" in res_str_full: res_suffix = "1080p"
            elif "720" in res_str_full: res_suffix = "720p"
            elif "480" in res_str_full: res_suffix = "480p"
            else: res_suffix = "Original"
            
            suffix = f"_{res_suffix}_{self.fps}fps_{now_str}"
            base_filename = f"{proj_name}{suffix}"
            
            msg_final = ""
            
            if self.model.export_mp4:
                mp4_path = os.path.join(output_dir, f"{base_filename}.mp4")
                self.progress.emit(45, "Codificando Video MP4 (Esto puede tardar)...")
                
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(mp4_path, fourcc, self.fps, (base_width, base_height))
                
                total_frames = len(sequence)
                for idx, frame in enumerate(sequence):
                    if idx % 15 == 0:
                        percent = 45 + int((idx / total_frames) * 25)
                        self.progress.emit(percent, f"Escribiendo video MP4 ({idx}/{total_frames})...")
                    
                    cv_img = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
                    out.write(cv_img)
                out.release()
                msg_final += f"✅ Video MP4 creado.\n"

            if self.model.export_gif:
                self.progress.emit(90, "Guardando archivo GIF (esto puede tardar)...")
                gif_path = os.path.join(output_dir, f"{base_filename}.gif")
                sequence[0].save(
                    gif_path,
                    save_all=True,
                    append_images=sequence[1:],
                    duration=int(1000 / self.fps),
                    loop=0,
                    optimize=True
                )
                msg_final += f"✅ Archivo GIF creado.\n"

            self.progress.emit(100, "¡Finalizado!")
            self.finished.emit(True, msg_final)

        except Exception as e:
            import traceback
            self.finished.emit(False, f"Error interno: {str(e)}\n\n{traceback.format_exc()}")

    def apply_transition(self, img1, img2, effect, progress, width, height):
        if effect == "Fade (Fundido)":
            return Image.blend(img1, img2, progress)
        elif effect == "Slide Horizontal":
            offset = int(width * progress)
            res = Image.new("RGB", (width, height))
            res.paste(img1, (-offset, 0))
            res.paste(img2, (width - offset, 0))
            return res
        elif effect == "Slide Vertical":
            offset = int(height * progress)
            res = Image.new("RGB", (width, height))
            res.paste(img1, (0, -offset))
            res.paste(img2, (0, height - offset))
            return res
        elif effect == "Wipe (Barrido)":
            split = int(width * progress)
            res = img1.copy()
            part2 = img2.crop((0, 0, split, height))
            res.paste(part2, (0, 0))
            return res
        elif effect == "Zoom In":
            factor = 1.0 + (0.2 * progress)
            new_w = int(width / factor)
            new_h = int(height / factor)
            left = (width - new_w) // 2
            top = (height - new_h) // 2
            
            if progress > 0.8:
                alpha = (progress - 0.8) / 0.2
                cropped = img1.crop((left, top, left + new_w, top + new_h))
                resized = cropped.resize((width, height), Image.Resampling.LANCZOS)
                return Image.blend(resized, img2, alpha)
            else:
                cropped = img1.crop((left, top, left + new_w, top + new_h))
                return cropped.resize((width, height), Image.Resampling.LANCZOS)
                
        return img1
