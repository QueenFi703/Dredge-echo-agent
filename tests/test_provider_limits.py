"""Offline tests of the Nebius SDK boundary; never use live credentials or HTTP."""

import json
import os
import threading
import time
import traceback
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch

try:
    import httpx
    import openai
except ImportError:
    openai = None

from bridge.llm_adapter import LLMAdapter, LLMBackendError, LLMCompletionError


@unittest.skipIf(openai is None, "install the existing [agent] dependencies")
class NebiusProviderLimitTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.sleeps = []
        self.requests = []
        self.options = []
        self.clients = []
        self.outcomes = []
        self.sdk_client = openai.OpenAI
        self.addCleanup(self._close_clients)
        for patcher in (patch.dict(os.environ, {"NEBIUS_API_KEY": "synthetic-secret"}, clear=True),
                        patch("openai.OpenAI", side_effect=self._client)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def _close_clients(self):
        for client in self.clients:
            client.close()

    def _client(self, **kwargs):
        self.options.append(kwargs)
        client = self.sdk_client(
            **kwargs, http_client=httpx.Client(transport=httpx.MockTransport(self._request))
        )
        self.clients.append(client)
        return client

    def _request(self, request):
        self.requests.append(request)
        duration, outcome = self.outcomes.pop(0)
        self.now += duration
        if isinstance(outcome, Exception):
            raise outcome
        if isinstance(outcome, int):
            return httpx.Response(outcome, json={"error": "synthetic-secret private prompt"})
        if isinstance(outcome, dict):
            return httpx.Response(200, json=outcome)
        content, finish_reason = outcome
        return httpx.Response(200, json={
            "id": "offline", "model": "offline", "object": "chat.completion", "created": 0,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": content},
                         "finish_reason": finish_reason}],
        })

    def _sleep(self, delay):
        self.sleeps.append(delay)
        self.now += delay

    def _generate(self, outcomes, *, model="test-model", max_tokens=800):
        self.outcomes = list(outcomes)
        # create=True also lets baseline tests show missing behavior, not missing imports.
        with patch("bridge.llm_adapter.monotonic", lambda: self.now, create=True), patch(
            "bridge.llm_adapter.sleep", self._sleep, create=True
        ):
            return LLMAdapter(backend="nebius", model=model, max_tokens=max_tokens).generate("infer")

    def test_explicit_timeouts_and_no_hidden_sdk_retries(self):
        self.assertEqual(self._generate([(0, ("complete", "stop"))]), "complete")
        self.assertTrue(self.clients[0].is_closed)
        self.assertEqual(self.options[0].get("max_retries"), 0)
        self.assertEqual(self.options[0].get("timeout"), 90.0)
        self.assertEqual(self.requests[0].extensions["timeout"],
                         {"connect": 90.0, "read": 90.0, "write": 90.0, "pool": 90.0})

    def test_transient_http_errors_recover_once(self):
        for status in (408, 409, 429, 500, 503):
            with self.subTest(status=status):
                self.requests.clear()
                self.sleeps.clear()
                self.assertEqual(self._generate([(0, status), (0, ("complete", "stop"))]), "complete")
                self.assertEqual(len(self.requests), 2)
                self.assertEqual(self.sleeps, [1.0])

    def test_connect_and_read_timeouts_recover_once(self):
        for exception in (httpx.ConnectTimeout, httpx.ReadTimeout):
            with self.subTest(exception=exception):
                self.requests.clear()
                self.sleeps.clear()
                self.assertEqual(self._generate([
                    (0, exception("synthetic-secret")), (0, ("complete", "stop"))
                ]), "complete")
                self.assertEqual(len(self.requests), 2)
                self.assertEqual(self.sleeps, [1.0])

    def test_permanent_errors_are_not_retried_and_are_secret_safe(self):
        for status in (400, 401, 403, 404, 422):
            with self.subTest(status=status):
                self.requests.clear()
                try:
                    self._generate([(0, status)])
                except LLMBackendError as exc:
                    rendered = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
                    self.assertNotIn("synthetic-secret", rendered)
                    self.assertNotIn("private prompt", rendered)
                    self.assertIn("Nebius", str(exc))
                else:
                    self.fail("expected a sanitized LLMBackendError")
                self.assertEqual(len(self.requests), 1)
                self.assertTrue(self.clients[-1].is_closed)

    def test_exhausted_timeouts_have_two_attempts_not_sdk_retry_multiplication(self):
        for exception in (httpx.ConnectTimeout, httpx.ReadTimeout):
            with self.subTest(exception=exception):
                self.requests.clear()
                self.sleeps.clear()
                with self.assertRaises(LLMBackendError):
                    self._generate([(0, exception("secret"))] * 6)
                self.assertEqual(len(self.requests), 2)
                self.assertEqual(self.sleeps, [1.0])

    def test_exhausted_http_retries_are_bounded(self):
        with self.assertRaises(LLMBackendError):
            self._generate([(0, 503)] * 6)
        self.assertEqual(len(self.requests), 2)
        self.assertEqual(self.sleeps, [1.0])

    def test_one_transient_retry_is_shared_across_completion_budgets(self):
        with self.assertRaises(LLMBackendError):
            self._generate([(0, 503), (0, ("partial", "length")), (0, 503), (0, ("complete", "stop"))])
        self.assertEqual(len(self.requests), 3)
        self.assertEqual([json.loads(r.content)["max_tokens"] for r in self.requests], [800, 800, 1600])
        self.assertEqual(self.sleeps, [1.0])

    def test_completion_retry_shares_remaining_elapsed_budget(self):
        self.assertEqual(self._generate([(130, ("partial", "length")), (0, ("complete", "stop"))]), "complete")
        self.assertEqual(self.requests[1].extensions["timeout"],
                         {"connect": 50.0, "read": 50.0, "write": 50.0, "pool": 50.0})

    def test_no_retry_when_backoff_would_exhaust_elapsed_budget(self):
        with self.assertRaisesRegex(LLMBackendError, "time budget"):
            self._generate([(179.5, 503), (0, ("complete", "stop"))])
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(self.sleeps, [])

    def test_late_success_is_not_accepted_or_retried(self):
        with self.assertRaisesRegex(LLMBackendError, "time budget"):
            self._generate([(180, ("complete", "stop")), (0, ("complete", "stop"))])
        self.assertEqual(len(self.requests), 1)
        self.assertTrue(self.clients[-1].is_closed)

    def test_late_backoff_does_not_admit_another_attempt(self):
        def oversleep(delay):
            self.now += 181
        with patch.object(self, "_sleep", oversleep):
            with self.assertRaisesRegex(LLMBackendError, "time budget"):
                self._generate([(0, 429), (0, ("complete", "stop"))])
        self.assertEqual(len(self.requests), 1)

    def test_initialization_failure_is_secret_safe(self):
        with patch("openai.OpenAI", side_effect=ValueError("synthetic-secret")):
            try:
                self._generate([])
            except LLMBackendError as exc:
                rendered = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
                self.assertNotIn("synthetic-secret", rendered)
            else:
                self.fail("expected a sanitized initialization error")
        self.assertEqual(self.requests, [])

    def test_malformed_completion_is_rejected_without_retry(self):
        for payload in ({"choices": []}, {"choices": None},
                        {"choices": [{"message": {"content": ["private prompt"]}}]}):
            with self.subTest(payload=payload):
                self.requests.clear()
                with self.assertRaises(LLMCompletionError):
                    self._generate([(0, payload)])
                self.assertEqual(len(self.requests), 1)

    def test_real_sdk_read_timeout_against_local_stalled_server(self):
        received = threading.Event()
        timed_out = threading.Event()

        class StallHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                received.set()
                time.sleep(0.15)  # No headers: the SDK must stop waiting for a read.

            def log_message(self, *args):
                pass

        server = HTTPServer(("127.0.0.1", 0), StallHandler)
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
        thread.start()

        def local_client(**kwargs):
            client = self.sdk_client(**kwargs, http_client=httpx.Client(trust_env=False))
            create = client.chat.completions.create

            def record_timeout(**request):
                try:
                    return create(**request)
                except openai.APITimeoutError:
                    timed_out.set()
                    raise

            client.chat.completions.create = record_timeout
            self.clients.append(client)
            return client

        try:
            env = {"NEBIUS_BASE_URL": "http://127.0.0.1:%s/v1" % server.server_port}
            with patch.dict(os.environ, env), patch("openai.OpenAI", side_effect=local_client), patch(
                "bridge.llm_adapter.NEBIUS_REQUEST_TIMEOUT_SECONDS", 0.03
            ), patch("bridge.llm_adapter.NEBIUS_MAX_RETRIES", 0):
                started = time.monotonic()
                with self.assertRaises(LLMBackendError):
                    LLMAdapter(backend="nebius", model="offline").generate("infer")
                self.assertLess(time.monotonic() - started, 1.0)
                self.assertTrue(received.is_set())
                self.assertTrue(timed_out.is_set())
                self.assertTrue(self.clients[-1].is_closed)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1)
            self.assertFalse(thread.is_alive())

    def test_model_success_and_completion_budgets_are_preserved(self):
        for model, expected in (("zai-org/GLM-5.3", [4096, 8192]),
                                ("zai-org/GLM-5.3-Flash", [4096, 8192]),
                                ("moonshotai/Kimi-K3", [4096, 8192]),
                                ("nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B", [2048, 4096])):
            with self.subTest(model=model):
                self.requests.clear()
                self.assertEqual(self._generate([(0, ("partial", "length")), (0, ("complete", "stop"))], model=model), "complete")
                self.assertEqual([json.loads(r.content)["max_tokens"] for r in self.requests], expected)


if __name__ == "__main__":
    unittest.main()
