from ultralytics import YOLO
import shutil, torch
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
def get_model():
    base_model = YOLO("yolo26n.pt") # Smallest available model
    base_model.export(format="torch", quantize=8)
    quantized_path = PROJECT_ROOT / "Inference" / "Models" / "yolo26n-Q8.pt"
    shutil.move("yolo26n.pt", quantized_path)
    return torch.load(quantized_path, weights_only=False)

def check_cat_presence(model, image_path):
    model.predict(image_path)