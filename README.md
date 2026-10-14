# Facebook Messenger chatbot with OpenAI

MessengerGPT is a small Flask webhook that receives Facebook Messenger messages, sends the text to the OpenAI chat API, and replies through the Facebook Graph API.

This repository is a lightweight example for the ReinfyTeam fork. It does not include a production queue, persistent conversation history, secret management service, or retry policy for failed API requests.

## Requirements

- Python 3
- A Facebook Developer app with a Messenger product and page access token
- An OpenAI API key
- A public HTTPS endpoint for Facebook webhook delivery

The project dependency list is in [`requirements.txt`](requirements.txt). The application reads credentials from environment variables; do not commit tokens to the repository.

## Installation

Clone the repository and create an isolated Python environment:

```sh
git clone https://github.com/ReinfyTeam/MessengerGPT.git
cd MessengerGPT
python -m venv .venv
```

Activate the environment and install the project dependencies.

On macOS or Linux:

```sh
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Configuration

Set these environment variables before starting the server:

| Variable | Purpose |
| --- | --- |
| `OPENAI_KEY` | OpenAI API key used for chat completions. |
| `PAGE_TOKEN` | Facebook page access token used to send replies. |
| `ACCESS_TOKEN` | Verification token entered in the Facebook webhook configuration. |

For example, on macOS or Linux:

```sh
export OPENAI_KEY="your-openai-key"
export PAGE_TOKEN="your-facebook-page-token"
export ACCESS_TOKEN="your-webhook-verification-token"
```

In Windows PowerShell:

```powershell
$env:OPENAI_KEY = "your-openai-key"
$env:PAGE_TOKEN = "your-facebook-page-token"
$env:ACCESS_TOKEN = "your-webhook-verification-token"
```

## Run locally

Start the Flask server with:

```sh
python app.py
```

The server listens on `0.0.0.0:5000`. A `GET /` request is used for Facebook webhook verification. A `POST /` request containing a Messenger event is handled as an incoming message.

To test webhook delivery from a local machine, expose port 5000 through an HTTPS tunnel such as [ngrok](https://ngrok.com/):

```sh
ngrok http 5000
```

Use the generated HTTPS URL with the `/` path as the callback URL in the Facebook Developer dashboard. Enter the same value as `ACCESS_TOKEN` in the webhook verification-token field, then subscribe the page to the message events required by the bot.

## Deployment

The included [`.replit`](.replit) configuration runs `python app.py` on port 5000 for Replit deployments. For another hosting provider, configure the three environment variables, expose the Flask port through HTTPS, and use the provider's Python process command to run `python app.py`.

## Current behavior and limitations

- The webhook sends received message text to the OpenAI chat API using the model selected in [`app.py`](app.py).
- The response is sent back through the Facebook Graph API.
- The example does not persist conversations or implement a durable background queue.
- API and webhook exceptions are handled by the current example code and are printed to the process log; production deployments should add structured logging, timeouts, retries and secret management appropriate for their host.

## License

This project is distributed under the [MIT License](LICENSE.md).
