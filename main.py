import chainlit as cl
import requests
import json
import os

API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Debug check for API key
print("🔍 API Key Found:", bool(API_KEY))

if not API_KEY:
    raise EnvironmentError("❌ OPENROUTER_API_KEY environment variable not found.")

BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = {
    "role": "system",
    "content": "You are ClimateGPT, a helpful assistant focused on Uganda’s climate change. Speak clearly, be friendly, and avoid bullet points or technical jargon."
}

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("history", [])
    await cl.Message(content="Welcome to Uganda's ClimateGPT! How can I help you today?").send()

@cl.on_chat_resume
async def on_chat_resume():
    history = cl.user_session.get("history", [])
    for role, content in history:
        await cl.Message(content=content, author=role).send()

@cl.on_message
async def on_message(message: cl.Message):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "ClimateGPT/1.0"
    }

    payload = {
        "model": "deepseek-chat",  # ✅ Correct model name
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
    except requests.exceptions.RequestException as e:
        await cl.Message(content=f"❌ Could not fetch response: {str(e)}").send()
    except KeyError:
        await cl.Message(content="❌ Unexpected response format.").send()
    except Exception as e:
        await cl.Message(content=f"❌ An error occurred: {str(e)}").send()
