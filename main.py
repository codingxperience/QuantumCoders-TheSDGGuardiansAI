import chainlit as cl
import requests
import json
import os

# Fetch API key from environment variable
API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Debug check - optional but helpful during deployment
print("🔍 API Key Found:", bool(API_KEY))  # Should print True in logs

# Raise error if API key is missing
if not API_KEY:
    raise EnvironmentError("❌ OPENROUTER_API_KEY environment variable not found.")

# OpenRouter endpoint
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# System prompt to guide the assistant’s behavior
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are ClimateGPT, a helpful assistant focused on Uganda’s climate change. "
        "Speak clearly, be friendly, and avoid bullet points or technical jargon."
    )
}

# Event: On chat start
@cl.on_chat_start
async def on_chat_start():
    await cl.Message(content="👋🏿 Welcome to Uganda's ClimateGPT! How can I assist you today?").send()

# Event: On message received from user
@cl.on_message
async def on_message(message: cl.Message):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek/deepseek-r1:free",  # Ensure this is a supported model name
        "messages": [
            SYSTEM_PROMPT,
            {"role": "user", "content": message.content}
        ]
    }

    try:
        response = requests.post(BASE_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        data = response.json()
        assistant_reply = data["choices"][0]["message"]["content"]
        await cl.Message(content=assistant_reply).send()

    except requests.exceptions.HTTPError as http_err:
        await cl.Message(content=f"❌ HTTP error: {str(http_err)}").send()

    except requests.exceptions.RequestException as req_err:
        await cl.Message(content=f"❌ Request error: {str(req_err)}").send()

    except KeyError:
        await cl.Message(content="❌ Unexpected response format.").send()

    except Exception as e:
        await cl.Message(content=f"❌ An error occurred: {str(e)}").send()
