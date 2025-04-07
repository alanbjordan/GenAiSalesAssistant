# routes/chatbot_route.py

from flask import Blueprint, request, jsonify
from config import Config
from helpers.chatbot_helper import continue_conversation
from helpers.cors_helpers import pre_authorized_cors_preflight
from datetime import datetime
from openai import OpenAI
import traceback
import os

# Initialize the OpenAI client.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")
if not OPENAI_API_KEY or not OPENAI_ASSISTANT_ID:
    print("Please set the OPENAI_API_KEY and OPENAI_ASSISTANT_ID environment variables.")
    raise ValueError("Missing OpenAI API key or assistant ID.")

chatbot_bp = Blueprint("chatbot_bp", __name__)

@pre_authorized_cors_preflight
@chatbot_bp.route("/chat", methods=["POST"])
def chat():
    """
    Handle a single chat message and get an assistant response using LLM API.
    
    Expects JSON:
    {
      "message": "<User's question or statement>",
      "thread_id": "<optional existing thread ID>"
    }
    Returns JSON:
    {
      "assistant_message": "...",
      "thread_id": "..."
    }
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400

        user_message = data.get("message", "").strip()
        thread_id = data.get("thread_id")

        if not user_message:
            return jsonify({"error": "No 'message' provided"}), 400

        # 1) Create or reuse the conversation thread
        if not thread_id:
            # Create a new thread using the LLM API
            thread = client.beta.threads.create()
            thread_id = thread.id
            print("Creating new thread with ID:", thread_id)
        else:
            print("Using existing thread with ID:", thread_id)

        # 2) Build the system message using your predefined assistant ID.
        system_message = f"Assistant ID: {OPENAI_ASSISTANT_ID}"

        # 3) Call the conversation function to get the assistant’s reply.
        result = continue_conversation(
            user_input=user_message,
            thread_id=thread_id,
            system_msg=system_message
        )
        assistant_text = result.get("assistant_message", "[No assistant response]")

        # 4) Return the final response with the assistant message and thread ID.
        return jsonify({
            "assistant_message": assistant_text,
            "thread_id": thread_id
        }), 200

    except Exception as e:
        print("[ERROR] Exception in /chat route:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
