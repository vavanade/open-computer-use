# Open Source Computer Use by E2B

A secure cloud Linux computer powered by [E2B Desktop Sandbox](https://github.com/e2b-dev/desktop/) and controlled by open-source LLMs.

https://github.com/user-attachments/assets/3837c4f6-45cb-43f2-9d51-a45f742424d4

## Get started

### Prerequisites

- Python 3.10 or later
- [git](https://git-scm.com/)
- [E2B API key](https://e2b.dev/dashboard?tab=keys)
- [OpenRouter API key](https://openrouter.ai/settings/keys)

### 1. Install the prerequisites

In your terminal:

```sh
brew install poetry ffmpeg
```

### 2. Clone the repository

In your terminal:

```sh
git clone https://github.com/e2b-dev/secure-computer-use/
```

### 3. Set the environment variables

Enter the project directory:

```
cd secure-computer-use
```

Create a `.env` file in `secure-computer-use` and set the following:

```sh
# Get your API key here - https://e2b.dev/
E2B_API_KEY="your-e2b-api-key"
OPENROUTER_API_KEY="your-openrouter-api-key"
```

### 4. Start the web interface

Run the following command to start the agent:

```sh
poetry run start
```

The agent will start and prompt you for its first instruction.
