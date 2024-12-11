from os_computer_use.utils import (
    send_bbox_request,
    draw_big_dot,
)
from os_computer_use.agent import ComputerUseAgent, format_message
from os_computer_use.llm import openrouter_config, llama_config, llama_vision

from gradio_client import handle_file
import fireworks.client

import base64
import shlex
import os
import tempfile
from PIL import Image

TYPING_DELAY_MS = 12
TYPING_GROUP_SIZE = 50


# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


class SandboxAgent(ComputerUseAgent):
    functions = [
        {
            "type": "function",
            "function": {
                "name": "send_key",
                "description": "Send a key or combination of keys to the system.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Key or combination (e.g. 'Return', 'Ctl-C')",
                        },
                    },
                    "required": ["name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "type_text",
                "description": "Type a specified text into the system.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to type",
                        },
                    },
                    "required": ["text"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_command",
                "description": "Run a shell command and return the result.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Shell command to run",
                        },
                    },
                    "required": ["command"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_background_command",
                "description": "Run a shell command in the background.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Shell command to run without waiting",
                        },
                    },
                    "required": ["command"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "click",
                "description": "Click on a specified UI element.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Item or UI element on the screen to click",
                        },
                    },
                    "required": ["query"],
                },
            },
        },
    ]

    def __init__(self, sandbox):
        super().__init__()
        self.sandbox = sandbox
        self.latest_screenshot = None
        self.function_map = {
            "send_key": self.send_key,
            "type_text": self.type_text,
            "run_command": self.run_command,
            "run_background_command": self.run_background_command,
            "click": self.click,
        }
        # Create temporary directory
        self.tmp_dir = tempfile.mkdtemp()
        self.image_counter = 0

    def save_image(self, image, prefix="image"):
        """Save image to temporary directory with incrementing counter."""
        self.image_counter += 1
        filename = f"{prefix}_{self.image_counter}.png"
        filepath = os.path.join(self.tmp_dir, filename)
        if isinstance(image, Image.Image):
            image.save(filepath)
        else:
            with open(filepath, "wb") as f:
                f.write(image)
        return filepath

    def take_screenshot(self):
        file = self.sandbox.take_screenshot()
        filename = self.save_image(file, "screenshot")
        print(f"Image: {filename}")
        self.latest_screenshot = filename
        return encode_image(filename)

    def run_command(self, command):
        result = self.sandbox.commands.run(command, timeout=5)
        stdout, stderr = result.stdout, result.stderr
        if stdout and stderr:
            return stdout + "\n" + stderr
        elif stdout or stderr:
            return stdout + stderr
        else:
            return "Done."

    def run_background_command(self, command):
        self.sandbox.commands.run(command, background=True)
        return "Done."

    def send_key(self, name):
        self.sandbox.commands.run(f"xdotool key -- {name}")
        return "Done."

    def type_text(self, text):
        def chunks(text, n):
            for i in range(0, len(text), n):
                yield text[i : i + n]

        results = []
        for chunk in chunks(text, TYPING_GROUP_SIZE):
            cmd = f"xdotool type --delay {TYPING_DELAY_MS} -- {shlex.quote(chunk)}"
            results.append(self.sandbox.commands.run(cmd))
        return "Done."

    def click(self, query):
        self.take_screenshot()
        original_image = Image.open(self.latest_screenshot)
        image_data = handle_file(self.latest_screenshot)
        x, y = send_bbox_request(image_data, query)

        # Save the image with dot instead of displaying
        dot_image = draw_big_dot(original_image, (x, y))
        filepath = self.save_image(dot_image, "location")
        print(f"Image: {filepath}")

        self.sandbox.commands.run(f"xdotool mousemove --sync {x} {y}")
        self.sandbox.commands.run("xdotool click 1")
        return "Done."

    def append_screenshot(self, instruction):
        # self.messages.append({"role": "user", "content": self.take_screenshot()})
        base64_data = self.take_screenshot()
        messages = [
            # *self.messages,
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Explain the next best action to take in order to complete the object: {instruction}\nOr, if the objective is accomplished, take no action.\nYou can click, type, use keyboard commands and run shell commands. Be concise.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_data}"},
                    },
                ],
            },
        ]
        completion = llama_vision.chat.completions.create(
            model=openrouter_config["vision_model"], messages=messages
        )
        return completion.choices[0].message.content

    def run(self, instruction):

        self.messages.append({"role": "user", "content": instruction})

        should_continue = True

        while should_continue:
            screen_contents = self.append_screenshot(instruction)
            print(f"ASSISTANT: {screen_contents}")

            messages = [
                {
                    "role": "system",
                    "content": "You are an AI assistant with the ability to click, type and run commands on a computer.",
                },
                *self.messages,
                {
                    "role": "assistant",
                    "content": screen_contents,
                },
                {
                    "role": "assistant",
                    "content": "If the objective is not accomplished, I will now perform the next step, otherwise I will do nothing.",
                },
            ]
            completion = fireworks.client.ChatCompletion.create(
                model=llama_config["model"], messages=messages, tools=self.functions
            )
            content = completion.choices[0].message.content
            if content:
                print(f"ASSISTANT: {content}")
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": content,
                    }
                )

            tool_calls = completion.choices[0].message.tool_calls or []
            should_continue = False
            for tool_call in tool_calls:
                should_continue = True
                self.messages.append(
                    {
                        "role": "function",
                        "name": tool_call.function.name,
                        "content": tool_call.function.arguments,
                    }
                )
                print(tool_call.function)
                func_rsp = self.call_function(tool_call.function)
                self.messages.append(func_rsp)
                print(func_rsp)
