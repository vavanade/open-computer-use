import os
from dotenv import load_dotenv
from os_computer_use.llm_provider import LLMProvider
from os_computer_use.osatlas_provider import OSAtlasProvider

# Load environment variables from .env file
load_dotenv()

# Model names can vary from provider to provider, and are standardized here:
model_names = {
    "llama": {"llama3.2": "llama3.2-90b-vision", "llama3.3": "llama3.3-70b"},
    "openrouter": {"llama3.2": "meta-llama/llama-3.2-90b-vision-instruct"},
    "fireworks": {"llama3.3": "accounts/fireworks/models/llama-v3p3-70b-instruct"},
}


# LLM providers use the OpenAI specification and require a base URL:


class LlamaProvider(LLMProvider):
    base_url = "https://api.llama-api.com"
    api_key = os.getenv("LLAMA_API_KEY")


class OpenRouterProvider(LLMProvider):
    base_url = "https://openrouter.ai/api/v1"
    api_key = os.getenv("OPENROUTER_API_KEY")


class FireworksProvider(LLMProvider):
    base_url = "https://api.fireworks.ai/inference/v1"
    api_key = os.getenv("FIREWORKS_API_KEY")


# The OS-Atlas provider is separately implemented.
grounding_model = OSAtlasProvider()


# Choose the models to use based on the defined environment variables.

if os.getenv("LLAMA_API_KEY"):
    print("Using Llama API for Llama 3.2")
    vision_model = LlamaProvider(model_names["llama"]["llama3.2"])

    print("Using Llama API for Llama 3.3")
    action_model = LlamaProvider(model_names["llama"]["llama3.3"])

else:
    print("Using OpenRouter for Llama 3.2")
    vision_model = OpenRouterProvider(model_names["openrouter"]["llama3.2"])

    print("Using Fireworks for Llama 3.3")
    action_model = FireworksProvider(model_names["fireworks"]["llama3.3"])
