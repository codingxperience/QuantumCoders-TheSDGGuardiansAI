import chainlit as cl
import requests
import json
import logging
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise EnvironmentError("❌ OPENROUTER_API_KEY not found in environment.")

# --- Authentication ---
@cl.password_auth_callback
def auth_callback(username: str, password: str):
    logging.info(f"Login attempt: username={username}")
    if username == "fred" and password == "secret123":
        return cl.User(identifier="fred", metadata={"role": "admin"})
    raise cl.AuthenticationError("Invalid username or password.")

# --- Starter Prompts ---
@cl.set_starters
async def set_starters():
    return [
        cl.Starter(label="🌾 Sustainable Farming", message="What are sustainable farming methods?"),
        cl.Starter(label="⚡ Reduce Energy Use", message="How can I reduce my energy use?"),
        cl.Starter(label="🌲 Deforestation Risks", message="What are the risks of deforestation?"),
        cl.Starter(label="🌳 Tree Planting", message="Why is tree planting important?"),
        cl.Starter(label="👦 Youth Involvement", message="How can youth take action?"),
    ]

# --- Chat Start ---
@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("history", [])
    await cl.ElementSidebar.set_title("Chat History")
    await cl.ElementSidebar.set_elements([])

# --- Resume Chat ---
@cl.on_chat_resume
async def on_chat_resume(thread):
    history = [{"role": m.author, "content": m.content} for m in thread.messages if m.author in ["user", "assistant"]]
    cl.user_session.set("history", history)

    sidebar_elements = [
        cl.Input(label="🔍 Search History", name="search_input", placeholder="Type to filter..."),
        cl.Switch(label="🌗 Dark Mode", name="dark_mode_toggle", value=True),
        cl.Text(content="🕘 Chat History", italic=True),
    ]

    for idx, entry in enumerate(history):
        label = f"{entry['role'].capitalize()}: {entry['content'][:30]}..."
        sidebar_elements.append(
            cl.Button(label=label, name=f"history_{idx}", value=entry['content'], variant="ghost")
        )

    await cl.ElementSidebar.set_elements(sidebar_elements)


# --- Main Chat Handler ---
@cl.on_message
async def on_message(message: cl.Message):
    user_input = message.content.strip()
    user_history = cl.user_session.get("history", [])

    # Smart context handling for off-topic questions
    off_topic = not any(kw in user_input.lower() for kw in [
        "climate", "uganda", "weather", "farming", "environment", "youth", "tree", "energy", "carbon", "forest"
    ])
    if off_topic:
        user_history.append({
            "role": "assistant",
            "content": "🤔 I'm mainly focused on climate change in Uganda, but I'll try to help with your question anyway!"
        })

    user_history.append({"role": "user", "content": user_input})

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek/deepseek-r1:free",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are ClimateGPT, a friendly assistant focused on Uganda's climate education. "
                    "Speak simply, avoid jargon, and if asked about global climate issues or random topics, "
                    "respond politely but steer the discussion back to Uganda where possible."
                )
            },
            *user_history
        ]
    }

    try:
        thinking_msg = await cl.Message(content="💭 Thinking...").send()

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload)
        )
        response.raise_for_status()
        data = response.json()
        assistant_reply = data["choices"][0]["message"]["content"]

        # Add small delay to smooth out fast replies
        await asyncio.sleep(0.5)

        user_history.append({"role": "assistant", "content": assistant_reply})
        cl.user_session.set("history", user_history)

        sidebar_elements = [
            cl.Text(content=f"{entry['role']}: {entry['content']}", name=f"history_entry_{idx}")
            for idx, entry in enumerate(user_history)
        ]
        await cl.ElementSidebar.set_elements(sidebar_elements)

        await thinking_msg.remove()
        await cl.Message(content=assistant_reply).send()

    except requests.exceptions.RequestException as e:
        await cl.Message(content=f"❌ Network error: {str(e)}").send()
    except Exception as e:
        await cl.Message(content=f"❌ Something went wrong: {str(e)}").send()
