# helpers/chatbot_helper.py

import os
import json
import time
import traceback
from openai import OpenAI

# Initialize the OpenAI client using your API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Use your assistant ID from environment variable or default value
assistant_id = os.getenv("OPENAI_ASSISTANT_ID")

def continue_conversation(user_input: str, thread_id: str = None, system_msg: str = None) -> dict:
    """
    Continues or starts a new conversation (thread) with the assistant using the LLM API.
    
    :param user_input: The user's message as a string.
    :param thread_id: Optional existing thread_id for multi-turn conversations.
    :param system_msg: Optional system message to initialize the conversation.
    :return: Dictionary containing "assistant_message" and "thread_id".
    """
    try:
        # 1) Create or reuse the conversation thread
        if not thread_id:
            thread = client.beta.threads.create()
            thread_id = thread.id
            print(f"[LOG] Created NEW thread: {thread_id}")
            # If a system message is provided, add it as the first message
            if system_msg:
                client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="system",
                    content=system_msg
                )
        else:
            print(f"[LOG] Reusing EXISTING thread: {thread_id}")
            # Create a simple stub for an existing thread
            thread_stub = type("ThreadStub", (), {})()
            thread_stub.id = thread_id
            thread = thread_stub

        # 2) Add the user's message to the thread
        user_message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )
        print(f"[LOG] Added user message. ID: {user_message.id}")

        # 3) Start a new run for the assistant's response
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )
        print(f"[LOG] Created run. ID: {run.id}, status={run.status}")

        # 4) Poll until the run reaches a terminal state
        while True:
            updated_run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if updated_run.status in ["completed", "requires_action", "failed", "incomplete"]:
                break
            time.sleep(1)
        print(f"[LOG] Polled run => status: {updated_run.status}")

        # (Optional) Skip detailed tool handling for simplicity
        if updated_run.status == "requires_action":
            print("[LOG] Run requires action, but skipping tool handling for simplicity.")

        # 5) Handle the final run status and retrieve the assistant's message
        if updated_run.status == "completed":
            msgs = client.beta.threads.messages.list(thread_id=thread.id)
            assistant_msgs = [m for m in msgs.data if m.role == "assistant"]
            if assistant_msgs:
                # Assume the first assistant message contains the response
                final_text = assistant_msgs[0].content[0].text.value
                print("[LOG] Final assistant message found.")
                return {
                    "assistant_message": str(final_text),
                    "thread_id": thread_id
                }
            else:
                return {
                    "assistant_message": "No assistant response found.",
                    "thread_id": thread_id
                }
        elif updated_run.status == "failed":
            return {
                "assistant_message": "Run ended with status: failed. The model encountered an error.",
                "thread_id": thread_id
            }
        elif updated_run.status == "incomplete":
            return {
                "assistant_message": "Run ended with status: incomplete. Possibly waiting for more info.",
                "thread_id": thread_id
            }
        else:
            return {
                "assistant_message": f"Run ended with status: {updated_run.status}, no final message produced.",
                "thread_id": thread_id
            }

    except Exception as e:
        print("[ERROR] Exception in continue_conversation():")
        traceback.print_exc()
        return {
            "assistant_message": f"An error occurred: {str(e)}",
            "thread_id": thread_id
        }
