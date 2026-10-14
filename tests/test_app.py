import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import app


class FakeResponses:
    def __init__(self, text="reply"):
        self.text = text
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text=self.text)


class FakeClient:
    def __init__(self, responses):
        self.responses = responses


class FakeResponse:
    def raise_for_status(self):
        return None


class MessengerGPTTests(unittest.TestCase):
    def test_generate_reply_uses_responses_api_contract(self):
        responses = FakeResponses("safe reply")
        reply = app.generate_reply("hello", FakeClient(responses))

        self.assertEqual(reply, "safe reply")
        self.assertEqual(responses.calls[0]["input"], "hello")
        self.assertFalse(responses.calls[0]["store"])

    def test_message_sends_reply_without_logging_content(self):
        responses = FakeResponses("safe reply")
        with patch.dict(os.environ, {"PAGE_TOKEN": "test-token"}, clear=False), patch(
            "app.requests.post", return_value=FakeResponse()
        ) as post:
            self.assertTrue(app.handle_message({
                "entry": [{"messaging": [{"sender": {"id": "42"}, "message": {"text": "hello"}}]}]
            }, FakeClient(responses)))

        post.assert_called_once()
        self.assertEqual(post.call_args.kwargs["json"]["recipient"]["id"], "42")
        self.assertEqual(post.call_args.kwargs["json"]["message"]["text"], "safe reply")
        self.assertEqual(post.call_args.kwargs["timeout"], 10)

    def test_invalid_event_is_ignored(self):
        self.assertFalse(app.handle_message({"entry": []}))

    def test_empty_response_is_rejected(self):
        with self.assertRaises(RuntimeError):
            app.response_text(SimpleNamespace(output_text="  "))

    def test_webhook_verification(self):
        with patch.dict(os.environ, {"ACCESS_TOKEN": "verify-me"}, clear=False):
            client = app.app.test_client()
            response = client.get("/?hub.mode=subscribe&hub.challenge=123&hub.verify_token=verify-me")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(as_text=True), "123")


if __name__ == "__main__":
    unittest.main()
