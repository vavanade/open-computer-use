from os_computer_use.streaming import Sandbox, DisplayClient
from os_computer_use.sandbox_agent import SandboxAgent
from os_computer_use.llm import qwen
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

        agent = SandboxAgent(qwen, sandbox)
        agent.run(
            "Do the following: 1) Open Firefox 2) Use run_command to sleep for two seconds "
            "3) Click on the URL bar 4) Type a URL."
        )

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise
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
