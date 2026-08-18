"""Tests for the create-shift Lambda handler."""

import json
import unittest
from uuid import UUID

from backend.src.create_shift.app import lambda_handler


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

    def test_valid_shift_returns_created_shift(self):
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
