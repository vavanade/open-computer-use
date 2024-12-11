from openai import OpenAI
import os
from dotenv import load_dotenv
import fireworks.client

# Load environment variables from .env file
load_dotenv()

# Use Fireworks to run Llama 3.3
fireworks.client.api_key = os.getenv("FIREWORKS_API_KEY")
llama_config = {
    "model": "accounts/fireworks/models/llama-v3p3-70b-instruct",
}

# Use OpenRouter to run Qwen-2-VL-72B-Instruct
openrouter_config = {
    "vision_model": "meta-llama/llama-3.2-90b-vision-instruct",
}
llama_vision = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Use Fireworks to run OS-Atlas-Base-7B
osatlas_config = {
    "source": "maxiw/OS-ATLAS",
    "model": "OS-Copilot/OS-Atlas-Base-7B",
    "api_name": "/run_example",
}

# Configure E2B
os.environ["E2B_API_KEY"] = os.getenv("E2B_API_KEY")
