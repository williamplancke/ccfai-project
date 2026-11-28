from azure.iot.device import IoTHubDeviceClient, MethodResponse
from azure.storage.blob import BlobClient, ContentSettings
from azure.core.exceptions import AzureError
from pathlib import Path
import dotenv
import os
import time
import mimetypes


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CATPICTURES = PROJECT_ROOT / "Data" / "CatPictures"

RELEVANT_PROPERTIES = ["upload_interval", "config_update_interval"]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def handle_method_request(method_request, iothub_client):
    output_data = {"error": "Unknown method"}
    status = 404

    if method_request.name == "get_catphoto_count":
        output_data = get_catphoto_count()
        status = 200
    response = MethodResponse.create_from_method_request(
        method_request,
        status,
        output_data
    )

    iothub_client.send_method_response(response)

def fetch_desired_properties(iothub_client):
    return iothub_client.get_twin()["desired"]
def fetch_reported_properties(iothub_client):
    return iothub_client.get_twin()["reported"]
def update_config(iothub_client, prev_config):
    config = prev_config
    desired = fetch_desired_properties(iothub_client)
    reported = fetch_reported_properties(iothub_client)
    for sublist in [RELEVANT_PROPERTIES, prev_config.keys()]: # To make sure properties that aren't in the twin config, but are in the local config                                                            # don't get lost.
        for setting in sublist:
            if desired.get(setting, prev_config.get(setting, None)) != reported.get(setting, prev_config.get(setting, None)):
                config[setting] = desired[setting]
    return config
def publish_config(iothub_client, config):
    iothub_client.patch_twin_reported_properties(config)
    print("Published config")
    return
def get_catphotos():
    return list(CATPICTURES.iterdir())

def get_catphoto_count():
    return len(get_catphotos())

def upload_catphotos(iothub_client):
    pictures = get_catphotos()

    if not pictures:
        return

    print(f"\nUploading {len(pictures)} pictures")

    uploaded_count = 0

    for path_to_file in pictures:
        blob_name = path_to_file.name

        # Request temporary access to Blob Storage
        try:
            blob_info = iothub_client.get_storage_info_for_blob(
                blob_name
            )

        except Exception as ex:
            print(f"Failed to obtain SAS for {blob_name}: "
                  f"{type(ex).__name__}")
            continue

        success = False
        status = 500
        description = "Upload failed"

        try:
            sas_url = "https://{}/{}/{}{}".format(
                blob_info["hostName"],
                blob_info["containerName"],
                blob_info["blobName"],
                blob_info["sasToken"]
            )

            print(f"\nUploading file: {path_to_file}")

            content_type = (
                mimetypes.guess_type(blob_name)[0] # Tries to derive the content-type (needed to send a request) from the filename
                or "application/octet-stream"
            )

            # Upload the image
            with BlobClient.from_blob_url(sas_url) as blob_client:
                with path_to_file.open("rb") as f:
                    blob_client.upload_blob(
                        f,
                        overwrite=True,
                        content_settings=ContentSettings(
                            content_type=content_type
                        )
                    )

            success = True
            status = 200
            description = "Upload successful"

        except FileNotFoundError:
            status = 404
            description = "File not found"

        except AzureError as ex:
            status = getattr(ex, "status_code", None) or 500
            description = "Azure Storage error"

        except OSError:
            status = 500
            description = "Local file error"

        finally:
            # Notify IoT Hub regardless of upload outcome
            try:
                iothub_client.notify_blob_upload_status(
                    blob_info["correlationId"],
                    success,
                    status,
                    description
                )

            except Exception as ex:
                success = False
                print(f"Notification failed: "
                      f"{type(ex).__name__}")

        # Only delete the image if upload and notification succeeded
        if success:
            uploaded_count += 1

            try:
                path_to_file.unlink()
                print(f"Successfully uploaded and removed {blob_name}")

            except OSError:
                print(f"Failed to remove local file: {blob_name}")

        else:
            print(f"Upload failed: {blob_name} ({description})")

    print(f"\nSuccessfully uploaded "
          f"{uploaded_count}/{len(pictures)} pictures")


def initialise_config(iothub_client):

    initialisation_time = time.monotonic()

    events = ["catphoto_transmission", "config_update"]

    iothub_client.on_method_request_received = (
        lambda request: handle_method_request(
            request,
            iothub_client
        )
    )

    # Track when each periodic event last occurred
    recent_events = {}
    config = {
        "upload_interval": 5 ,# * 60,
        "config_update_interval": 5 ,# * 60
    }
    for event in events:
        recent_events[event] = initialisation_time

    return iothub_client, recent_events, config


def main(connection_string):
    
    iothub_client = IoTHubDeviceClient.create_from_connection_string(
        connection_string
    )
    try:
        iothub_client.connect()
        print("Connected to Azure IoT Hub")

        iothub_client, recent_events, config = initialise_config(
            iothub_client
        )
        while True:
            if (
                time.monotonic()
                - recent_events["catphoto_transmission"]
                >= config["upload_interval"]
            ):
                upload_catphotos(iothub_client)

                recent_events["catphoto_transmission"] = (
                    time.monotonic()
                )
            if (
                time.monotonic()
                - recent_events["config_update"]
                >= config["config_update_interval"]
            ):
                print("Config before update:",config)
                config = update_config(iothub_client, config)
                print("Config after update:",config)
                publish_config(iothub_client, config)
                recent_events["config_update"] = (
                    time.monotonic()
                )
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down IoT device")

    finally:
        iothub_client.shutdown()
        print("Disconnected from Azure IoT Hub")


if __name__ == "__main__":
    dotenv.load_dotenv(PROJECT_ROOT / ".env")

    connection_string = os.environ.get(
        "IOTDEVICE_CONNECTION_STRING"
    )

    if not connection_string:
        raise RuntimeError("Missing IoT Hub connection string")

    CATPICTURES.mkdir(parents=True, exist_ok=True)

    main(connection_string)
