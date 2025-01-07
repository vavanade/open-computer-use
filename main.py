from os_computer_use.streaming import Sandbox, DisplayClient
from os_computer_use.sandbox_agent import SandboxAgent
import asyncio
import argparse

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure E2B
os.environ["E2B_API_KEY"] = os.getenv("E2B_API_KEY")


async def start(user_input=None):
    sandbox = None
    client = None
    try:
        sandbox = Sandbox()
        client = DisplayClient()

        print("Starting the display server...")
        stream_url = sandbox.start_stream()
        await asyncio.sleep(2.5)

        print("Starting the display client...")
        await client.start_display_client(stream_url)

        agent = SandboxAgent(sandbox)

        while True:
            try:
                if user_input is None:
                    user_input = input("USER: ")
                agent.run(user_input)
                user_input = None

            except KeyboardInterrupt:
                print("\nExit key pressed.")
                break

    finally:
        if client:
            print("Stopping the display client...")
            try:
                await client.stop_display_client()
            except Exception as e:
                print(f"Error stopping display client: {str(e)}")

        if sandbox:
            print("Stopping the sandbox...")
            try:
                sandbox.kill()
            except Exception as e:
                print(f"Error stopping sandbox: {str(e)}")

        if client:
            print("Saving the stream as mp4...")
            try:
                await client.save_stream()
            except Exception as e:
                print(f"Error saving stream: {str(e)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", type=str, help="User prompt for the agent")
    args = parser.parse_args()

    asyncio.run(start(user_input=args.prompt))
