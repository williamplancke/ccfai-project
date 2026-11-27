
import azure.functions as func
from azure.iot.hub import IoTHubRegistryManager
from azure.iot.hub.models import Twin, TwinProperties
import os
import json
import logging


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="update_device_twin/{device_id}", methods=["PATCH"])
def update_device_twin(req: func.HttpRequest) -> func.HttpResponse:

    device_id = req.route_params.get("device_id")

    try:
        desired_properties = req.get_json()

    except ValueError:
        return func.HttpResponse(
            "Invalid JSON body",
            status_code=400
        )

    if not isinstance(desired_properties, dict):
        return func.HttpResponse(
            "Request body must be a JSON dictionary",
            status_code=400
        )

    try:
        registry_manager = IoTHubRegistryManager.from_connection_string(
            os.environ["IOTHUB_SERVICE_CONNECTION_STRING"]
        )

        twin = registry_manager.get_twin(device_id)

        twin_patch = Twin(
            properties=TwinProperties(
                desired=desired_properties
            )
        )

        updated_twin = registry_manager.update_twin(
            device_id,
            twin_patch,
            twin.etag
        )

        return func.HttpResponse(
            json.dumps(updated_twin.properties.desired),
            status_code=200,
            mimetype="application/json"
        )

    except Exception:
        logging.exception("Failed to update device twin")

        return func.HttpResponse(
            "Failed to update device twin",
            status_code=500
        )
