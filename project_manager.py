import os
import json
import zipfile
import shutil
from model import AppModel, SlideImage

class ProjectManager:
    @staticmethod
    def save_project(model: AppModel, filepath: str = None) -> str:
        """Guarda el proyecto en un contenedor .vsp (ZIP)"""
        if filepath is None:
            filepath = model.project_filepath
            
        if not filepath:
            # Auto-save fallback if no manual save was done yet
            if model.save_location and model.project_name:
                filename = f"{model.project_name.replace(' ', '_')}.vsp"
                filepath = os.path.join(model.save_location, filename)
            else:
                return "" # Nowhere to save
                
        # Preparar data
        data = {
            "project_name": model.project_name,
            "video_path": model.video_path,
            "save_location": model.save_location,
            "export_mp4": model.export_mp4,
            "export_gif": model.export_gif,
            "transition_effect": getattr(model, 'transition_effect', 'Ninguno'),
            "images": []
        }
        
        temp_filepath = filepath + ".tmp"
        
        try:
            with zipfile.ZipFile(temp_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for slide in model.images:
                    if os.path.exists(slide.file_path):
                        arcname = f"slides/{os.path.basename(slide.file_path)}"
                        zipf.write(slide.file_path, arcname)
                        
                        data["images"].append({
                            "timestamp": slide.timestamp,
                            "duration_custom": slide.duration_custom,
                            "arcname": arcname
                        })
                        
                # Guardar el JSON dentro del zip
                json_data = json.dumps(data, indent=4)
                zipf.writestr("project_data.json", json_data)
                
            # Mover temporal al destino final
            if os.path.exists(filepath):
                os.remove(filepath)
            os.rename(temp_filepath, filepath)
            
            model.project_filepath = filepath
            return filepath
        except Exception as e:
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            print(f"Error saving project: {e}")
            return ""

    @staticmethod
    def load_project(filepath: str) -> AppModel:
        """Carga un proyecto desde un contenedor .vsp"""
        import tempfile
        import uuid
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Project file not found: {filepath}")
            
        model = AppModel()
        model.project_filepath = filepath
        
        extract_dir = os.path.join(tempfile.gettempdir(), "video_slides_app", f"vsp_extract_{uuid.uuid4().hex[:8]}")
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(filepath, 'r') as zipf:
            zipf.extractall(extract_dir)
            
        json_path = os.path.join(extract_dir, "project_data.json")
        if not os.path.exists(json_path):
            shutil.rmtree(extract_dir, ignore_errors=True)
            raise ValueError("Invalid project file: missing project_data.json")
            
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        model.project_name = data.get("project_name", "Proyecto_Recuperado")
        model.video_path = data.get("video_path", "")
        
        # Definir nueva carpeta de guardado temporal si no existe o usar la original
        model.save_location = data.get("save_location", os.path.dirname(filepath))
        
        model.export_mp4 = data.get("export_mp4", True)
        model.export_gif = data.get("export_gif", True)
        model.transition_effect = data.get("transition_effect", "Ninguno")
        
        model.images = []
        import tempfile
        final_dir = os.path.join(tempfile.gettempdir(), "video_slides_app", model.project_name.replace(' ', '_'))
        os.makedirs(final_dir, exist_ok=True)
        
        for img_data in data.get("images", []):
            arcname = img_data.get("arcname")
            extracted_path = os.path.join(extract_dir, arcname)
            
            final_img_path = os.path.join(final_dir, os.path.basename(arcname))
            if os.path.exists(extracted_path):
                shutil.copy(extracted_path, final_img_path)
                
            slide = SlideImage(
                timestamp=img_data.get("timestamp", "00:00"),
                duration_custom=img_data.get("duration_custom", 2.0),
                file_path=final_img_path
            )
            model.images.append(slide)
            
        shutil.rmtree(extract_dir, ignore_errors=True)
        return model
