from qwen_agent.llm import get_chat_model
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
osatlas_config = {
    "source": "maxiw/OS-ATLAS",
    "model": "OS-Copilot/OS-Atlas-Base-7B",
    "api_name": "/run_example",
}

# Configure E2B
os.environ["E2B_API_KEY"] = os.getenv("E2B_API_KEY")
