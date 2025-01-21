import os
from dotenv import load_dotenv
from os_computer_use.llm_provider import LLMProvider
from os_computer_use.osatlas_provider import OSAtlasProvider
from os_computer_use.showui_provider import ShowUIProvider

# Load environment variables from .env file
load_dotenv()

# LLM providers use the OpenAI specification and require a base URL:


class LlamaProvider(LLMProvider):
    base_url = "https://api.llama-api.com"
    api_key = os.getenv("LLAMA_API_KEY")
    aliases = {"llama3.2": "llama3.2-90b-vision", "llama3.3": "llama3.3-70b"}


class OpenRouterProvider(LLMProvider):
    base_url = "https://openrouter.ai/api/v1"
    api_key = os.getenv("OPENROUTER_API_KEY")
    aliases = {"llama3.2": "meta-llama/llama-3.2-90b-vision-instruct"}


class FireworksProvider(LLMProvider):
    base_url = "https://api.fireworks.ai/inference/v1"
    api_key = os.getenv("FIREWORKS_API_KEY")
    aliases = {
        "llama3.2": "accounts/fireworks/models/llama-v3p2-90b-vision-instruct",
        "llama3.3": "accounts/fireworks/models/llama-v3p3-70b-instruct",
    }


class DeepSeekProvider(LLMProvider):
    base_url = "https://api.deepseek.com"
    api_key = os.getenv("DEEPSEEK_API_KEY")


class GeminiProvider(LLMProvider):
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
    api_key = os.getenv("GEMINI_API_KEY")


# Define the models to use in the agent

# grounding_model = ShowUIProvider()
grounding_model = OSAtlasProvider()

vision_model = FireworksProvider("llama3.2")

action_model = FireworksProvider("llama3.3")
