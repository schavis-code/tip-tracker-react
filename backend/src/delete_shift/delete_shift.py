"""Lambda handler for deleting a restaurant shift."""

# Import Python tools for JSON responses, environment variables, and DynamoDB numbers.
import json
import os
from decimal import Decimal

# Import the AWS SDK used to communicate with DynamoDB.
import boto3


# Convert DynamoDB numbers into types that json.dumps can serialize.
def decimal_to_number(value):
    """Convert a DynamoDB Decimal into a JSON-compatible number."""
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)

    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


# Build the response format expected by API Gateway and include the CORS header.
def create_response(status_code, body):
    """Create an API Gateway-compatible HTTP response."""
    allowed_origin = os.environ.get("ALLOWED_ORIGIN", "http://localhost:5173")

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": allowed_origin,
        },
        "body": json.dumps(body, default=decimal_to_number),
    }


# Delete one shift and ask DynamoDB to return the item that was removed.
def delete_shift(shift_id):
    """Delete and return the shift with the supplied ID."""
    # Get the deployed table's physical name from the Lambda environment.
    table_name = os.environ["SHIFTS_TABLE"]

    # Connect to the table and delete the item with the matching partition key.
    table = boto3.resource("dynamodb").Table(table_name)
    response = table.delete_item(
        Key={"id": shift_id},
        ReturnValues="ALL_OLD",
    )

    # Attributes contains the deleted shift, but is absent when no item matched.
    return response.get("Attributes")


# Coordinate validating the URL ID, deleting the shift, and returning an HTTP response.
def lambda_handler(event, context):
    """Delete a shift identified by the API path parameter."""
    # API Gateway places the {id} part of /shifts/{id} in pathParameters.
    path_parameters = event.get("pathParameters") or {}
    shift_id = path_parameters.get("id")

    # Reject requests that do not include a usable shift ID.
    if not isinstance(shift_id, str) or not shift_id.strip():
        return create_response(400, {"error": "Shift ID is required"})

    # Remove accidental surrounding spaces before using the ID as the table key.
    shift_id = shift_id.strip()
    deleted_shift = delete_shift(shift_id)

    # Return 404 when DynamoDB reports that no matching item existed.
    if deleted_shift is None:
        return create_response(404, {"error": "Shift not found"})

    # Return the deleted shift so the frontend knows exactly what was removed.
    return create_response(200, {"shift": deleted_shift})
