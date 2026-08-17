"""Tests for the create-shift Lambda handler."""

import json
import unittest
from uuid import UUID

from backend.src.create_shift.app import lambda_handler


class TestCreateShift(unittest.TestCase):
    """Test the behavior of the create-shift Lambda."""

    def test_valid_shift_returns_created_shift(self):
        """A valid request should return the newly created shift."""
        shift_data = {
            "date": "2026-08-13",
            "startTime": "16:00",
            "endTime": "22:30",
            "cashTips": 35.0,
            "creditTips": 120.5,
        }
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


if __name__ == "__main__":
    unittest.main()
