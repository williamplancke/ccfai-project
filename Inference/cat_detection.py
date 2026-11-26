from ultralytics import YOLO
from pathlib import Path
from executorch.runtime import Runtime
import executorch
PROJECT_ROOT = Path(__file__).resolve().parent.parent
def get_model():
    return YOLO(
        PROJECT_ROOT / "Inference" / "Models" / "yolo26n_executorch_model",
        task="detect"
    )

def check_cat_presence(model: YOLO, image_path):
    results = model.predict(
        source=image_path,
        classes=[15],
        conf=0.5,
        verbose=False
    )
    return results[0]