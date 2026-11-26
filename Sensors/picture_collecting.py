import picamera2
import time
from Data.storage_management import delete_old_assets, get_data
from Inference.cat_detection import check_cat_presence
AMOUNT_OF_DATA_KEPT = 20
KEEP_NEW_DATA = True
local_state = "off"
local_interval = 5
def toggle_state(state: str) -> str:
    global local_state
    state = state.lower().strip()
    if state != "on" and state != "off":
        raise ValueError("Requested state must either be 'on' or 'off'")
    local_state = state
    return state
def change_interval(interval: int) -> int:
    global local_interval
    if not isinstance(interval, int):
        raise TypeError("Requested interval must be an integer")
    if interval <= 0:
        raise ValueError("Requested interval must be greater than 0")
    local_interval = interval
    return interval
def main(model):
    camera = picamera2.Picamera2()
    config = camera.create_still_configuration(
        main={"size": (640, 480), "format": "RGB888"},
        buffer_count=2
    )
    camera.configure(config)
    camera.start()
    while True:
        if local_state == "on":
            filename = f"Data/Pictures/{time.time_ns()}.jpg"
            camera.capture_file(filename)
            prediction = check_cat_presence(model, filename)
            print(f"Prediction: {prediction}")
            if len(get_data("Pictures")) > AMOUNT_OF_DATA_KEPT:
                delete_old_assets("Pictures", AMOUNT_OF_DATA_KEPT)
        time.sleep(local_interval)
if __name__ == "__main__":
    main()