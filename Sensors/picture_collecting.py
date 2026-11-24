import picamera2
import time
local_state = "off"
local_interval = 5
def toggle_state(state: str) -> str:
    state = state.lower().strip()
    if state != "on" and state != "off":
        raise ValueError("Requested state must either be 'on' or 'off'")
    local_state = state
    return state
def change_interval(interval: int) -> int:
    if not isinstance(interval, int):
        raise TypeError("Requested interval must be an integer")
    if interval <= 0:
        raise ValueError("Requested interval must be greater than 0")
    local_interval = interval
    return interval
def main():
    camera = picamera2.Picamera2()
    config = camera.create_video_configuration(
        main={"size": (640, 480), "format": "RGB888"}
    )
    camera.configure(config)
    camera.start()
    while True:
        if local_state == "on":
            camera.capture_file(f"Data/Pictures/{time.time_ns()}.jpg")
            time.sleep(local_interval)
if __name__ == "__main__":
    main()