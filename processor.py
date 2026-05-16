import os
import cv2
import numpy as np
from PIL import Image
from PyQt6.QtCore import QThread, pyqtSignal

class RenderThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.fps = 30 # Fotogramas por segundo para el MP4
        self.transition_time = 0.5 # Segundos que dura la transición

    def run(self):
        try:
            self.progress.emit(0, "Preparando imágenes en memoria...")
            if not self.model.images:
                self.finished.emit(False, "No hay imágenes para procesar.")
                return

            # Cargar imágenes
            pil_images = []
            for slide in self.model.images:
                if os.path.exists(slide.file_path):
                    # Forzar conversión a RGB
                    img = Image.open(slide.file_path).convert("RGB")
                    pil_images.append((img, slide.duration_custom))

            if not pil_images:
                self.finished.emit(False, "Las rutas de las imágenes no son válidas.")
                return

            # Estandarizar resolución (basado en la primera imagen)
            base_width, base_height = pil_images[0][0].size
            
            sequence = []
            total_slides = len(pil_images)
            effect = self.model.transition_effect
            trans_frames_count = int(self.transition_time * self.fps) if effect != "Ninguno" else 0

            # --- GENERACIÓN DE FRAMES ---
            for i in range(total_slides):
                self.progress.emit(int((i / total_slides) * 40), f"Calculando frame {i+1} de {total_slides}...")
                current_img, duration = pil_images[i]
                
                # Resize if needed
                if current_img.size != (base_width, base_height):
                    current_img = current_img.resize((base_width, base_height), Image.Resampling.LANCZOS)
                
                # Frames estáticos (Descontamos el tiempo de la transición al final)
                static_frames = int(duration * self.fps) - (trans_frames_count if i < total_slides - 1 else 0)
                if static_frames < 1: 
                    static_frames = 1
                
                # Agregar la imagen sin alterar
                for _ in range(static_frames):
                    sequence.append(current_img.copy())
                
                # Generar transición hacia el siguiente slide
                if effect != "Ninguno" and i < total_slides - 1:
                    next_img, _ = pil_images[i+1]
                    if next_img.size != (base_width, base_height):
                        next_img = next_img.resize((base_width, base_height), Image.Resampling.LANCZOS)
                        
                    for f in range(trans_frames_count):
                        prog = f / float(trans_frames_count)
                        frame = self.apply_transition(current_img, next_img, effect, prog, base_width, base_height)
                        sequence.append(frame)
                        
            # --- EXPORTACIÓN ---
            output_dir = self.model.save_location
            proj_name = self.model.project_name.replace(" ", "_")
            msg_final = ""

            # 1. MP4
            if self.model.export_mp4:
                mp4_path = os.path.join(output_dir, f"{proj_name}.mp4")
                self.progress.emit(45, "Codificando Video MP4 (Esto puede tardar)...")
                
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(mp4_path, fourcc, self.fps, (base_width, base_height))
                
                total_frames = len(sequence)
                for idx, frame in enumerate(sequence):
                    if idx % 15 == 0:
                        percent = 45 + int((idx / total_frames) * 25)
                        self.progress.emit(percent, f"Escribiendo video MP4 ({idx}/{total_frames})...")
                    
                    # Convertir de PIL (RGB) a OpenCV (BGR)
                    cv_img = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
                    out.write(cv_img)
                out.release()
                msg_final += f"✅ Video MP4 creado.\n"

            # 2. GIF
            if self.model.export_gif:
                gif_path = os.path.join(output_dir, f"{proj_name}.gif")
                self.progress.emit(75, "Compilando archivo GIF...")
                
                # Para evitar un GIF gigante, bajamos los FPS y la resolución
                skip_frames = 3 # Bajamos a ~10fps
                gif_sequence = sequence[::skip_frames]
                gif_duration = int(1000 / (self.fps / skip_frames)) # ms por frame
                
                # Escalar resolución al 50%
                gif_w, gif_h = int(base_width * 0.5), int(base_height * 0.5)
                self.progress.emit(85, "Redimensionando frames para el GIF...")
                gif_sequence = [img.resize((gif_w, gif_h), Image.Resampling.LANCZOS) for img in gif_sequence]
                
                self.progress.emit(95, "Guardando GIF en disco...")
                gif_sequence[0].save(
                    gif_path,
                    save_all=True,
                    append_images=gif_sequence[1:],
                    duration=gif_duration,
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
        """Lógica matemática de las transiciones visuales"""
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
            factor = 1.0 + (0.2 * progress) # Zoom hasta 1.2x
            new_w = int(width / factor)
            new_h = int(height / factor)
            left = (width - new_w) // 2
            top = (height - new_h) // 2
            
            # Crossfade final para no cortar brusco
            if progress > 0.8:
                alpha = (progress - 0.8) / 0.2
                cropped = img1.crop((left, top, left + new_w, top + new_h))
                resized = cropped.resize((width, height), Image.Resampling.LANCZOS)
                return Image.blend(resized, img2, alpha)
            else:
                cropped = img1.crop((left, top, left + new_w, top + new_h))
                return cropped.resize((width, height), Image.Resampling.LANCZOS)
                
        return img1
