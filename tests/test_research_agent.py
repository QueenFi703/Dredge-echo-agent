import unittest

from bridge.research_agent import ResearchAgent


class _FakeSearch:
    def search(self, query, *, max_results=5):
        return {
            "query": query,
            "answer": None,
            "sources": [{"title": "Source", "url": "https://example.com", "content": "fact"}],
        }


class _FakeLLM:
    def __init__(self):
        self.calls = []

    def generate(self, action, source="source", target="target", source_value=None):
        self.calls.append((action, source, target, source_value))
        return "grounded synthesis"


class ResearchAgentTests(unittest.TestCase):
    def test_research_routes_tavily_evidence_into_llm(self):
        llm = _FakeLLM()
        agent = ResearchAgent(search=_FakeSearch(), llm=llm)
        result = agent.research("What changed?", max_results=4)

        self.assertEqual(result.answer, "grounded synthesis")
        action, source, target, payload = llm.calls[0]
        self.assertEqual(action, "research_and_reason")
        self.assertEqual(source, "tavily_web_evidence")
        self.assertEqual(target, "grounded_answer")
        self.assertEqual(payload["question"], "What changed?")
        self.assertEqual(payload["evidence"]["sources"][0]["url"], "https://example.com")


if __name__ == "__main__":
    unittest.main()
