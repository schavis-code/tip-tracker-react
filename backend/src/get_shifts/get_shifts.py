"""Lambda handler for retrieving restaurant shifts."""

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


# Read every page of shifts from the DynamoDB table.
def get_all_shifts():
    """Retrieve every shift from the configured DynamoDB table."""
    # Get the deployed table's physical name from the Lambda environment.
    table_name = os.environ["SHIFTS_TABLE"]

    # Create the DynamoDB connection and a paginator for tables over one response page.
    dynamodb = boto3.resource("dynamodb")
    paginator = dynamodb.meta.client.get_paginator("scan")
    shifts = []

    # Add the items from each DynamoDB page to one list.
    for page in paginator.paginate(TableName=table_name):
        shifts.extend(page.get("Items", []))

    return shifts


# Coordinate retrieving, sorting, and returning the shifts for the GET request.
def lambda_handler(event, context):
    """Return all saved shifts, ordered from newest to oldest."""
    # Retrieve the stored shifts before preparing the HTTP response.
    shifts = get_all_shifts()

    # Sort by date and clock-in time so the newest shifts appear first.
    shifts.sort(
        key=lambda shift: (shift.get("date", ""), shift.get("startTime", "")),
        reverse=True,
    )

    # Return the completed list to API Gateway as JSON.
    return create_response(200, {"shifts": shifts})
