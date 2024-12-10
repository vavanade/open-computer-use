from os_computer_use.streaming import Sandbox, DisplayClient
from os_computer_use.sandbox_agent import SandboxAgent
from os_computer_use.llm import llama
import asyncio


async def start():
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

        agent = SandboxAgent(llama, sandbox)
        while True:
            try:
                user_input = input("USER: ")
                agent.run(user_input)

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
    asyncio.run(start())
