from os_computer_use.sandbox import Sandbox
from os_computer_use.sandbox_agent import SandboxAgent
from os_computer_use.llm import qwen


def main():
    sandbox = Sandbox()
    agent = SandboxAgent(qwen, sandbox)

    agent.run(
        "Do the following: 1) Open Firefox 2) Use run_command to sleep for two seconds 3) Click on the URL bar 4) Type a URL."
    )

    sandbox.kill()
