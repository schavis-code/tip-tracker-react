"""Tests for the get-shifts Lambda handler."""

# Import Python tools for reading JSON, organizing tests, and creating DynamoDB numbers.
import json
import unittest
from decimal import Decimal

# Import patch so the tests can replace AWS resources with controlled mock objects.
from unittest.mock import patch

# Import the get-shifts functions that the tests will exercise.
from backend.src.get_shifts.get_shifts import (
    decimal_to_number,
    get_all_shifts,
    lambda_handler,
)


# Group all get-shifts Lambda tests into one unittest test case.
class TestGetShifts(unittest.TestCase):
    """Test the behavior of the get-shifts Lambda."""

    def test_decimal_to_number_converts_dynamodb_numbers(self):
        """Whole and fractional Decimals should become JSON-compatible numbers."""
        # Verify whole Decimals become integers and fractional Decimals become floats.
        self.assertEqual(decimal_to_number(Decimal("35")), 35)
        self.assertEqual(decimal_to_number(Decimal("120.50")), 120.5)

    # Supply a fake table name and replace boto3 so this test never contacts AWS.
    @patch.dict(
        "backend.src.get_shifts.get_shifts.os.environ",
        {"SHIFTS_TABLE": "test-shifts-table"},
        clear=True,
    )
    @patch("backend.src.get_shifts.get_shifts.boto3.resource")
    def test_get_all_shifts_combines_scan_pages(self, mock_resource):
        """Every DynamoDB scan page should be combined into one shift list."""
        # Create three sample shifts that will be returned across two pages.
        first_shift = {"id": "shift-1", "date": "2026-10-10"}
        second_shift = {"id": "shift-2", "date": "2026-10-11"}
        third_shift = {"id": "shift-3", "date": "2026-10-12"}
        mock_dynamodb = mock_resource.return_value
        mock_client = mock_dynamodb.meta.client
        mock_paginator = mock_client.get_paginator.return_value
        mock_paginator.paginate.return_value = [
            {"Items": [first_shift, second_shift]},
            {"Items": [third_shift]},
        ]

        # Run the function using the controlled paginator responses.
        shifts = get_all_shifts()

        # Verify all pages were combined and DynamoDB received the expected settings.
        self.assertEqual(shifts, [first_shift, second_shift, third_shift])
        mock_resource.assert_called_once_with("dynamodb")
        mock_client.get_paginator.assert_called_once_with("scan")
        mock_paginator.paginate.assert_called_once_with(
            TableName="test-shifts-table"
        )

    # Supply a fake table name and make the mocked scan return no items.
    @patch.dict(
        "backend.src.get_shifts.get_shifts.os.environ",
        {"SHIFTS_TABLE": "test-shifts-table"},
        clear=True,
    )
    @patch("backend.src.get_shifts.get_shifts.boto3.resource")
    def test_get_all_shifts_returns_empty_list_for_empty_table(self, mock_resource):
        """An empty DynamoDB table should produce an empty list."""
        mock_paginator = (
            mock_resource.return_value.meta.client.get_paginator.return_value
        )
        mock_paginator.paginate.return_value = [{"Items": []}]

        # Run the function and verify an empty table produces an empty list.
        shifts = get_all_shifts()

        self.assertEqual(shifts, [])

    # Set the allowed browser origin and replace the DynamoDB-reading function.
    @patch.dict(
        "backend.src.get_shifts.get_shifts.os.environ",
        {"ALLOWED_ORIGIN": "http://localhost:5173"},
        clear=True,
    )
    @patch("backend.src.get_shifts.get_shifts.get_all_shifts")
    def test_lambda_handler_returns_sorted_json_response(self, mock_get_all_shifts):
        """The handler should return newest shifts first in an API response."""
        # Return unsorted shifts with DynamoDB Decimal tip values.
        mock_get_all_shifts.return_value = [
            {
                "id": "older-shift",
                "date": "2026-10-10",
                "startTime": "16:00",
                "cashTips": Decimal("35"),
                "creditTips": Decimal("120.50"),
            },
            {
                "id": "newer-late-shift",
                "date": "2026-10-12",
                "startTime": "18:00",
                "cashTips": Decimal("42.25"),
                "creditTips": Decimal("100"),
            },
            {
                "id": "newer-early-shift",
                "date": "2026-10-12",
                "startTime": "10:00",
                "cashTips": Decimal("20"),
                "creditTips": Decimal("80.75"),
            },
        ]

        # Run the handler and convert its JSON body back into a Python dictionary.
        response = lambda_handler({}, None)
        response_body = json.loads(response["body"])

        # Verify the HTTP response, CORS header, sorting, and number conversion.
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response["headers"]["Content-Type"], "application/json")
        self.assertEqual(
            response["headers"]["Access-Control-Allow-Origin"],
            "http://localhost:5173",
        )
        self.assertEqual(
            [shift["id"] for shift in response_body["shifts"]],
            ["newer-late-shift", "newer-early-shift", "older-shift"],
        )
        self.assertEqual(response_body["shifts"][0]["cashTips"], 42.25)
        self.assertEqual(response_body["shifts"][0]["creditTips"], 100)

    # Replace the DynamoDB-reading function with an empty result.
    @patch("backend.src.get_shifts.get_shifts.get_all_shifts", return_value=[])
    def test_lambda_handler_returns_success_for_empty_table(self, mock_get_all_shifts):
        """An empty table should still return a successful response."""
        # Run the handler and inspect the returned JSON body.
        response = lambda_handler({}, None)
        response_body = json.loads(response["body"])

        # Verify an empty table is a successful response rather than an error.
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response_body, {"shifts": []})
        mock_get_all_shifts.assert_called_once_with()


# Allow this test file to be run directly with Python.
if __name__ == "__main__":
    unittest.main()
