import os
import sys
import types
import unittest
from unittest.mock import patch

from bridge.search_adapter import SearchBackendError, TavilySearchAdapter


class _FakeTavilyClient:
    clients = []

    def __init__(self, **kwargs):
        self.options = kwargs
        self.calls = []
        self.__class__.clients.append(self)

    def search(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "query": kwargs["query"],
            "answer": "summary",
            "response_time": 0.25,
            "results": [
                {
                    "title": "Example",
                    "url": "https://example.com",
                    "content": "evidence",
                    "score": 0.98,
                    "raw_content": "should not leak",
                }
            ],
        }


class TavilySearchAdapterTests(unittest.TestCase):
    def setUp(self):
        _FakeTavilyClient.clients.clear()

    def test_search_normalizes_results_and_tracks_project(self):
        fake_module = types.SimpleNamespace(TavilyClient=_FakeTavilyClient)
        env = {"TAVILY_API_KEY": "tvly-test", "TAVILY_PROJECT": "dredge-echo-agent"}
        with patch.dict(sys.modules, {"tavily": fake_module}), patch.dict(
            os.environ, env, clear=True
        ):
            adapter = TavilySearchAdapter()
            result = adapter.search("agent infrastructure", max_results=3)

        client = _FakeTavilyClient.clients[0]
        self.assertEqual(client.options["api_key"], "tvly-test")
        self.assertEqual(client.options["project"], "dredge-echo-agent")
        self.assertEqual(client.calls[0]["max_results"], 3)
        self.assertTrue(client.calls[0]["include_answer"])
        self.assertEqual(result["sources"][0]["url"], "https://example.com")
        self.assertNotIn("raw_content", result["sources"][0])

    def test_requires_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(SearchBackendError, "TAVILY_API_KEY"):
                TavilySearchAdapter()


if __name__ == "__main__":
    unittest.main()
