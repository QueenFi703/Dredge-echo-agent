import unittest
from unittest.mock import patch

import app


class InteractiveDemoTests(unittest.TestCase):
    def test_follow_up_turn_passes_bounded_history_and_preserves_chat(self):
        history = [
            {"role": "user", "content": "Should Missouri run a pilot?"},
            {"role": "assistant", "content": "The initial evidence supports a pilot."},
        ]
        result = (
            "A challenged answer",
            "sources",
            "status",
            "{}",
            "{}",
        )

        with patch("app.run_research", return_value=result) as run_research:
            output = app.interactive_turn(
                "Challenge that assumption.",
                history,
                app.DEFAULT_ARCHITECTURE.value,
                app.ARCADE_RETRIEVAL,
                "session-1",
            )

        self.assertEqual(output[0][-1]["content"], "A challenged answer")
        self.assertEqual(output[-1], "session-1")
        context = run_research.call_args.args[4]
        self.assertIn("Should Missouri run a pilot?", context)
        self.assertIn("initial evidence supports a pilot", context)

    def test_empty_session_receives_new_arcade_identity(self):
        result = ("answer", "sources", "status", "{}", "{}")

        with patch("app.run_research", return_value=result):
            output = app.interactive_turn(
                "Question",
                [],
                app.DEFAULT_ARCHITECTURE.value,
                app.TAVILY_RETRIEVAL,
                "",
            )

        self.assertTrue(output[-1].startswith("dredge-"))


if __name__ == "__main__":
    unittest.main()
