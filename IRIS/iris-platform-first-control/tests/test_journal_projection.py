"""Focused tests for bounded MCP action-journal projections.

These test only the metadata projection used for the journal; they do not
claim that a live MCP server or ChatGPT host was exercised.
"""
import unittest

from runtime.mcp_server import _journal_projection, _journal_result_projection


class JournalProjectionTests(unittest.TestCase):
    def test_strings_are_capped(self):
        projected = _journal_projection("x" * 700)
        self.assertEqual(len(projected), 514)
        self.assertTrue(projected.endswith("...[TRUNCATED]"))

    def test_dicts_are_bounded_and_mark_truncation(self):
        projected = _journal_projection({f"k{i}": i for i in range(35)})
        self.assertEqual(len([k for k in projected if k != "_truncated_keys"]), 30)
        self.assertEqual(projected["_truncated_keys"], 5)

    def test_lists_keep_only_ten_samples_and_count(self):
        projected = _journal_projection(list(range(25)))
        self.assertEqual(projected["_kind"], "list")
        self.assertEqual(projected["item_count"], 25)
        self.assertEqual(projected["sample"], list(range(10)))
        self.assertTrue(projected["truncated"])

    def test_nested_values_are_depth_limited(self):
        value = {"a": {"b": {"c": {"d": {"e": "deep"}}}}}
        projected = _journal_projection(value)
        self.assertEqual(projected["a"]["b"]["c"]["d"], "[TRUNCATED_DEPTH]")

    def test_action_history_is_summarized_not_copied(self):
        history = [{"action_id": f"action-{i}", "payload": "x" * 1000} for i in range(50)]
        projected = _journal_result_projection("get_agent_actions", history)
        self.assertEqual(projected["kind"], "action_history")
        self.assertEqual(projected["item_count"], 50)
        self.assertEqual(len(projected["action_ids"]), 20)
        self.assertNotIn("payload", str(projected))

    def test_resume_context_is_summarized(self):
        context = {
            "task": {"task_id": "task-1"},
            "latest_checkpoint": {"checkpoint_id": "cp-1"},
            "audit_events": [{"event_id": i} for i in range(4)],
            "recent_agent_actions": [{"action_id": "a"} for _ in range(3)],
        }
        projected = _journal_result_projection("get_resume_context", context)
        self.assertEqual(projected, {
            "kind": "resume_context",
            "task_id": "task-1",
            "action_count": 3,
            "checkpoint_present": True,
            "audit_event_count": 4,
        })


if __name__ == "__main__":
    unittest.main()
