# helpers/chatbot_helper.py

import os
import json
import time
import traceback
from openai import OpenAI
from helpers.property_helpers import fetch_properties

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)
assistant_id = os.getenv("OPENAI_ASSISTANT_ID")

def continue_conversation(user_input: str, thread_id: str = None, system_msg: str = None) -> dict:
    """
    Continues or starts a new conversation (thread) with the assistant using the older
    client.beta.threads approach. We also do a basic check for function calls if status == requires_action.
    """
    try:
        # 1) Create or reuse the conversation thread
        if not thread_id:
            thread = client.beta.threads.create()
            thread_id = thread.id
            print(f"[LOG] Created NEW thread: {thread_id}")
            if system_msg:
                client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="system",
                    content=system_msg
                )
        else:
            print(f"[LOG] Reusing EXISTING thread: {thread_id}")
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

        # 3) Start a run
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )
        print(f"[LOG] Created run. ID: {run.id}, status={run.status}")

        # 4) Poll until the run ends
        while True:
            updated_run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if updated_run.status in ["completed", "requires_action", "failed", "incomplete"]:
                break
            time.sleep(1)

        print(f"[LOG] Polled run => status: {updated_run.status}")

        # 5) If the run requires_action => the LLM may want a “function call”
        if updated_run.status == "requires_action":
            # We'll check the messages to see if there's a special “function_call” request
            msgs = client.beta.threads.messages.list(thread_id=thread.id).data
            # Often the newest assistant message might contain something like JSON "function_call"
            assistant_msg = next((m for m in msgs if m.role == "assistant"), None)
            if assistant_msg and hasattr(assistant_msg, "content"):
                # Suppose the model tried to produce a JSON chunk. You have to define your own pattern:
                # e.g. content could be: {"name": "fetch_properties", "arguments": {...}}
                try:
                    parsed = json.loads(assistant_msg.content[0].text.value)
                    func_name = parsed.get("name")
                    arguments = parsed.get("arguments", {})
                    if func_name == "fetch_properties":
                        # 5a) call your local function
                        filter_params = arguments.get("filter_params", {})
                        results = fetch_properties(filter_params)

                        # 5b) Add a new message with role="function" containing the result
                        # This is how the new function-calling approach wants it,
                        # but you have to see if `beta.threads` supports role="function"
                        # or if you can emulate it with role="tool".
                        func_msg = client.beta.threads.messages.create(
                            thread_id=thread.id,
                            role="assistant",  # or possibly "tool" if "function" isn't recognized
                            content=json.dumps(results)
                        )

                        # 5c) Re-run so the LLM can incorporate the tool’s response
                        run2 = client.beta.threads.runs.create(
                            thread_id=thread.id,
                            assistant_id=assistant_id
                        )
                        while True:
                            updated_run2 = client.beta.threads.runs.retrieve(
                                thread_id=thread.id,
                                run_id=run2.id
                            )
                            if updated_run2.status in ["completed", "requires_action", "failed", "incomplete"]:
                                break
                            time.sleep(1)

                        if updated_run2.status == "completed":
                            # retrieve final messages again
                            msgs2 = client.beta.threads.messages.list(thread_id=thread.id).data
                            final_assistant = [m for m in msgs2 if m.role == "assistant"]
                            if final_assistant:
                                final_text = final_assistant[-1].content[0].text.value
                                return {"assistant_message": final_text, "thread_id": thread_id}

                    # If unrecognized function name or parse error, just skip
                except Exception as parse_err:
                    print("[ERR] Parsing function call failed:", parse_err)

        # 6) If we reach here or run was completed, fetch the final assistant message
        if updated_run.status == "completed":
            msgs = client.beta.threads.messages.list(thread_id=thread.id).data
            assistant_msgs = [m for m in msgs if m.role == "assistant"]
            if assistant_msgs:
                final_text = assistant_msgs[-1].content[0].text.value
                return {"assistant_message": final_text, "thread_id": thread_id}
            else:
                return {"assistant_message": "No assistant response found.", "thread_id": thread_id}

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
