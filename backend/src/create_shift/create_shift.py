"""Lambda handler for creating a restaurant shift."""

import json
import os
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import boto3


REQUIRED_FIELDS = (
    "date",
    "startTime",
    "endTime",
    "cashTips",
    "creditTips",
)


def create_response(status_code, body):
    """Create an API Gateway-compatible HTTP response."""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def matches_format(value, expected_format):
    """Return whether a string exactly matches a date or time format."""
    if not isinstance(value, str):
        return False

    try:
        parsed_value = datetime.strptime(value, expected_format)
    except ValueError:
        return False

    return parsed_value.strftime(expected_format) == value


def validate_shift(shift):
    """Return an error message when shift data is invalid."""
    missing_fields = [field for field in REQUIRED_FIELDS if field not in shift]

    if missing_fields:
        return f"Missing required fields: {', '.join(missing_fields)}"

    if not matches_format(shift["date"], "%Y-%m-%d"):
        return "date must use YYYY-MM-DD format"

    for field in ("startTime", "endTime"):
        if not matches_format(shift[field], "%H:%M"):
            return f"{field} must use HH:MM format"

    for field in ("cashTips", "creditTips"):
        if type(shift[field]) not in (int, float):
            return f"{field} must be a number"

        if shift[field] < 0:
            return f"{field} cannot be negative"

    return None


def save_shift(shift):
    """Save a shift in the DynamoDB table configured for this Lambda."""
    table_name = os.environ["SHIFTS_TABLE"]
    table = boto3.resource("dynamodb").Table(table_name)
    item = {
        **shift,
        "cashTips": Decimal(str(shift["cashTips"])),
        "creditTips": Decimal(str(shift["creditTips"])),
    }

    table.put_item(Item=item)


def lambda_handler(event, context):
    """Validate incoming data and return a newly created shift."""
    if not event.get("body"):
        return create_response(400, {"error": "Request body is required"})

    try:
        request_body = json.loads(event["body"])
    except (json.JSONDecodeError, TypeError):
        return create_response(400, {"error": "Request body must contain valid JSON"})

    if not isinstance(request_body, dict):
        return create_response(400, {"error": "Request body must be a JSON object"})

    validation_error = validate_shift(request_body)

    if validation_error:
        return create_response(400, {"error": validation_error})

    shift = {
        "id": str(uuid4()),
        "date": request_body["date"],
        "startTime": request_body["startTime"],
        "endTime": request_body["endTime"],
        "cashTips": request_body["cashTips"],
        "creditTips": request_body["creditTips"],
    }

    save_shift(shift)

    return create_response(201, {"shift": shift})
