from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class SlideImage:
    timestamp: str
    duration_custom: float
    file_path: str

@dataclass
class AppModel:
    video_path: Optional[str] = None
    project_name: str = ""
    save_location: Optional[str] = None
    images: List[SlideImage] = field(default_factory=list)
    export_gif: bool = True
    export_mp4: bool = False
    transition_effect: str = "Fade (Fundido)"
