import unittest
from unittest.mock import Mock, patch

from appwrite_compat import normalize_limit
from guitar_service import GuitarPracticeService


class GuitarPracticeRecordsTests(unittest.TestCase):
    def setUp(self):
        self.service = GuitarPracticeService.__new__(GuitarPracticeService)
        self.service.db = Mock()
        self.service.database_id = "db"
        self.service.table_id = "guitarpractice"
        self.service.practice_records_table_id = "guitarPracticeRecords"

    def rows(self, records):
        self.service.db.list_rows.return_value = {"rows": records}

    def test_linked_session_and_actual_duration_seconds(self):
        self.rows([{
            "$id": "r1", "sessionId": "s1", "practiceDate": "2026-10-13",
            "startedAt": "2026-10-13T09:00:00.000Z", "duration": 1200,
            "completed": True,
        }])
        self.service._get = Mock(return_value={
            "$id": "s1", "sessionName": "Fingerstyle", "category": "Fingerstyle",
            "level": "Beginner", "suggestedTime": 1800, "duration": 3600,
            "link": "https://example.com", "dailyPracticeTime": 4321,
        })
        result = self.service.list_practice_records()
        record = result["records"][0]
        self.assertEqual(record["duration"], 1200)
        self.assertEqual(record["session"]["suggestedTime"], 1800)
        self.assertNotIn("dailyPracticeTime", record["session"])
        self.assertEqual(result["totalDurationSeconds"], 1200)
        self.service._get.assert_called_once_with("s1")

    def test_general_practice_returns_null_without_lookup(self):
        self.rows([{"$id": "r", "sessionId": "general-practice", "duration": 900}])
        self.service._get = Mock()
        result = self.service.list_practice_records()
        self.assertIsNone(result["records"][0]["session"])
        self.service._get.assert_not_called()

    def test_missing_curriculum_session_does_not_drop_record(self):
        self.rows([{"$id": "r", "sessionId": "gone", "duration": 20}])
        self.service._get = Mock(side_effect=Exception("Row not found"))
        result = self.service.list_practice_records()
        self.assertEqual(result["recordCount"], 1)
        self.assertIsNone(result["records"][0]["session"])

    def test_filters_and_nullable_false(self):
        self.rows([])
        with patch("guitar_service.Query.equal", side_effect=lambda k, v: (k, v)), patch(
            "guitar_service.Query.order_desc", side_effect=lambda k: ("order", k)
        ), patch("guitar_service.Query.limit", side_effect=lambda n: ("limit", n)):
            result = self.service.list_practice_records(
                session_id="s", practice_date="2026-10-13", completed=False
            )
        query_list = self.service.db.list_rows.call_args.kwargs["queries"]
        self.assertIn(("sessionId", "s"), query_list)
        self.assertIn(("practiceDate", "2026-10-13"), query_list)
        self.assertIn(("completed", False), query_list)
        self.assertIs(result["filters"]["completed"], False)

    def test_practice_date_validation(self):
        with self.assertRaises(ValueError):
            self.service.list_practice_records(practice_date="13-10-2026")

    def test_limit_defaults_and_caps(self):
        self.assertEqual(normalize_limit(None, default=25), 25)
        self.assertEqual(normalize_limit(1000, default=25), 100)
        self.assertEqual(normalize_limit(-2, default=25), 1)
        self.rows([])
        with patch("guitar_service.Query.order_desc", side_effect=lambda k: ("order", k)), patch(
            "guitar_service.Query.limit", side_effect=lambda n: ("limit", n)
        ):
            result = self.service.list_practice_records(limit=999)
        self.assertEqual(result["filters"]["limit"], 100)
        self.assertIn(("limit", 100), self.service.db.list_rows.call_args.kwargs["queries"])

    def test_duration_sum_is_for_returned_rows_only(self):
        self.rows([
            {"$id": "r1", "sessionId": "general-practice", "duration": 10},
            {"$id": "r2", "sessionId": "general-practice", "duration": 15},
        ])
        result = self.service.list_practice_records(limit=2)
        self.assertEqual(result["recordCount"], 2)
        self.assertEqual(result["totalDurationSeconds"], 25)

    def test_retrieval_never_mutates_appwrite_or_daily_practice_time(self):
        self.rows([{"$id": "r", "sessionId": "general-practice", "duration": 10}])
        self.service.list_practice_records()
        self.service.db.create_row.assert_not_called()
        self.service.db.update_row.assert_not_called()
        self.service.db.delete_row.assert_not_called()

    def test_existing_curriculum_list_unchanged(self):
        self.service._query_practice = Mock(return_value=[{"$id": "s", "dailyPracticeTime": 5}])
        self.assertEqual(self.service.list_practice(completed=False, limit=10), {
            "documentType": "guitarPractice",
            "filters": {"completed": False, "limit": 10},
            "practiceCount": 1,
            "practices": [{"$id": "s", "dailyPracticeTime": 5}],
        })


if __name__ == "__main__":
    unittest.main()
