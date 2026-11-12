import unittest
from app.state_equivalence import compare_state_snapshots


class StateEquivalenceTests(unittest.TestCase):
    def test_identical_snapshots_match(self):
        snapshot = {"database":{"schema":{"users":"id"},"tables":{"users":[{"id":1,"name":"Ana"}]}},
                    "events":[{"name":"user.created","payload":{"id":1}}],
                    "integrations":[{"provider":"mail","operation":"send","response":{"status":202}}]}
        result = compare_state_snapshots(snapshot, snapshot)
        self.assertEqual(result["overall_status"], "MATCH")
        self.assertEqual(result["summary"]["difference_count"], 0)

    def test_database_row_difference_is_detected(self):
        original = {"database":{"tables":{"users":[{"id":1}]}}, "events":[], "integrations":[]}
        rebuilt = {"database":{"tables":{"users":[{"id":2}]}}, "events":[], "integrations":[]}
        result = compare_state_snapshots(original, rebuilt)
        self.assertEqual(result["dimension_status"]["database"], "MISMATCH")
        self.assertGreater(result["summary"]["difference_count"], 0)

    def test_database_row_order_is_ignored(self):
        a = {"database":{"tables":{"users":[{"id":1},{"id":2}]}}, "events":[], "integrations":[]}
        b = {"database":{"tables":{"users":[{"id":2},{"id":1}]}}, "events":[], "integrations":[]}
        self.assertEqual(compare_state_snapshots(a,b)["dimension_status"]["database"], "VERIFIED")

    def test_event_order_and_payload_are_compared(self):
        a = {"database":{}, "events":[{"name":"created"},{"name":"sent"}], "integrations":[]}
        b = {"database":{}, "events":[{"name":"sent"},{"name":"created"}], "integrations":[]}
        self.assertEqual(compare_state_snapshots(a,b)["dimension_status"]["events"], "MISMATCH")

    def test_integration_response_is_compared(self):
        a = {"database":{}, "events":[], "integrations":[{"provider":"payments","response":{"status":200}}]}
        b = {"database":{}, "events":[], "integrations":[{"provider":"payments","response":{"status":500}}]}
        self.assertEqual(compare_state_snapshots(a,b)["dimension_status"]["integrations"], "MISMATCH")


if __name__ == "__main__":
    unittest.main()
