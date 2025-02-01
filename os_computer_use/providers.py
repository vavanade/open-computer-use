import os
from dotenv import load_dotenv
from os_computer_use.llm_provider import OpenAIBaseProvider, AnthropicBaseProvider
from os_computer_use.osatlas_provider import OSAtlasProvider
from os_computer_use.showui_provider import ShowUIProvider
from openai import OpenAI
import base64
import json

# Load environment variables from .env file
load_dotenv()

# LLM providers use the OpenAI specification and require a base URL:


class LlamaProvider(OpenAIBaseProvider):
    base_url = "https://api.llama-api.com"
    api_key = os.getenv("LLAMA_API_KEY")
    aliases = {"llama3.2": "llama3.2-90b-vision", "llama3.3": "llama3.3-70b"}


class OpenRouterProvider(OpenAIBaseProvider):
    base_url = "https://openrouter.ai/api/v1"
    api_key = os.getenv("OPENROUTER_API_KEY")
    aliases = {"llama3.2": "meta-llama/llama-3.2-90b-vision-instruct"}


class FireworksProvider(OpenAIBaseProvider):
    base_url = "https://api.fireworks.ai/inference/v1"
    api_key = os.getenv("FIREWORKS_API_KEY")
    aliases = {
        "llama3.2": "accounts/fireworks/models/llama-v3p2-90b-vision-instruct",
        "llama3.3": "accounts/fireworks/models/llama-v3p3-70b-instruct",
    }


class DeepSeekProvider(OpenAIBaseProvider):
    base_url = "https://api.deepseek.com"
    api_key = os.getenv("DEEPSEEK_API_KEY")


class OpenAIProvider(OpenAIBaseProvider):
    base_url = "https://api.openai.com/v1"
    api_key = os.getenv("OPENAI_API_KEY")


class GeminiProvider(OpenAIBaseProvider):
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
    api_key = os.getenv("GEMINI_API_KEY")


class AnthropicProvider(AnthropicBaseProvider):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    aliases = {
        "claude-3.5-sonnet": "claude-3-5-sonnet-20241022",
        "claude-3.5-haiku": "claude-3-5-haiku-20241022",
        "claude-3-opus": "claude-3-opus-20240229",
    }


class GroqProvider(OpenAIBaseProvider):
    base_url = "https://api.groq.com/openai/v1"
    api_key = os.getenv("GROQ_API_KEY")
    aliases = {
        "llama3.2": "llama-3.2-90b-vision-preview",
        "llama3.3": "llama-3.3-70b-versatile",
    }


class MistralProvider(OpenAIBaseProvider):
    base_url = "https://api.mistral.ai/v1"
    api_key = os.getenv("MISTRAL_API_KEY")
    aliases = {
        "small": "mistral-small-latest",
        "medium": "mistral-medium-latest",
        "large": "mistral-large-latest",
        "pixtral": "pixtral-large-latest"
    }

    def create_client(self):
        return OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        ).chat.completions

    def completion(self, messages, **kwargs):
        try:
            # Process message content
            formatted_messages = []
            for msg in messages:
                content = msg["content"]
                processed_content = []

                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, bytes):
                            # Handle image data
                            base64_image = base64.b64encode(item).decode('utf-8')
                            processed_content.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            })
                        else:
                            # Handle text blocks
                            processed_content.append({
                                "type": "text",
                                "text": str(item)
                            })
                else:
                    # Handle simple text content
                    processed_content.append({
                        "type": "text",
                        "text": str(content)
                    })

                formatted_messages.append({
                    "role": msg["role"],
                    "content": processed_content
                })

            # Prepare tools if provided
            if "tools" in kwargs and kwargs["tools"] is not None:
                kwargs["tools"] = [{
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": details["description"],
                        "parameters": {
                            "type": "object",
                            "properties": details["params"],
                            "required": list(details["params"].keys())
                        }
                    }
                } for name, details in kwargs["tools"].items()]

            # Filter out None values
            filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}
            
            return self.client.create(
                model=self.model,
                messages=formatted_messages,
                **filtered_kwargs
            )
            
        except Exception as e:
            print(f"Mistral API Error: {str(e)}")
            raise

    def call(self, messages, functions=None):
        try:
            completion = self.completion(messages, tools=functions)
            message = completion.choices[0].message
            content = message.content
            
            # Extract tool calls
            tool_calls = []
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_calls.append({
                        "type": "function",
                        "name": tool_call.function.name,
                        "parameters": json.loads(tool_call.function.arguments)
                    })
            
            return content, tool_calls
            
        except json.JSONDecodeError:
            print("Failed to parse tool call arguments")
            return content, []