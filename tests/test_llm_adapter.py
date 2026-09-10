import os
import sys
import types
import unittest
from unittest.mock import patch

from bridge.llm_adapter import LLMAdapter, LLMBackendError


class _FakeCompletions:
    def __init__(self, calls):
        self._calls = calls

    def create(self, **kwargs):
        self._calls.append(kwargs)
        message = types.SimpleNamespace(content="token factory response")
        return types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=message)]
        )


class _FakeOpenAI:
    clients = []

    def __init__(self, **kwargs):
        self.options = kwargs
        self.calls = []
        self.chat = types.SimpleNamespace(completions=_FakeCompletions(self.calls))
        self.__class__.clients.append(self)


class NebiusBackendTests(unittest.TestCase):
    def setUp(self):
        _FakeOpenAI.clients.clear()

    def test_nebius_uses_token_factory_endpoint_model_and_key(self):
        fake_module = types.SimpleNamespace(OpenAI=_FakeOpenAI)
        env = {
            "NEBIUS_API_KEY": "test-key",
            "NEBIUS_MODEL": "org/test-model",
        }

        with patch.dict(os.environ, env, clear=True), patch.dict(
            sys.modules, {"openai": fake_module}
        ):
            result = LLMAdapter(backend="nebius").generate(
                "summarize", source_value="an execution trace"
            )

        self.assertEqual(result, "token factory response")
        client = _FakeOpenAI.clients[0]
        self.assertEqual(client.options["api_key"], "test-key")
        self.assertEqual(
            client.options["base_url"], "https://api.tokenfactory.nebius.com/v1"
        )
        self.assertEqual(client.calls[0]["model"], "org/test-model")
        self.assertEqual(client.calls[0]["messages"][0]["role"], "user")

    def test_constructor_model_overrides_environment_model(self):
        fake_module = types.SimpleNamespace(OpenAI=_FakeOpenAI)
        env = {"NEBIUS_API_KEY": "test-key", "NEBIUS_MODEL": "env-model"}

        with patch.dict(os.environ, env, clear=True), patch.dict(
            sys.modules, {"openai": fake_module}
        ):
            LLMAdapter(backend="nebius", model="explicit-model").generate("infer")

        self.assertEqual(_FakeOpenAI.clients[0].calls[0]["model"], "explicit-model")

    def test_nebius_requires_api_key(self):
        with patch.dict(os.environ, {"NEBIUS_MODEL": "test-model"}, clear=True):
            with self.assertRaisesRegex(LLMBackendError, "NEBIUS_API_KEY"):
                LLMAdapter(backend="nebius").generate("infer")

    def test_nebius_requires_model(self):
        with patch.dict(os.environ, {"NEBIUS_API_KEY": "test-key"}, clear=True):
            with self.assertRaisesRegex(LLMBackendError, "Nebius model"):
                LLMAdapter(backend="nebius").generate("infer")


if __name__ == "__main__":
    unittest.main()
