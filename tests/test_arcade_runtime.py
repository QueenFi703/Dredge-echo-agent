import unittest
from types import SimpleNamespace

from bridge.arcade_runtime import (
    ARCADE_NEWS_TOOL,
    ArcadeAuthorizationRequired,
    ArcadeNewsSearchAdapter,
    ArcadeRuntime,
    ArcadeRuntimeError,
)


class _FakeTools:
    def __init__(self, *, authorization_status="completed", value=None):
        self.authorization_status = authorization_status
        self.value = value
        self.authorize_calls = []
        self.execute_calls = []

    def authorize(self, **kwargs):
        self.authorize_calls.append(kwargs)
        return SimpleNamespace(
            status=self.authorization_status,
            url="https://auth.arcade.example/approve",
        )

    def execute(self, **kwargs):
        self.execute_calls.append(kwargs)
        return SimpleNamespace(
            success=True,
            output=SimpleNamespace(value=self.value),
            execution_id="exec-123",
            duration=0.25,
        )


class _FakeClient:
    def __init__(self, tools):
        self.tools = tools


class ArcadeRuntimeTests(unittest.TestCase):
    def test_executes_only_allowlisted_tool_for_session_user(self):
        tools = _FakeTools(value={"news_results": []})
        runtime = ArcadeRuntime(
            client=_FakeClient(tools), allowed_tools=[ARCADE_NEWS_TOOL]
        )

        result = runtime.execute(
            tool_name=ARCADE_NEWS_TOOL,
            input={"keywords": "Astra"},
            user_id="session-1",
        )

        self.assertEqual(result.execution_id, "exec-123")
        self.assertEqual(tools.execute_calls[0]["user_id"], "session-1")

    def test_disallowed_tool_fails_before_authorization(self):
        tools = _FakeTools()
        runtime = ArcadeRuntime(
            client=_FakeClient(tools), allowed_tools=[ARCADE_NEWS_TOOL]
        )

        with self.assertRaises(ArcadeRuntimeError):
            runtime.execute(
                tool_name="Gmail.SendEmail", input={}, user_id="session-1"
            )

        self.assertEqual(tools.authorize_calls, [])

    def test_pending_authorization_returns_safe_url_without_execution(self):
        tools = _FakeTools(authorization_status="pending")
        runtime = ArcadeRuntime(
            client=_FakeClient(tools), allowed_tools=[ARCADE_NEWS_TOOL]
        )

        with self.assertRaises(ArcadeAuthorizationRequired) as caught:
            runtime.execute(
                tool_name=ARCADE_NEWS_TOOL,
                input={"keywords": "Astra"},
                user_id="session-1",
            )

        self.assertEqual(
            caught.exception.authorization_url,
            "https://auth.arcade.example/approve",
        )
        self.assertEqual(tools.execute_calls, [])

    def test_non_https_authorization_url_is_not_exposed(self):
        tools = _FakeTools(authorization_status="pending")
        runtime = ArcadeRuntime(
            client=_FakeClient(tools), allowed_tools=[ARCADE_NEWS_TOOL]
        )
        tools.authorize = lambda **kwargs: SimpleNamespace(
            status="pending", url="javascript:alert(1)"
        )

        with self.assertRaises(ArcadeAuthorizationRequired) as caught:
            runtime.execute(
                tool_name=ARCADE_NEWS_TOOL,
                input={"keywords": "Astra"},
                user_id="session-1",
            )

        self.assertIsNone(caught.exception.authorization_url)

    def test_news_adapter_normalizes_arcade_output(self):
        tools = _FakeTools(value={
            "news_results": [{
                "source": "Example News",
                "title": "Astra launches",
                "link": "https://news.example/astra",
            }]
        })
        runtime = ArcadeRuntime(
            client=_FakeClient(tools), allowed_tools=[ARCADE_NEWS_TOOL]
        )

        result = ArcadeNewsSearchAdapter(runtime, user_id="session-1").search(
            "Astra"
        )

        self.assertEqual(result["provider"], "Arcade")
        self.assertEqual(result["execution_id"], "exec-123")
        self.assertEqual(result["sources"][0]["publisher"], "Example News")
        self.assertEqual(result["sources"][0]["url"], "https://news.example/astra")


if __name__ == "__main__":
    unittest.main()
