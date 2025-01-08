from openai import OpenAI
import os
from dotenv import load_dotenv
from gradio_client import Client, handle_file
from os_computer_use.llama_utils import (
    parse_llama_tool_calls,
    create_llama_function_list,
)
import base64

# Load environment variables from .env file
load_dotenv()

# Initialize the OS-Atlas provider

OSATLAS_HUGGINGFACE_SOURCE = "maxiw/OS-ATLAS"
OSATLAS_HUGGINGFACE_MODEL = "OS-Copilot/OS-Atlas-Base-7B"
OSATLAS_HUGGINGFACE_API = "/run_example"

osatlas = Client(OSATLAS_HUGGINGFACE_SOURCE)


def call_grounding_model(prompt, image_data):
    result = osatlas.predict(
        image=handle_file(image_data),
        text_input=prompt,
        model_id=OSATLAS_HUGGINGFACE_MODEL,
        api_name=OSATLAS_HUGGINGFACE_API,
    )
    return result[1], result[2]


# Initialize the Llama provider(s)

LLAMA_BASE_URL = "https://api.llama-api.com"
LLAMA_32_MODEL = "llama3.2-90b-vision"
LLAMA_33_MODEL = "llama3.3-70b"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
LLAMA_32_OPENROUTER_MODEL = "meta-llama/llama-3.2-90b-vision-instruct"
LLAMA_33_FIREWORKS_MODEL = "accounts/fireworks/models/llama-v3p3-70b-instruct"

llama_api_client = None
if os.getenv("LLAMA_API_KEY"):
    llama_api_client = OpenAI(
        base_url=LLAMA_BASE_URL,
        api_key=os.getenv("LLAMA_API_KEY"),
    )

# Establish the Llama 3.2 provider

if llama_api_client:
    print("Using Llama API for Llama 3.2")

    def llama32_complete(messages):
        return llama_api_client.chat.completions.create(
            messages=messages,
            model=LLAMA_32_MODEL,
        )

else:
    print("Using OpenRouter for Llama 3.2")

    openrouter_client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    def llama32_complete(messages):
        return openrouter_client.chat.completions.create(
            messages=messages,
            model=LLAMA_32_OPENROUTER_MODEL,
        )


# Use Llama 3.2 as the vision model
def call_vision_model(messages):
    completion = llama32_complete(messages)
    if hasattr(completion, "error"):
        raise Exception(
            "Error calling Llama 3.2 vision model: {}".format(completion.error)
        )
    if not completion.choices:
        raise ValueError(
            "Invalid response from Llama 3.2 vision model: {}".format(completion)
        )
    return completion.choices[0].message.content


# Establish the Llama 3.3 provider

if llama_api_client:
    print("Using Llama API for Llama 3.3")

    def llama33_complete(messages, tools):
        return llama_api_client.chat.completions.create(
            messages=messages,
            model=LLAMA_33_MODEL,
            tools=tools,
        )

else:
    print("Using Fireworks for Llama 3.3")
    import fireworks.client

    fireworks.client.api_key = os.getenv("FIREWORKS_API_KEY")

    def llama33_complete(messages, tools):
        return fireworks.client.ChatCompletion.create(
            messages=messages,
            model=LLAMA_33_FIREWORKS_MODEL,
            tools=tools,
        )


# Use Llama 3.3 as the action model
def call_action_model(messages, functions):
    completion = llama33_complete(messages, tools=create_llama_function_list(functions))
    if hasattr(completion, "error"):
        raise Exception(
            "Error calling Llama 3.3 action model: {}".format(completion.error)
        )
    if not completion.choices:
        raise ValueError(
            "Invalid response from Llama 3.3 action model: {}".format(completion)
        )
    return parse_llama_tool_calls(
        completion.choices[0].message.content,
        completion.choices[0].message.tool_calls or [],
    )


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
