import os
from typing import Any

import openai
import requests
from flask import Flask, request

app = Flask(__name__)

GRAPH_API_VERSION = os.environ.get("GRAPH_API_VERSION", "v16.0")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def create_openai_client() -> openai.OpenAI:
    """Create a client only when a webhook actually needs one."""
    api_key = os.environ.get("OPENAI_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_KEY is not configured")
    return openai.OpenAI(api_key=api_key, timeout=20.0, max_retries=0)


def response_text(response: Any) -> str:
    """Read the Responses API text output without assuming Chat Completions shape."""
    text = getattr(response, "output_text", None)
    if not isinstance(text, str) or not text.strip():
        raise RuntimeError("OpenAI returned an empty response")
    return text.strip()


def generate_reply(message: str, client: Any = None) -> str:
    client = client or create_openai_client()
    response = client.responses.create(
        model=os.environ.get("OPENAI_MODEL", OPENAI_MODEL),
        input=message,
        store=False,
    )
    return response_text(response)


def send_reply(sender_id: str, message: str) -> None:
    page_token = os.environ.get("PAGE_TOKEN")
    if not page_token:
        raise RuntimeError("PAGE_TOKEN is not configured")

    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/me/messages"
    response = requests.post(
        url,
        params={"access_token": page_token},
        json={"recipient": {"id": sender_id}, "message": {"text": message}},
        timeout=10,
    )
    response.raise_for_status()


def handle_message(data: Any, client: Any = None) -> bool:
    """Handle one Messenger text event and return whether a reply was sent."""
    if not isinstance(data, dict):
        return False

    try:
        event = data["entry"][0]["messaging"][0]
        sender_id = event["sender"]["id"]
        message = event["message"]["text"]
    except (KeyError, IndexError, TypeError):
        return False

    if not isinstance(sender_id, str) or not isinstance(message, str) or not message.strip():
        return False

    send_reply(sender_id, generate_reply(message, client))
    return True


@app.route("/", methods=["GET"])
def verify():
    """Verify the Facebook Messenger webhook subscription."""
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if request.args.get("hub.verify_token") != os.environ.get("ACCESS_TOKEN"):
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    return "MessengerGPT: https://facebook.com/MessengerBotGPT", 200


@app.route("/", methods=["POST"])
def fbwebhook():
    try:
        handle_message(request.get_json(silent=True))
    except (RuntimeError, requests.RequestException, openai.OpenAIError) as error:
        # Keep secrets and message contents out of logs while preserving the
        # webhook's acknowledgement behavior expected by Facebook.
        app.logger.warning("Messenger event was not completed: %s", error.__class__.__name__)
    return "200 OK HTTPS."


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False, port=5000)
