from azure.iot.device import IoTHubDeviceClient
import dotenv
from pathlib import Path
import os, time
import asyncio
async def handle_method_request(method_request):
    if method_request.method_name == "get_catphoto_count":
        output_data = get_catphoto_count()
    return output_data
def get_catphoto_count():
    return len(os.listdir(PROJECT_ROOT / "Data" / "CatPictures"))
async def main(connection_string):
    iothub_client = IoTHubDeviceClient.create_from_connection_string(connection_string)
    try:
        iothub_client.connect()
        iothub_client.on_method_request_received = handle_method_request
        while True:
            time.sleep(3)
    except KeyboardInterrupt:
        iothub_client.disconnect()
        raise

    return

if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    found_env_file = dotenv.load_dotenv(PROJECT_ROOT / ".env")
    assert found_env_file
    asyncio.run(main(
        connection_string=os.environ.get("IOTDEVICE_CONNECTION_STRING")
    ))