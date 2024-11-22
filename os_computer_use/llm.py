from qwen_agent.llm import get_chat_model
import fireworks.client
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Use OpenRouter to run Qwen-2-VL-72B-Instruct
qwenvl_config = {
    "model_type": "qwenvl_oai",
    "model": "qwen/qwen-2-vl-72b-instruct",
    "model_server": "https://openrouter.ai/api/v1",
    "api_key": os.getenv("OPENROUTER_API_KEY"),
}
qwen = get_chat_model(qwenvl_config)

# Use Fireworks to run OS-Atlas-Base-7B
fireworks.client.api_key = os.getenv("FIREWORKS_API_KEY")
osatlas_config = {
    "model": "accounts/jamesmurdza-2250f2/models/os-atlas-base-7b",
}

# Configure E2B
os.environ["E2B_API_KEY"] = os.getenv("E2B_API_KEY")
