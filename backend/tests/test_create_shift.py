"""Tests for the create-shift Lambda handler."""

import json
import unittest
from decimal import Decimal
from unittest.mock import patch
from uuid import UUID

from backend.src.create_shift.create_shift import lambda_handler, save_shift


class TestCreateShift(unittest.TestCase):
    """Test the behavior of the create-shift Lambda."""

    def make_valid_shift(self):
        """Return valid shift data that individual tests can modify."""
        return {
            "date": "2026-08-13",
            "startTime": "16:00",
            "endTime": "22:30",
            "cashTips": 35.0,
            "creditTips": 120.5,
        }

    @patch("backend.src.create_shift.create_shift.save_shift")
    def test_valid_shift_returns_created_shift(self, mock_save_shift):
        """A valid request should return the newly created shift."""
        shift_data = self.make_valid_shift()
        event = {"body": json.dumps(shift_data)}

        response = lambda_handler(event, None)
        response_body = json.loads(response["body"])
        returned_shift = response_body["shift"]

        self.assertEqual(response["statusCode"], 201)
        self.assertEqual(response["headers"]["Content-Type"], "application/json")
        self.assertEqual(set(response_body), {"shift"})
        self.assertEqual(set(returned_shift), set(shift_data) | {"id"})

        generated_id = returned_shift["id"]
        self.assertEqual(str(UUID(generated_id)), generated_id)

        for field, expected_value in shift_data.items():
            self.assertEqual(returned_shift[field], expected_value)

        mock_save_shift.assert_called_once_with(returned_shift)

    @patch.dict(
        "backend.src.create_shift.create_shift.os.environ",
        {"SHIFTS_TABLE": "test-shifts-table"},
        clear=True,
    )
    @patch("backend.src.create_shift.create_shift.boto3.resource")
    def test_save_shift_writes_item_to_dynamodb(self, mock_resource):
        """Saving a shift should write a DynamoDB-compatible item."""
        shift = {
            "id": "test-shift-id",
            **self.make_valid_shift(),
        }
        mock_dynamodb = mock_resource.return_value
        mock_table = mock_dynamodb.Table.return_value

        save_shift(shift)

        mock_resource.assert_called_once_with("dynamodb")
        mock_dynamodb.Table.assert_called_once_with("test-shifts-table")
        mock_table.put_item.assert_called_once_with(
            Item={
                **shift,
                "cashTips": Decimal("35.0"),
                "creditTips": Decimal("120.5"),
            }
        )

    @patch("backend.src.create_shift.create_shift.save_shift")
    def test_invalid_shift_is_not_saved(self, mock_save_shift):
        """A shift that fails validation should not be written."""
        shift_data = self.make_valid_shift()
        del shift_data["date"]

        response = lambda_handler({"body": json.dumps(shift_data)}, None)

        self.assertEqual(response["statusCode"], 400)
        mock_save_shift.assert_not_called()

    def test_missing_body_returns_bad_request(self):
        """A request without a body should return a clear error."""
        response = lambda_handler({}, None)
        response_body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(response_body, {"error": "Request body is required"})

    def test_malformed_json_returns_bad_request(self):
        """A request with invalid JSON should return a clear error."""
        response = lambda_handler({"body": "{"}, None)
        response_body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(
            response_body,
            {"error": "Request body must contain valid JSON"},
        )

    def test_non_object_json_returns_bad_request(self):
        """A JSON value that is not an object should return a clear error."""
        response = lambda_handler({"body": "[]"}, None)
        response_body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(
            response_body,
            {"error": "Request body must be a JSON object"},
        )

    def test_missing_required_field_returns_bad_request(self):
        """A shift missing a required field should identify that field."""
        shift_data = self.make_valid_shift()
        del shift_data["date"]

        response = lambda_handler({"body": json.dumps(shift_data)}, None)
        response_body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(
            response_body,
            {"error": "Missing required fields: date"},
        )

    def test_invalid_date_format_returns_bad_request(self):
        """A date must use the YYYY-MM-DD format."""
        shift_data = self.make_valid_shift()
        shift_data["date"] = "08/13/2026"

        response = lambda_handler({"body": json.dumps(shift_data)}, None)
        response_body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(
            response_body,
            {"error": "date must use YYYY-MM-DD format"},
        )

    def test_invalid_time_format_returns_bad_request(self):
        """Start and end times must use the 24-hour HH:MM format."""
        for field in ("startTime", "endTime"):
            with self.subTest(field=field):
                shift_data = self.make_valid_shift()
                shift_data[field] = "4:30 PM"

                response = lambda_handler({"body": json.dumps(shift_data)}, None)
                response_body = json.loads(response["body"])

                self.assertEqual(response["statusCode"], 400)
                self.assertEqual(
                    response_body,
                    {"error": f"{field} must use HH:MM format"},
                )

    def test_nonnumeric_tips_return_bad_request(self):
        """Cash and credit tips must be numbers."""
        for field in ("cashTips", "creditTips"):
            with self.subTest(field=field):
                shift_data = self.make_valid_shift()
                shift_data[field] = "twenty"

                response = lambda_handler({"body": json.dumps(shift_data)}, None)
                response_body = json.loads(response["body"])

                self.assertEqual(response["statusCode"], 400)
                self.assertEqual(
                    response_body,
                    {"error": f"{field} must be a number"},
                )

    def test_negative_tips_return_bad_request(self):
        """Cash and credit tips cannot be negative."""
        for field in ("cashTips", "creditTips"):
            with self.subTest(field=field):
                shift_data = self.make_valid_shift()
                shift_data[field] = -1

                response = lambda_handler({"body": json.dumps(shift_data)}, None)
                response_body = json.loads(response["body"])

                self.assertEqual(response["statusCode"], 400)
                self.assertEqual(
                    response_body,
                    {"error": f"{field} cannot be negative"},
                )


if __name__ == "__main__":
    unittest.main()
