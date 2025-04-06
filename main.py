import chainlit as cl
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env variables

API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    raise EnvironmentError("❌ OPENROUTER_API_KEY not found.")

# --- Auth ---
@cl.password_auth_callback
def auth_callback(username: str, password: str):
    if (username, password) == ("fred", "secret123"):
        return cl.User(identifier="fred", metadata={"role": "admin"})
    return None

# --- Starter Prompts ---
@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="🌾 Sustainable Farming",
            message="What are sustainable farming methods?",
            # icon="/public/idea.svg",
        ),
        cl.Starter(
            label="⚡ Reduce Energy Use",
            message="How can I reduce my energy use?",
            # icon="/public/energy.svg",
        ),
        cl.Starter(
            label="🌲 Deforestation Risks",
            message="What are the risks of deforestation?",
            # icon="/public/forest.svg",
        ),
        cl.Starter(
            label="🌳 Tree Planting",
            message="Why is tree planting important?",
            # icon="/public/tree.svg",
        ),
        cl.Starter(
            label="👦 Youth Involvement",
            message="How can youth take action?",
            # icon="/public/youth.svg",
        ),
    ]

# --- Chat Start ---
@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("history", [])

    history = cl.user_session.get("history", [])
    sidebar_elements = [
        cl.Text(content=f"{entry['role']}: {entry['content']}", name=f"history_entry_{idx}")
        for idx, entry in enumerate(history)
    ]

    await cl.ElementSidebar.set_elements(sidebar_elements)
    await cl.ElementSidebar.set_title("Chat History")

    # await cl.Message(content="👋 Welcome to Uganda's ClimateGPT! Ask me anything about climate change.").send()

# --- Resume Hook ---
@cl.on_chat_resume
async def on_chat_resume(thread):
    print(f"✅ Chat Resumed: {thread.id} | Messages: {len(thread.messages)}")

# --- Message Handler (covers both text + starters) ---
@cl.on_message
async def on_message(message: cl.Message):
    user_history = cl.user_session.get("history", [])
    user_history.append({"role": "user", "content": message.content})

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
            *user_history
        ]
    }

    try:
        thinking_msg = await cl.Message(content="Thinking...").send()

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload)
        )
        response.raise_for_status()
        data = response.json()
        assistant_reply = data["choices"][0]["message"]["content"]

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
