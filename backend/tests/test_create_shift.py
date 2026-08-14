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


if __name__ == "__main__":
    unittest.main()
