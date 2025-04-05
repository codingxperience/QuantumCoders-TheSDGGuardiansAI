import chainlit as cl
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env variables

API_KEY = os.getenv("OPENROUTER_API_KEY")

print("🔍 API Key Found:", bool(API_KEY))

if not API_KEY:
    raise EnvironmentError("❌ OPENROUTER_API_KEY not found.")

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("history", [])
    await cl.Message(content="Welcome to Uganda's ClimateGPT! Ask me anything about climate change.").send()

@cl.on_message
async def on_message(message: cl.Message):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek/deepseek-r1:free",
        "messages": [
            {
                "role": "system",
                "content": "You are ClimateGPT, a friendly assistant focused on Uganda's climate education. Speak simply, avoid lists or jargon."
            },
            {
                "role": "user",
                "content": message.content
            }
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        data = response.json()
        assistant_reply = data["choices"][0]["message"]["content"]
        await cl.Message(content=assistant_reply).send()
    except requests.exceptions.RequestException as e:
        await cl.Message(content=f"❌ Network error: {str(e)}").send()
    except Exception as e:
        await cl.Message(content=f"❌ Something went wrong: {str(e)}").send()
    