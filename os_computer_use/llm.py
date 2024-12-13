from openai import OpenAI
import os
from dotenv import load_dotenv
import fireworks.client
from gradio_client import Client, handle_file
import base64

# Load environment variables from .env file
load_dotenv()


OSATLAS_HUGGINGFACE_SOURCE = "maxiw/OS-ATLAS"
OSATLAS_HUGGINGFACE_MODEL = "OS-Copilot/OS-Atlas-Base-7B"
OSATLAS_HUGGINGFACE_API = "/run_example"
LLAMA_32_OPENROUTER_MODEL = "meta-llama/llama-3.2-90b-vision-instruct"
LLAMA_33_FIREWORKS_MODEL = "accounts/fireworks/models/llama-v3p3-70b-instruct"


def create_llama_function_list(definitions):
    functions = []

    for name, details in definitions.items():
        properties = {}
        required = []

        if "params" in details:
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


fireworks.client.api_key = os.getenv("FIREWORKS_API_KEY")
llama_vision = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
osatlas = Client(OSATLAS_HUGGINGFACE_SOURCE)


def call_vision_model(messages):
    completion = llama_vision.chat.completions.create(
        model=LLAMA_32_OPENROUTER_MODEL, messages=messages
    )
    return completion.choices[0].message.content


def call_action_model(messages, functions):
    completion = fireworks.client.ChatCompletion.create(
        model=LLAMA_33_FIREWORKS_MODEL,
        messages=messages,
        tools=create_llama_function_list(functions),
    )
    return (
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


def Message(content, role="assistant", log=True):
    if log:
        print(content)
    return {"role": role, "content": content}


def Text(text):
    return {"type": "text", "text": text}


def Image(data):
    base64_data = base64.b64encode(data).decode("utf-8")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{base64_data}"},
    }
