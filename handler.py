from Sensors.picture_collecting import main as collect_pictures
from Sensors.picture_collecting import toggle_state, change_interval
from Inference.cat_detection import get_model

model = get_model()

toggle_state("on")
change_interval(3)
collect_pictures(model)