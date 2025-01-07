from openai import OpenAI
import os
from dotenv import load_dotenv
from gradio_client import Client, handle_file
import base64
import json
import re

# Load environment variables from .env file
load_dotenv()


OSATLAS_HUGGINGFACE_SOURCE = "maxiw/OS-ATLAS"
OSATLAS_HUGGINGFACE_MODEL = "OS-Copilot/OS-Atlas-Base-7B"
OSATLAS_HUGGINGFACE_API = "/run_example"
LLAMA_32_MODEL = "llama3.2-90b-vision"
LLAMA_33_MODEL = "llama3.3-70b"


def create_llama_function_list(definitions):
    functions = []

    for name, details in definitions.items():
        properties = {}
        required = []

        for param_name, param_desc in details["params"].items():
            properties[param_name] = {"type": "string", "description": param_desc}
            required.append(param_name)

        function_def = {
            "type": "function",
            "function": {
                "name": name,
                "description": details["description"],
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }
        functions.append(function_def)

    return functions


def parse_llama_tool_calls(content, tool_calls):

    combined_tool_calls = []
    for tool_call in tool_calls:
        try:
            parameters = json.loads(tool_call.function.arguments)
            combined_tool_calls.append(
                {
                    "type": "function",
                    "name": tool_call.function.name,
                    "parameters": parameters,
                }
            )
        except json.JSONDecodeError:
            print(
                f"Error decoding JSON for tool call arguments: {tool_call.function.arguments}"
            )

    if content and not tool_calls:
        try:
            tool_call = json.loads(re.search(r"\{.*\}", content).group(0))
            if tool_call.get("name") and tool_call.get("parameters"):
                combined_tool_calls.append(tool_call)
                return None, combined_tool_calls
        except Exception as e:
            pass

    return content, combined_tool_calls


llama = OpenAI(
    base_url="https://api.llama-api.com",
    api_key=os.getenv("LLAMA_API_KEY"),
)
osatlas = Client(OSATLAS_HUGGINGFACE_SOURCE)


def call_vision_model(messages):
    completion = llama.chat.completions.create(model=LLAMA_32_MODEL, messages=messages)
    return completion.choices[0].message.content


def call_action_model(messages, functions):
    completion = llama.chat.completions.create(
        model=LLAMA_33_MODEL,
        messages=messages,
        tools=create_llama_function_list(functions),
    )
    return parse_llama_tool_calls(
        completion.choices[0].message.content,
        completion.choices[0].message.tool_calls or [],
    )


def call_grounding_model(prompt, image_data):
    result = osatlas.predict(
        image=handle_file(image_data),
        text_input=prompt,
        model_id=OSATLAS_HUGGINGFACE_MODEL,
        api_name=OSATLAS_HUGGINGFACE_API,
    )
    return result[1], result[2]


def Message(content, role="assistant"):
    return {"role": role, "content": content}


def Text(text):
    return {"type": "text", "text": text}


def Image(data):
    base64_data = base64.b64encode(data).decode("utf-8")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{base64_data}"},
    }
