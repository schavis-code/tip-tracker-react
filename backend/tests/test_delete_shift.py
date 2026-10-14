"""Tests for the delete-shift Lambda handler."""

# Import Python tools for reading JSON, organizing tests, and creating DynamoDB numbers.
import json
import unittest
from decimal import Decimal

# Import patch so the tests can replace AWS resources with controlled mock objects.
from unittest.mock import patch

# Import the delete-shift functions that the tests will exercise.
from backend.src.delete_shift.delete_shift import delete_shift, lambda_handler


# Group all delete-shift Lambda tests into one unittest test case.
class TestDeleteShift(unittest.TestCase):
    """Test the behavior of the delete-shift Lambda."""

    # Supply a fake table name and replace boto3 so this test never contacts AWS.
    @patch.dict(
        "backend.src.delete_shift.delete_shift.os.environ",
        {"SHIFTS_TABLE": "test-shifts-table"},
        clear=True,
    )
    @patch("backend.src.delete_shift.delete_shift.boto3.resource")
    def test_delete_shift_returns_removed_item(self, mock_resource):
        """The DynamoDB helper should delete and return the matching shift."""
        # Configure the fake table to return the item that existed before deletion.
        deleted_shift = {"id": "shift-1", "date": "2026-10-14"}
        mock_table = mock_resource.return_value.Table.return_value
        mock_table.delete_item.return_value = {"Attributes": deleted_shift}

        # Run the helper with a controlled shift ID.
        result = delete_shift("shift-1")

        # Verify the correct table, key, and return-value option were used.
        self.assertEqual(result, deleted_shift)
        mock_resource.assert_called_once_with("dynamodb")
        mock_resource.return_value.Table.assert_called_once_with("test-shifts-table")
        mock_table.delete_item.assert_called_once_with(
            Key={"id": "shift-1"},
            ReturnValues="ALL_OLD",
        )

    # Set the allowed browser origin and replace the DynamoDB deletion helper.
    @patch.dict(
        "backend.src.delete_shift.delete_shift.os.environ",
        {"ALLOWED_ORIGIN": "http://localhost:5173"},
        clear=True,
    )
    @patch("backend.src.delete_shift.delete_shift.delete_shift")
    def test_lambda_handler_returns_deleted_shift(self, mock_delete_shift):
        """A valid ID should return the deleted shift in a successful response."""
        # Return a deleted item containing DynamoDB Decimal tip values.
        mock_delete_shift.return_value = {
            "id": "shift-1",
            "date": "2026-10-14",
            "cashTips": Decimal("35"),
            "creditTips": Decimal("120.50"),
        }

        # Run the handler with the path format supplied by API Gateway.
        response = lambda_handler({"pathParameters": {"id": "shift-1"}}, None)
        response_body = json.loads(response["body"])

        # Verify the HTTP response, CORS header, ID, and number conversion.
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response["headers"]["Content-Type"], "application/json")
        self.assertEqual(
            response["headers"]["Access-Control-Allow-Origin"],
            "http://localhost:5173",
        )
        self.assertEqual(response_body["shift"]["id"], "shift-1")
        self.assertEqual(response_body["shift"]["cashTips"], 35)
        self.assertEqual(response_body["shift"]["creditTips"], 120.5)
        mock_delete_shift.assert_called_once_with("shift-1")

    # Replace the delete helper so invalid requests cannot accidentally call it.
    @patch("backend.src.delete_shift.delete_shift.delete_shift")
    def test_lambda_handler_rejects_missing_shift_id(self, mock_delete_shift):
        """A request without a usable path ID should return 400."""
        # Check the common missing and blank path-parameter shapes.
        invalid_events = [
            {},
            {"pathParameters": None},
            {"pathParameters": {}},
            {"pathParameters": {"id": "   "}},
        ]

        for event in invalid_events:
            with self.subTest(event=event):
                response = lambda_handler(event, None)
                self.assertEqual(response["statusCode"], 400)
                self.assertEqual(
                    json.loads(response["body"]),
                    {"error": "Shift ID is required"},
                )

        mock_delete_shift.assert_not_called()

    # Make the delete helper report that DynamoDB had no matching item.
    @patch(
        "backend.src.delete_shift.delete_shift.delete_shift",
        return_value=None,
    )
    def test_lambda_handler_returns_not_found_for_unknown_id(self, mock_delete_shift):
        """An unknown shift ID should return 404."""
        # Run the handler with a validly shaped ID that does not exist.
        response = lambda_handler({"pathParameters": {"id": "missing-id"}}, None)

        # Verify the response distinguishes a missing shift from a successful delete.
        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(json.loads(response["body"]), {"error": "Shift not found"})
        mock_delete_shift.assert_called_once_with("missing-id")


# Allow this test file to be run directly with Python.
if __name__ == "__main__":
    unittest.main()
