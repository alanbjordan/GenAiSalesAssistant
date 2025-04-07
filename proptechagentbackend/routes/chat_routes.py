import os
import json
import traceback
from flask import Blueprint, request, jsonify
from openai import OpenAI  # New import style
from helpers.cors_helpers import pre_authorized_cors_preflight
from helpers.property_helpers import fetch_properties  # Your local helper for property lookup

# Initialize the OpenAI client using the new syntax
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

chatbot_bp = Blueprint("chatbot_bp", __name__)

tools = [{
    "type": "function",
    "function": {
        "name": "fetch_properties",
        "description": "Get property details based on filter criteria. Users can provide minimal or partial filters such as just the building name, or a range for bedrooms, price, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "bedrooms": {
                    "type": "integer",
                    "description": "Minimum number of bedrooms"
                },
                "max_bedrooms": {
                    "type": "integer",
                    "description": "Maximum number of bedrooms"
                },
                "price": {
                    "type": "number",
                    "description": "Minimum rental price"
                },
                "max_price": {
                    "type": "number",
                    "description": "Maximum rental price"
                },
                "bathrooms": {
                    "type": "integer",
                    "description": "Minimum number of bathrooms"
                },
                "max_bathrooms": {
                    "type": "integer",
                    "description": "Maximum number of bathrooms"
                },
                "sq_meters": {
                    "type": "number",
                    "description": "Minimum size of the property in square meters"
                },
                "max_sq_meters": {
                    "type": "number",
                    "description": "Maximum size of the property in square meters"
                },
                "distance_from_bts": {
                    "type": "number",
                    "description": "Maximum distance from the nearest BTS station in kilometers"
                },
                "property_name": {
                    "type": "string",
                    "description": "Name of the property (if applicable)"
                },
                "building_name": {
                    "type": "string",
                    "description": "Name of the building"
                },
                "property_code": {
                    "type": "string",
                    "description": "Unique code for the property"
                }, 
            },
            "required": [
            "bedrooms",
            "max_bedrooms",
            "price",
            "max_price",
            "bathrooms",
            "max_bathrooms",
            "sq_meters",
            "max_sq_meters",
            "distance_from_bts",
            "property_name",
            "building_name",
            "property_code"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
}]




@pre_authorized_cors_preflight
@chatbot_bp.route("/chat", methods=["POST"])
def chat():
    """
    A simplified chat endpoint using the new OpenAI client tool syntax.
    
    Expects JSON:
    {
      "message": "User's message",
      "conversation_history": [ {"role": "system"/"user"/"assistant", "content": "..."}, ... ] // optional
    }
    
    Returns JSON:
    {
      "assistant_message": "Assistant's reply",
      "conversation_history": [ ... ] // Updated conversation history
    }
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400

        user_message = data.get("message", "").strip()
        conversation_history = data.get("conversation_history", [])
        if not isinstance(conversation_history, list):
            conversation_history = []

        if not user_message:
            return jsonify({"error": "No 'message' provided"}), 400

        # If no conversation history, add a system message to define the assistant's identity
        if not conversation_history:
            system_message = (
                "You are a property agent named Patrica. "
                "Help users with property-related queries and use function calling if you need to fetch property details."
            )
            conversation_history.append({"role": "system", "content": system_message})

        # Append the new user message to the conversation history
        conversation_history.append({"role": "user", "content": user_message})

        # Call the ChatCompletion API using the new tools syntax
        completion = client.chat.completions.create(
            model="gpt-4o",  # or your chosen model
            messages=conversation_history,
            tools=tools
        )

        # Retrieve the full assistant message object
        message = completion.choices[0].message
        print(message)  # Debug print

        # Check if the assistant triggered a tool call
        if message.tool_calls and len(message.tool_calls) > 0:
            tool_call = message.tool_calls[0]
            func_name = tool_call.function.name
            args_str = tool_call.function.arguments  # Access the function's arguments

            try:
                func_args = json.loads(args_str)
            except Exception:
                assistant_response = "Error parsing tool arguments."
            else:
                if func_name == "fetch_properties":
                    filter_params = func_args.get("filter_params", {})
                    result = fetch_properties(filter_params)
                    # Append the tool's output to the conversation history with role "function"
                    conversation_history.append({
                        "role": "function",
                        "name": "fetch_properties",
                        "content": json.dumps(result)
                    })
                    # Re-run ChatCompletion with updated history to integrate the tool output
                    completion = client.chat.completions.create(
                        model="gpt-4o",
                        messages=conversation_history
                    )
                    message = completion.choices[0].message
                    assistant_response = message.content or ""
                else:
                    assistant_response = f"Unknown tool '{func_name}' called."
        else:
            # If no tool call was made, get the assistant's content normally
            assistant_response = message.content or ""

        # Convert the assistant message to a dictionary before appending to conversation history
        conversation_history.append({
            "role": message.role,
            "content": message.content,
            "tool_calls": [  # Optionally include tool call info if needed
                {
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    },
                    "type": tc.type
                }
                for tc in message.tool_calls
            ] if message.tool_calls else None
        })

        return jsonify({
            "assistant_message": assistant_response,
            "conversation_history": conversation_history
        }), 200

    except Exception as e:
        print(e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
